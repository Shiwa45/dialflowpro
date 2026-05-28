"""
SMS gateway webhook handlers.
Receive delivery status updates from SMS providers.
"""
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
import logging
from .models import SmsMessage
from .constants import SmsStatus

logger = logging.getLogger(__name__)


@csrf_exempt
@require_POST
def twilio_webhook(request):
    """
    Twilio delivery status webhook.
    
    POST data from Twilio:
    - MessageSid: Message ID
    - MessageStatus: sent, delivered, undelivered, failed
    - ErrorCode: Error code if failed
    """
    try:
        message_sid = request.POST.get('MessageSid')
        message_status = request.POST.get('MessageStatus', '').lower()
        error_code = request.POST.get('ErrorCode', '')
        
        if not message_sid:
            return JsonResponse({'error': 'MessageSid required'}, status=400)
        
        # Find message by gateway_message_id
        try:
            message = SmsMessage.objects.get(gateway_message_id=message_sid)
        except SmsMessage.DoesNotExist:
            logger.warning(f"SMS message not found: {message_sid}")
            return JsonResponse({'status': 'not_found'}, status=404)
        
        # Update status
        if message_status == 'delivered':
            message.status = SmsStatus.DELIVERED
            message.delivered_date = timezone.now()
            
            # Update campaign statistics
            if message.sms_campaign:
                message.sms_campaign.total_delivered += 1
                message.sms_campaign.save(update_fields=['total_delivered'])
                
        elif message_status in ['undelivered', 'failed']:
            message.status = SmsStatus.FAILED
            message.error = f"Twilio error: {error_code}" if error_code else "Delivery failed"
            
        elif message_status == 'sent':
            message.status = SmsStatus.SENT
            message.sent_date = timezone.now()
        
        message.save(update_fields=['status', 'delivered_date', 'error'])
        
        logger.info(f"Twilio webhook processed: {message_sid}, status={message_status}")
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error in Twilio webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def plivo_webhook(request):
    """
    Plivo delivery status webhook.
    
    POST data from Plivo:
    - MessageUUID: Message UUID
    - Status: queued, sent, delivered, undelivered, rejected
    - ErrorCode: Error code if failed
    """
    try:
        message_uuid = request.POST.get('MessageUUID')
        status = request.POST.get('Status', '').lower()
        error_code = request.POST.get('ErrorCode', '')
        
        if not message_uuid:
            return JsonResponse({'error': 'MessageUUID required'}, status=400)
        
        try:
            message = SmsMessage.objects.get(gateway_message_id=message_uuid)
        except SmsMessage.DoesNotExist:
            logger.warning(f"SMS message not found: {message_uuid}")
            return JsonResponse({'status': 'not_found'}, status=404)
        
        # Update status
        if status == 'delivered':
            message.status = SmsStatus.DELIVERED
            message.delivered_date = timezone.now()
            
            if message.sms_campaign:
                message.sms_campaign.total_delivered += 1
                message.sms_campaign.save(update_fields=['total_delivered'])
                
        elif status in ['undelivered', 'rejected']:
            message.status = SmsStatus.FAILED
            message.error = f"Plivo error: {error_code}" if error_code else "Delivery failed"
            
        elif status == 'sent':
            message.status = SmsStatus.SENT
            message.sent_date = timezone.now()
        
        message.save(update_fields=['status', 'delivered_date', 'error'])
        
        logger.info(f"Plivo webhook processed: {message_uuid}, status={status}")
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error in Plivo webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@require_POST
def nexmo_webhook(request):
    """
    Nexmo/Vonage delivery receipt webhook.
    
    POST data from Nexmo:
    - messageId: Message ID
    - status: delivered, failed, rejected
    - err-code: Error code if failed
    """
    try:
        message_id = request.POST.get('messageId')
        status = request.POST.get('status', '').lower()
        error_code = request.POST.get('err-code', '')
        
        if not message_id:
            return JsonResponse({'error': 'messageId required'}, status=400)
        
        try:
            message = SmsMessage.objects.get(gateway_message_id=message_id)
        except SmsMessage.DoesNotExist:
            logger.warning(f"SMS message not found: {message_id}")
            return JsonResponse({'status': 'not_found'}, status=404)
        
        # Update status
        if status == 'delivered':
            message.status = SmsStatus.DELIVERED
            message.delivered_date = timezone.now()
            
            if message.sms_campaign:
                message.sms_campaign.total_delivered += 1
                message.sms_campaign.save(update_fields=['total_delivered'])
                
        elif status in ['failed', 'rejected', 'expired']:
            message.status = SmsStatus.FAILED
            message.error = f"Nexmo error: {error_code}" if error_code else "Delivery failed"
        
        message.save(update_fields=['status', 'delivered_date', 'error'])
        
        logger.info(f"Nexmo webhook processed: {message_id}, status={status}")
        
        return JsonResponse({'status': 'ok'})
        
    except Exception as e:
        logger.error(f"Error in Nexmo webhook: {e}")
        return JsonResponse({'error': str(e)}, status=500)
