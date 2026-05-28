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
from math import floor
import uuid
from .models import Campaign, Subscriber
from .constants import CampaignStatus, SubscriberStatus
from apps.dialer_cdr.models import Callrequest
from apps.dialer_cdr.constants import CallrequestStatus, CallrequestType
from apps.dialer_cdr.tasks import init_callrequest

logger = get_task_logger(__name__)


@shared_task(name='dialer_campaign.campaign_running', ignore_result=True)
def campaign_running() -> None:
    """
    Periodic task that checks for running campaigns and spools calls.
    
    This is the heartbeat of the dialer - runs every 60/HEARTBEAT_MIN seconds.
    For each running campaign, it triggers campaign_spool_contact.
    
    Replaces original campaign_running PeriodicTask.
    """
    logger.info("TASK :: campaign_running")
    
    # Get all campaigns that should be running right now
    running_campaigns = Campaign.objects.get_running_campaigns()
    
    logger.info(f"Found {running_campaigns.count()} running campaigns")
    
    for campaign in running_campaigns:
        logger.info(f"Spooling campaign: {campaign.name} (ID: {campaign.id})")
        campaign_spool_contact.delay(campaign.id)


@shared_task(name='dialer_campaign.campaign_spool_contact', ignore_result=True)
def campaign_spool_contact(campaign_id: int) -> bool:
    """
    Spool contacts for a single campaign.
    
    This task:
    1. Fetches pending subscribers (up to frequency limit)
    2. Creates Callrequest records for each
    3. Updates subscriber status to IN_PROCESS
    4. Schedules init_callrequest tasks with ETA spread across the minute
    
    Args:
        campaign_id: Campaign to process
        
    Returns:
        True if successful, False otherwise
    """
    logger.info(f"TASK :: campaign_spool_contact campaign_id={campaign_id}")
    
    try:
        campaign = Campaign.objects.select_related(
            'user__profile__dialersetting', 'aleg_gateway'
        ).get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return False
    
    # Check if campaign is still running
    if not campaign.is_running():
        logger.info(f"Campaign {campaign_id} is no longer running")
        return False
    
    # Calculate frequency for this cycle
    frequency = campaign.frequency
    if settings.HEARTBEAT_MIN > 1:
        # If running multiple times per minute, divide frequency
        frequency = int(frequency / settings.HEARTBEAT_MIN) + 1
    
    logger.info(f"Campaign {campaign.name}: frequency={frequency}")
    
    # Get pending subscribers with row-level locking
    with transaction.atomic():
        subscribers = list(
            Subscriber.objects.filter(
                campaign=campaign,
                status=SubscriberStatus.PENDING
            ).select_for_update(skip_locked=True)[:frequency]
        )
        
        if not subscribers:
            logger.info(f"No pending subscribers for campaign {campaign_id}")
            return False
        
        logger.info(f"Found {len(subscribers)} pending subscribers")
        
        # Update subscriber status to IN_PROCESS
        for sub in subscribers:
            sub.status = SubscriberStatus.IN_PROCESS
        Subscriber.objects.bulk_update(subscribers, ['status'])
    
    # Determine call_type based on maxretry
    call_type = CallrequestType.ALLOW_RETRY
    if campaign.maxretry == 0:
        call_type = CallrequestType.CANNOT_RETRY
    
    # Check user's dialer setting
    try:
        dialersetting = campaign.user.profile.dialersetting
        if dialersetting and dialersetting.maxretry == 0:
            call_type = CallrequestType.CANNOT_RETRY
    except Exception:
        pass
    
    # Calculate time distribution across the minute
    now = timezone.now()
    time_to_wait = 60.0 / len(subscribers)
    
    # Create callrequests in bulk
    callrequests = []
    for i, subscriber in enumerate(subscribers):
        phone_number = subscriber.duplicate_contact
        
        # Check if contact is authorized (whitelist/blacklist)
        if not _is_authorized_contact(campaign, phone_number):
            logger.info(f"Contact {phone_number} not authorized (whitelist/blacklist)")
            subscriber.status = SubscriberStatus.NOT_AUTHORIZED
            subscriber.save(update_fields=['status'])
            continue
        
        # Check DNC (Do-Not-Call) list
        if campaign.check_dnc and campaign.dnc_list:
            if _is_in_dnc(campaign.dnc_list, phone_number):
                logger.info(f"Contact {phone_number} is in DNC list")
                subscriber.status = SubscriberStatus.NOT_AUTHORIZED
                subscriber.save(update_fields=['status'])
                continue
        
        # Calculate ETA for this call (spread across minute)
        eta = now + timedelta(seconds=(i * time_to_wait))
        
        # Create callrequest
        cr = Callrequest(
            request_uuid=uuid.uuid4(),
            user=campaign.user,
            campaign=campaign,
            subscriber=subscriber,
            phone_number=phone_number,
            callerid=campaign.callerid,
            aleg_gateway=campaign.aleg_gateway,
            content_type=campaign.content_type,
            object_id=campaign.object_id,
            timeout=campaign.calltimeout,
            timelimit=campaign.callmaxduration,
            call_time=eta,
            call_type=call_type,
            status=CallrequestStatus.PENDING,
        )
        callrequests.append(cr)
    
    # Bulk create callrequests
    if callrequests:
        Callrequest.objects.bulk_create(callrequests)
        logger.info(f"Created {len(callrequests)} callrequests")
        
        # Schedule init_callrequest for each (with ETA)
        for cr in callrequests:
            init_callrequest.apply_async(
                args=[cr.id],
                eta=cr.call_time
            )
    
    return True


@shared_task(name='dialer_campaign.collect_subscriber', ignore_result=True)
def collect_subscriber(campaign_id: int) -> bool:
    """
    Import contacts from phonebook(s) to campaign subscribers.
    
    This task:
    1. Fetches all contacts from campaign's phonebooks
    2. Checks DNC list
    3. Checks whitelist/blacklist
    4. Creates Subscriber records (deduplicates)
    
    Args:
        campaign_id: Campaign to import subscribers for
        
    Returns:
        True if successful
    """
    logger.info(f"TASK :: collect_subscriber campaign_id={campaign_id}")
    
    try:
        campaign = Campaign.objects.prefetch_related('phonebook').get(id=campaign_id)
    except Campaign.DoesNotExist:
        logger.error(f"Campaign {campaign_id} not found")
        return False
    
    imported_count = 0
    skipped_count = 0
    
    # Get all contacts from all phonebooks
    for phonebook in campaign.phonebook.all():
        contacts = phonebook.contacts.filter(status=1)  # Active contacts only
        
        logger.info(f"Processing {contacts.count()} contacts from phonebook '{phonebook.name}'")
        
        for contact in contacts:
            phone_number = str(contact.contact)
            
            # Check if already exists
            if Subscriber.objects.filter(
                campaign=campaign,
                duplicate_contact=phone_number
            ).exists():
                skipped_count += 1
                continue
            
            # Check DNC
            if campaign.dnc and _check_dnc(campaign.dnc, phone_number):
                logger.debug(f"Contact {phone_number} in DNC list")
                skipped_count += 1
                continue
            
            # Check whitelist/blacklist
            if not _is_authorized_contact(campaign, phone_number):
                skipped_count += 1
                continue
            
            # Create subscriber
            Subscriber.objects.create(
                campaign=campaign,
                contact=contact,
                duplicate_contact=phone_number,
                status=SubscriberStatus.PENDING
            )
            imported_count += 1
    
    # Update campaign total
    campaign.totalcontact = Subscriber.objects.filter(campaign=campaign).count()
    campaign.save(update_fields=['totalcontact'])
    
    logger.info(
        f"Imported {imported_count} subscribers, skipped {skipped_count} "
        f"for campaign {campaign.name}"
    )
    
    return True


def _is_authorized_contact(campaign: Campaign, phone_number: str) -> bool:
    """
    Check if contact is authorized based on whitelist/blacklist.
    
    Args:
        campaign: Campaign with user->dialersetting
        phone_number: Phone number to check
        
    Returns:
        True if authorized, False otherwise
    """
    import re
    
    try:
        dialersetting = campaign.user.profile.dialersetting
        if not dialersetting:
            return True  # No restrictions
        
        whitelist = dialersetting.whitelist
        blacklist = dialersetting.blacklist
        
        if whitelist == '*':
            whitelist = ''
        if blacklist == '*':
            blacklist = ''
        
        # Check whitelist first (if configured)
        if whitelist and len(whitelist) > 0:
            try:
                if re.search(whitelist, phone_number):
                    return True
                else:
                    return False  # Not in whitelist
            except Exception as e:
                logger.error(f"Error in whitelist regex: {e}")
        
        # Check blacklist
        if blacklist and len(blacklist) > 0:
            try:
                if re.search(blacklist, phone_number):
                    return False  # In blacklist
            except Exception as e:
                logger.error(f"Error in blacklist regex: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error checking contact authorization: {e}")
        return True  # Default to allow


def _check_dnc(dnc, phone_number: str) -> bool:
    """
    Check if phone number is in DNC list.
    
    Args:
        dnc: DNC instance
        phone_number: Phone number to check
        
    Returns:
        True if in DNC, False otherwise
    """
    if not dnc:
        return False
    
    from apps.dnc.models import DNCContact
    
    try:
        return DNCContact.objects.filter(
            dnc=dnc,
            phone_number=phone_number
        ).exists()
    except Exception as e:
        logger.error(f"Error checking DNC: {e}")
        return False


def _is_in_dnc(dnc, phone_number: str) -> bool:
    """
    Alias for _check_dnc for consistency.
    """
    return _check_dnc(dnc, phone_number)
