"""
Celery tasks for campaign management.
Core dialer engine tasks that spool calls and manage subscribers.
"""
from __future__ import annotations
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone
from django.db import transaction
from datetime import timedelta
import uuid

from datetime import timedelta

from .models import Campaign, Subscriber
from .constants import CampaignStatus, SubscriberStatus, DialMode
from apps.dialer_cdr.models import Callrequest
from apps.dialer_cdr.constants import CallrequestStatus, CallrequestType
from apps.dialer_cdr.tasks import init_callrequest

logger = get_task_logger(__name__)


def _get_tenant_schemas():
    """Return all active non-public tenant schema names."""
    from apps.tenants.models import Tenant
    return list(
        Tenant.objects.filter(is_active=True)
              .exclude(schema_name='public')
              .values_list('schema_name', flat=True)
    )


# ── Periodic heartbeat ────────────────────────────────────────────────────────

@shared_task(name='dialer_campaign.campaign_running', ignore_result=True)
def campaign_running() -> None:
    """
    Periodic heartbeat — checks every tenant for running campaigns and spools calls.
    Fires every 60 / HEARTBEAT_MIN seconds via Celery beat.
    """
    logger.info("TASK :: campaign_running")
    from django_tenants.utils import schema_context

    for schema in _get_tenant_schemas():
        with schema_context(schema):
            running = Campaign.objects.get_running_campaigns()
            count = running.count()
            if count:
                logger.info(f"[{schema}] {count} running campaign(s)")
            for campaign in running:
                logger.info(f"[{schema}] Spooling '{campaign.name}' (id={campaign.id})")
                campaign_spool_contact.delay(campaign.id, schema)


# ── Per-campaign spool ────────────────────────────────────────────────────────

@shared_task(name='dialer_campaign.campaign_spool_contact', ignore_result=True)
def campaign_spool_contact(campaign_id: int, tenant_schema: str = '') -> bool:
    """
    Spool one campaign cycle — fetch pending subscribers, create Callrequests,
    schedule init_callrequest tasks with ETA spread across the minute.
    Always runs inside the correct tenant schema.
    """
    logger.info(
        f"TASK :: campaign_spool_contact id={campaign_id} schema={tenant_schema or 'current'}"
    )
    from django_tenants.utils import schema_context

    def _run():
        # ── Fetch campaign ────────────────────────────────────────────────
        try:
            campaign = Campaign.objects.select_related(
                'user__profile__dialersetting', 'aleg_gateway'
            ).get(id=campaign_id)
        except Campaign.DoesNotExist:
            logger.error(f"Campaign {campaign_id} not found (schema={tenant_schema})")
            return False

        if not campaign.is_running():
            logger.info(f"Campaign {campaign_id} not running — skipping")
            return False

        # ── Auto-recover stale IN_PROCESS subscribers ─────────────────────
        # Calls stuck >5 min never reported completion (no answer / lost
        # webhook). Retry if under maxretry, otherwise mark FAIL so they
        # don't redial forever.
        stale_cutoff = timezone.now() - timedelta(minutes=5)
        stale_subs = list(Subscriber.objects.filter(
            campaign=campaign,
            status=SubscriberStatus.IN_PROCESS,
            updated_date__lt=stale_cutoff,
        ))
        for sub in stale_subs:
            sub.count_attempt = (sub.count_attempt or 0) + 1
            if sub.count_attempt <= campaign.maxretry:
                sub.status = SubscriberStatus.PENDING
            else:
                sub.status = SubscriberStatus.FAIL
            sub.save(update_fields=['status', 'count_attempt'])
        if stale_subs:
            logger.info(f"Recovered {len(stale_subs)} stale IN_PROCESS subscriber(s)")

        # ── Auto-collect newly added contacts ─────────────────────────────
        # When the campaign has no pending subscribers, re-scan the linked
        # phonebooks so contacts added AFTER the campaign started get turned
        # into subscribers and dialed (collect dedupes by number, so this is
        # idempotent and cheap).
        if not Subscriber.objects.filter(
            campaign=campaign, status=SubscriberStatus.PENDING
        ).exists():
            try:
                collect_subscriber(campaign_id, tenant_schema)
            except Exception as exc:
                logger.warning(f"auto-collect failed for campaign {campaign_id}: {exc}")

        # ── Frequency (upper cap) ─────────────────────────────────────────
        frequency = campaign.frequency
        if getattr(settings, 'HEARTBEAT_MIN', 1) > 1:
            frequency = int(frequency / settings.HEARTBEAT_MIN) + 1
        logger.info(f"'{campaign.name}' frequency cap={frequency}")

        # ── Call pacing ───────────────────────────────────────────────────
        claim_limit = frequency

        if campaign.ai_agent_id:
            # AI campaign: no human presence to pace against. Cap the number of
            # simultaneous calls at ai_max_concurrent (each uses one AI session).
            active_window = timezone.now() - timedelta(seconds=(campaign.callmaxduration or 600))
            active = Callrequest.objects.filter(
                campaign=campaign,
                status=CallrequestStatus.CALLING,
                last_attempt_time__gte=active_window,
            ).count()
            cap = max(campaign.ai_max_concurrent, 1)
            claim_limit = max(0, min(cap - active, frequency))
            logger.info(
                f"'{campaign.name}' AI pacing: max_concurrent={cap} "
                f"active={active} → dialing {claim_limit}"
            )
            if claim_limit == 0:
                logger.info(f"'{campaign.name}': AI at max concurrency — skipping")
                return False

        # For human agent modes, dial only what available agents can handle.
        # Capacity = available_agents × lines_per_agent − calls_still_ringing.
        elif campaign.dial_mode in (DialMode.PREDICTIVE, DialMode.PROGRESSIVE) and campaign.queue_id:
            from apps.callcenter.services import count_available_agents, get_registered_extensions

            registered = get_registered_extensions()
            available = count_available_agents(campaign.queue, registered)
            if available == 0:
                logger.info(
                    f"'{campaign.name}': no available agents "
                    f"(must be WS-connected AND SIP-registered) — not dialing"
                )
                return False

            ring_window = timezone.now() - timedelta(seconds=(campaign.calltimeout or 30) + 5)
            ringing = Callrequest.objects.filter(
                campaign=campaign,
                status=CallrequestStatus.CALLING,
                last_attempt_time__gte=ring_window,
            ).count()

            capacity = available * max(campaign.lines_per_agent, 1)
            claim_limit = max(0, min(capacity - ringing, frequency))
            logger.info(
                f"'{campaign.name}' pacing: agents={available} "
                f"lines/agent={campaign.lines_per_agent} ringing={ringing} "
                f"capacity={capacity} → dialing {claim_limit}"
            )
            if claim_limit == 0:
                logger.info(f"'{campaign.name}': at capacity — skipping this cycle")
                return False

        # ── Lock & claim pending subscribers ─────────────────────────────
        with transaction.atomic():
            subscribers = list(
                Subscriber.objects.filter(
                    campaign=campaign,
                    status=SubscriberStatus.PENDING,
                ).select_for_update(skip_locked=True)[:claim_limit]
            )
            if not subscribers:
                logger.info(f"No pending subscribers for campaign {campaign_id}")
                return False
            logger.info(f"{len(subscribers)} subscribers claimed")
            for sub in subscribers:
                sub.status = SubscriberStatus.IN_PROCESS
            Subscriber.objects.bulk_update(subscribers, ['status'])

        # ── Call type ─────────────────────────────────────────────────────
        call_type = CallrequestType.ALLOW_RETRY
        if campaign.maxretry == 0:
            call_type = CallrequestType.CANNOT_RETRY
        try:
            ds = campaign.user.profile.dialersetting
            if ds and ds.maxretry == 0:
                call_type = CallrequestType.CANNOT_RETRY
        except Exception:
            pass

        # ── Build Callrequests ────────────────────────────────────────────
        now = timezone.now()
        spread = 60.0 / max(len(subscribers), 1)
        callrequests = []

        for i, sub in enumerate(subscribers):
            # duplicate_contact holds the normalized E.164 string;
            # fall back to the Contact.contact PhoneNumberField
            phone = sub.duplicate_contact or str(sub.contact or '')
            if not phone:
                logger.warning(f"Subscriber {sub.id} has no phone — marking NOT_AUTHORIZED")
                sub.status = SubscriberStatus.NOT_AUTHORIZED
                sub.save(update_fields=['status'])
                continue

            if not _is_authorized_contact(campaign, phone):
                logger.info(f"{phone} not authorized")
                sub.status = SubscriberStatus.NOT_AUTHORIZED
                sub.save(update_fields=['status'])
                continue

            if campaign.check_dnc and campaign.dnc_list:
                if _check_dnc(campaign.dnc_list, phone):
                    logger.info(f"{phone} in DNC — skipping")
                    sub.status = SubscriberStatus.NOT_AUTHORIZED
                    sub.save(update_fields=['status'])
                    continue

            callrequests.append(Callrequest(
                request_uuid=uuid.uuid4(),
                user=campaign.user,
                campaign=campaign,
                subscriber=sub,
                phone_number=phone,
                callerid=campaign.callerid,
                aleg_gateway=campaign.aleg_gateway,
                content_type=campaign.content_type,
                object_id=campaign.object_id,
                timeout=campaign.calltimeout,
                timelimit=campaign.callmaxduration,
                call_time=now + timedelta(seconds=i * spread),
                call_type=call_type,
                status=CallrequestStatus.PENDING,
            ))

        # ── Persist & schedule ────────────────────────────────────────────
        if callrequests:
            Callrequest.objects.bulk_create(callrequests)
            logger.info(f"Created {len(callrequests)} callrequests")
            for cr in callrequests:
                init_callrequest.apply_async(args=[cr.id, tenant_schema], eta=cr.call_time)

        return True

    if tenant_schema:
        with schema_context(tenant_schema):
            return _run()
    return _run()


# ── Import phonebook contacts into Subscribers ───────────────────────────────

@shared_task(name='dialer_campaign.collect_subscriber', ignore_result=True)
def collect_subscriber(campaign_id: int, tenant_schema: str = '') -> bool:
    """
    Import contacts from the campaign's phonebook(s) into Subscriber rows.
    Deduplicates, checks DNC and whitelist/blacklist.
    """
    logger.info(
        f"TASK :: collect_subscriber id={campaign_id} schema={tenant_schema or 'current'}"
    )
    from django_tenants.utils import schema_context

    def _run():
        try:
            campaign = Campaign.objects.prefetch_related('phonebook').get(id=campaign_id)
        except Campaign.DoesNotExist:
            logger.error(f"Campaign {campaign_id} not found")
            return False

        created = 0
        skipped = 0

        for phonebook in campaign.phonebook.all():
            contacts = phonebook.contacts.filter(status=1)
            logger.info(f"{contacts.count()} active contacts in '{phonebook.name}'")

            for contact in contacts:
                phone = str(contact.contact)

                # Skip numbers already imported for this campaign — unless the
                # campaign explicitly allows duplicate numbers. Dedup is keyed on
                # the contact row (not the number) when duplicates are allowed,
                # so re-running collect stays idempotent.
                if getattr(campaign, 'allow_duplicate_contacts', False):
                    if Subscriber.objects.filter(campaign=campaign, contact=contact).exists():
                        skipped += 1
                        continue
                elif Subscriber.objects.filter(campaign=campaign, duplicate_contact=phone).exists():
                    skipped += 1
                    continue

                if campaign.dnc and _check_dnc(campaign.dnc, phone):
                    skipped += 1
                    continue

                if not _is_authorized_contact(campaign, phone):
                    skipped += 1
                    continue

                Subscriber.objects.create(
                    campaign=campaign,
                    contact=contact,
                    duplicate_contact=phone,
                    status=SubscriberStatus.PENDING,
                )
                created += 1

        campaign.totalcontact = Subscriber.objects.filter(campaign=campaign).count()
        campaign.save(update_fields=['totalcontact'])
        logger.info(f"collect_subscriber done: created={created} skipped={skipped} for '{campaign.name}'")
        return True

    if tenant_schema:
        with schema_context(tenant_schema):
            return _run()
    return _run()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _is_authorized_contact(campaign: Campaign, phone_number: str) -> bool:
    import re
    try:
        ds = campaign.user.profile.dialersetting
        if not ds:
            return True
        wl = ds.whitelist if ds.whitelist != '*' else ''
        bl = ds.blacklist if ds.blacklist != '*' else ''
        if wl:
            return bool(re.search(wl, phone_number))
        if bl and re.search(bl, phone_number):
            return False
        return True
    except Exception:
        return True


def _check_dnc(dnc, phone_number: str) -> bool:
    if not dnc:
        return False
    try:
        from apps.dnc.models import DNCContact
        return DNCContact.objects.filter(dnc=dnc, phone_number=phone_number).exists()
    except Exception:
        return False
