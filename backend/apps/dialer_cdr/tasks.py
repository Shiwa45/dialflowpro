"""
Celery tasks for call initiation and processing.
"""
from __future__ import annotations
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from .models import Callrequest
from .constants import CallrequestStatus
from .esl import dial_out

logger = get_task_logger(__name__)


@shared_task(name='dialer_cdr.init_callrequest', bind=True, max_retries=3)
def init_callrequest(self, callrequest_id: int, tenant_schema: str = '') -> None:
    """
    Initialize a call via FreeSWITCH ESL inside the correct tenant schema.
    """
    from django_tenants.utils import schema_context

    def _run():
        try:
            cr = Callrequest.objects.select_related(
                'campaign', 'aleg_gateway', 'user'
            ).get(id=callrequest_id)
        except Callrequest.DoesNotExist:
            logger.error(f"Callrequest {callrequest_id} not found (schema={tenant_schema})")
            return

        # Only dial requests that are still pending. Guards against stray/
        # stale queued tasks re-dialing a callrequest that was already
        # failed, completed, aborted, or is already in progress.
        if cr.status not in (CallrequestStatus.PENDING, CallrequestStatus.RETRY):
            logger.info(f"CR#{callrequest_id} status={cr.status} not dialable — skipping")
            return

        logger.info(f"Initiating call: {cr.phone_number} (CR#{callrequest_id})")

        cr.status = CallrequestStatus.CALLING
        cr.num_attempt += 1
        cr.last_attempt_time = timezone.now()
        cr.save(update_fields=['status', 'num_attempt', 'last_attempt_time'])

        gateway = cr.aleg_gateway
        if not gateway:
            logger.error(f"No gateway for CR#{callrequest_id}")
            cr.status = CallrequestStatus.FAILURE
            cr.result = 'No gateway configured'
            cr.save(update_fields=['status', 'result'])
            return

        dial_string = _build_dial_string(cr, gateway, tenant_schema)
        command = _build_originate_command(cr, dial_string)
        logger.info(f"Originate: {command}")

        result = dial_out(command, callrequest_id)

        if result == 'error':
            cr.status = CallrequestStatus.FAILURE
            cr.result = 'ESL originate failed'
            cr.save(update_fields=['status', 'result'])
            logger.error(f"ESL originate failed for CR#{callrequest_id}")

            # Reset subscriber so it is retried on the next campaign cycle
            if cr.subscriber_id:
                from apps.dialer_campaign.models import Subscriber
                from apps.dialer_campaign.constants import SubscriberStatus
                Subscriber.objects.filter(
                    id=cr.subscriber_id,
                    status=SubscriberStatus.IN_PROCESS,
                ).update(status=SubscriberStatus.PENDING)
        else:
            logger.info(f"CR#{callrequest_id} originated — Job-UUID: {result}")

    if tenant_schema:
        with schema_context(tenant_schema):
            _run()
    else:
        _run()


def _build_dial_string(cr: Callrequest, gateway, tenant_schema: str = '') -> str:
    vars_dict = {
        'ignore_early_media': 'true',
        'originate_timeout': cr.timeout,
        'origination_caller_id_number': cr.callerid or '',
        'request_uuid': str(cr.request_uuid),
        'callrequest_id': cr.id,
    }

    if cr.campaign:
        vars_dict.update({
            'campaign_id':   cr.campaign.id,
            'campaign_name': cr.campaign.name,
            'tenant_id':     cr.user.tenant_id if cr.user and cr.user.tenant_id else 0,
            'tenant_schema': tenant_schema,
            'dial_mode':     cr.campaign.dial_mode,
            'queue_id':      cr.campaign.queue_id or '',
        })

    vars_str = ','.join(f"{k}={v}" for k, v in vars_dict.items())

    phone_number = cr.phone_number

    # Strip leading + if no addprefix is configured — GSM/FXO gateways
    # (OpenVox, Goip, etc.) typically reject E.164 format and return
    # UNALLOCATED_NUMBER (cause 1).
    if not gateway.addprefix and phone_number.startswith('+'):
        phone_number = phone_number[1:]

    if gateway.removeprefix and phone_number.startswith(gateway.removeprefix):
        phone_number = phone_number[len(gateway.removeprefix):]
    if gateway.addprefix:
        phone_number = gateway.addprefix + phone_number

    # Strip trailing slash from gateways field to avoid double-slash in URL
    gateways = gateway.gateways.rstrip('/')

    return f"{{{vars_str}}}{gateways}/{phone_number}"


def _build_originate_command(cr: Callrequest, dial_string: str) -> str:
    lua_script = settings.FS_LUA_SCRIPT
    return f"bgapi originate {dial_string} &lua({lua_script})"
