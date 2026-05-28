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
def init_callrequest(self, callrequest_id: int) -> None:
    """
    Initialize a call via FreeSWITCH ESL.
    
    This task:
    1. Fetches the Callrequest
    2. Builds the FreeSWITCH originate command
    3. Sends it via ESL
    4. Updates Callrequest status
    
    Args:
        callrequest_id: Primary key of Callrequest to dial
    """
    try:
        cr = Callrequest.objects.select_related(
            'campaign', 'aleg_gateway', 'user'
        ).get(id=callrequest_id)
    except Callrequest.DoesNotExist:
        logger.error(f"Callrequest {callrequest_id} not found")
        return
    
    logger.info(f"Initiating call: {cr.phone_number} (CR#{callrequest_id})")
    
    # Update status to CALLING
    cr.status = CallrequestStatus.CALLING
    cr.num_attempt += 1
    cr.last_attempt_time = timezone.now()
    cr.save(update_fields=['status', 'num_attempt', 'last_attempt_time'])
    
    # Build originate command
    gateway = cr.aleg_gateway
    if not gateway:
        logger.error(f"No gateway for callrequest {callrequest_id}")
        cr.status = CallrequestStatus.FAILURE
        cr.result = 'No gateway configured'
        cr.save(update_fields=['status', 'result'])
        return
    
    # Build dial string
    dial_string = _build_dial_string(cr, gateway)
    
    # Build full originate command
    command = _build_originate_command(cr, dial_string)
    
    logger.debug(f"Originate command: {command}")
    
    # Send to FreeSWITCH
    result = dial_out(command, callrequest_id)
    
    if result == 'error':
        # ESL failed
        cr.status = CallrequestStatus.FAILURE
        cr.result = 'ESL originate failed'
        cr.save(update_fields=['status', 'result'])
        logger.error(f"ESL originate failed for CR#{callrequest_id}")
    else:
        # Success - Job-UUID received
        logger.info(f"Originated call CR#{callrequest_id}, Job-UUID: {result}")
        # Status will be updated by FreeSWITCH hangup webhook


def _build_dial_string(cr: Callrequest, gateway) -> str:
    """
    Build the dial string with all channel variables.
    
    Format:
    {var1=val1,var2=val2}gateway/number
    """
    vars_dict = {
        'ignore_early_media': 'true',
        'originate_timeout': cr.timeout,
        'origination_caller_id_number': cr.callerid or '',
        'request_uuid': str(cr.request_uuid),
        'callrequest_id': cr.id,
    }
    
    # Add campaign info if present
    if cr.campaign:
        vars_dict.update({
            'campaign_id': cr.campaign.id,
            'campaign_name': cr.campaign.name,
            'tenant_id': cr.user.tenant_id if cr.user.tenant else 0,
        })
    
    # Add extra dial string if present
    if cr.extra_dial_string:
        # Parse extra dial string and add to vars
        pass  # TODO: parse extra_dial_string
    
    # Build channel vars string
    vars_str = ','.join(f"{k}={v}" for k, v in vars_dict.items())
    
    # Apply prefix routing
    phone_number = cr.phone_number
    if gateway.removeprefix and phone_number.startswith(gateway.removeprefix):
        phone_number = phone_number[len(gateway.removeprefix):]
    if gateway.addprefix:
        phone_number = gateway.addprefix + phone_number
    
    # Build full dial string
    dial_string = f"{{{vars_str}}}{gateway.gateways}/{phone_number}"
    
    return dial_string


def _build_originate_command(cr: Callrequest, dial_string: str) -> str:
    """
    Build the full bgapi originate command.
    
    Format:
    bgapi originate <dial_string> &lua(<script>)
    """
    lua_script = settings.FS_LUA_SCRIPT
    
    # For now, simple originate to Lua script
    # In Phase 3, this will route to survey/audiofile based on content_type
    command = f"bgapi originate {dial_string} &lua({lua_script})"
    
    return command
