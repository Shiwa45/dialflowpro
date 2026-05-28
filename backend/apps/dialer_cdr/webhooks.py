"""
FreeSWITCH webhook handlers.
Called by FreeSWITCH when calls complete or AMD detects.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.dateparse import parse_datetime
import logging
from .models import Callrequest, VoIPCall
from .constants import CallrequestStatus, CallrequestType, AmdStatus, CallDisposition
from apps.dialer_campaign.models import Subscriber
from apps.dialer_campaign.constants import SubscriberStatus

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def hangup_webhook(request):
    """
    FreeSWITCH hangup webhook.
    
    Called when a call ends. Creates VoIPCall CDR and updates Callrequest.
    
    Expected POST data from FreeSWITCH:
    - callid (UUID)
    - request_uuid
    - callerid
    - phone_number
    - start_time
    - duration
    - billsec
    - disposition
    - hangup_cause
    - amd_status (optional)
    """
    try:
        # Parse FreeSWITCH data
        callid = request.POST.get('callid')
        request_uuid = request.POST.get('request_uuid')
        
        if not callid or not request_uuid:
            logger.error("Missing callid or request_uuid in hangup webhook")
            return JsonResponse({'error': 'Missing required fields'}, status=400)
        
        # Find Callrequest
        try:
            callrequest = Callrequest.objects.select_related(
                'campaign', 'subscriber', 'user'
            ).get(request_uuid=request_uuid)
        except Callrequest.DoesNotExist:
            logger.error(f"Callrequest not found: {request_uuid}")
            return JsonResponse({'error': 'Callrequest not found'}, status=404)
        
        # Parse call data
        duration = int(request.POST.get('duration', 0))
        billsec = int(request.POST.get('billsec', 0))
        disposition = request.POST.get('disposition', 'FAILED')
        hangup_cause = request.POST.get('hangup_cause', '')
        
        # Create VoIPCall CDR
        voipcall = VoIPCall.objects.create(
            callid=callid,
            callerid=request.POST.get('callerid', ''),
            phone_number=callrequest.phone_number,
            starting_date=parse_datetime(request.POST.get('start_time')) or timezone.now(),
            duration=duration,
            billsec=billsec,
            disposition=disposition,
            hangup_cause=hangup_cause,
            hangup_cause_q850=request.POST.get('hangup_cause_q850', ''),
            user=callrequest.user,
            callrequest=callrequest,
        )
        
        # Update AMD status if present
        amd_status = request.POST.get('amd_status')
        if amd_status:
            amd_map = {'PERSON': AmdStatus.PERSON, 'MACHINE': AmdStatus.MACHINE, 'NOTSURE': AmdStatus.NOTSURE}
            voipcall.amd_status = amd_map.get(amd_status.upper())
            voipcall.save(update_fields=['amd_status'])
        
        # Update Callrequest status
        if disposition in ['ANSWER', 'NORMAL_CLEARING']:
            callrequest.status = CallrequestStatus.SUCCESS
            callrequest.completed = True
        else:
            callrequest.status = CallrequestStatus.FAILURE
        
        callrequest.result = disposition
        callrequest.hangup_cause = hangup_cause
        callrequest.save(update_fields=['status', 'completed', 'result', 'hangup_cause'])
        
        # Update Subscriber status
        if callrequest.subscriber:
            subscriber = callrequest.subscriber
            
            if callrequest.completed:
                # Call completed successfully
                subscriber.status = SubscriberStatus.COMPLETED
                subscriber.save(update_fields=['status'])
                
                # Update campaign completed count
                if callrequest.campaign:
                    callrequest.campaign.completed += 1
                    callrequest.campaign.save(update_fields=['completed'])
            else:
                # Check if retry needed
                campaign = callrequest.campaign
                if campaign and subscriber.count_attempt < campaign.maxretry:
                    # Retry allowed
                    subscriber.status = SubscriberStatus.PENDING
                    subscriber.save(update_fields=['status'])
                else:
                    # Max retries reached
                    subscriber.status = SubscriberStatus.FAIL
                    subscriber.save(update_fields=['status'])
        
        logger.info(f"Hangup processed: {callid}, disposition={disposition}")
        
        return JsonResponse({
            'status': 'ok',
            'callid': callid,
            'voipcall_id': voipcall.id
        })
        
    except Exception as e:
        logger.error(f"Error in hangup_webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def amd_webhook(request):
    """
    AMD (Answering Machine Detection) webhook.
    
    Called when AMD detection completes during call.
    Updates VoIPCall with AMD status.
    
    Expected POST data:
    - callid
    - amd_status (PERSON, MACHINE, NOTSURE)
    """
    try:
        callid = request.POST.get('callid')
        amd_status = request.POST.get('amd_status', '').upper()
        
        if not callid:
            return JsonResponse({'error': 'Missing callid'}, status=400)
        
        # Map AMD status
        amd_map = {
            'PERSON': AmdStatus.PERSON,
            'MACHINE': AmdStatus.MACHINE,
            'NOTSURE': AmdStatus.NOTSURE
        }
        
        amd_value = amd_map.get(amd_status)
        if not amd_value:
            return JsonResponse({'error': 'Invalid amd_status'}, status=400)
        
        # Update VoIPCall (if exists)
        try:
            voipcall = VoIPCall.objects.get(callid=callid)
            voipcall.amd_status = amd_value
            voipcall.save(update_fields=['amd_status'])
            
            logger.info(f"AMD updated: {callid}, status={amd_status}")
            
            return JsonResponse({'status': 'ok', 'amd_status': amd_status})
        except VoIPCall.DoesNotExist:
            # VoIPCall not created yet (call still in progress)
            # AMD status will be set when hangup webhook creates the record
            logger.warning(f"VoIPCall not found for AMD update: {callid}")
            return JsonResponse({'status': 'pending'})
        
    except Exception as e:
        logger.error(f"Error in amd_webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)
