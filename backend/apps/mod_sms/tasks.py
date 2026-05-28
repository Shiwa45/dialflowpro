"""
Celery tasks for SMS campaigns.
Handles SMS sending via various gateways.
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(name='sms_campaign_running')
def sms_campaign_running():
    """
    Periodic task to process running SMS campaigns.
    Runs every 60 seconds (similar to campaign_running for voice).
    
    Finds campaigns with status=START and creates SmsMessage records.
    """
    from .models import SmsCampaign, SmsMessage
    from .constants import SmsCampaignStatus, SmsStatus
    from apps.dialer_contact.models import Contact
    
    now = timezone.now()
    
    # Find running campaigns
    campaigns = SmsCampaign.objects.filter(
        status=SmsCampaignStatus.START,
        startingdate__lte=now,
        expirationdate__gte=now
    ).select_related('gateway')
    
    for campaign in campaigns:
        logger.info(f"Processing SMS campaign: {campaign.name}")
        
        # Get contacts from phonebooks
        phonebooks = campaign.phonebook.all()
        contacts = Contact.objects.filter(
            phonebook__in=phonebooks,
            status=1  # ACTIVE
        ).exclude(
            contact__in=SmsMessage.objects.filter(
                sms_campaign=campaign
            ).values_list('recipient', flat=True)
        )
        
        # Respect frequency (messages per minute)
        batch_size = campaign.frequency
        contacts_to_process = contacts[:batch_size]
        
        # Create SmsMessage records
        messages_created = 0
        for contact in contacts_to_process:
            try:
                message = SmsMessage.objects.create(
                    recipient=contact.contact,
                    sender=str(campaign.gateway.from_number or campaign.gateway.from_name),
                    message=campaign.message_text,
                    gateway=campaign.gateway,
                    status=SmsStatus.PENDING,
                    sms_campaign=campaign,
                    user=campaign.user
                )
                
                # Trigger send task
                sms_send_message.delay(message.id)
                messages_created += 1
                
            except Exception as e:
                logger.error(f"Error creating SMS message for {contact.contact}: {e}")
        
        logger.info(f"Created {messages_created} SMS messages for campaign {campaign.id}")
        
        # Check if campaign completed
        if contacts.count() == 0:
            campaign.status = SmsCampaignStatus.END
            campaign.save(update_fields=['status'])
            logger.info(f"SMS campaign {campaign.id} completed")


@shared_task(name='sms_send_message')
def sms_send_message(message_id):
    """
    Send individual SMS message via gateway.
    
    Args:
        message_id: SmsMessage ID to send
    """
    from .models import SmsMessage
    from .constants import SmsStatus, SmsGatewayType
    
    try:
        message = SmsMessage.objects.select_related('gateway').get(id=message_id)
    except SmsMessage.DoesNotExist:
        logger.error(f"SmsMessage {message_id} not found")
        return
    
    gateway = message.gateway
    
    try:
        # Send via appropriate gateway
        if gateway.gateway_type == SmsGatewayType.TWILIO:
            result = _send_via_twilio(message, gateway)
        elif gateway.gateway_type == SmsGatewayType.PLIVO:
            result = _send_via_plivo(message, gateway)
        elif gateway.gateway_type == SmsGatewayType.NEXMO:
            result = _send_via_nexmo(message, gateway)
        elif gateway.gateway_type == SmsGatewayType.CLICKATELL:
            result = _send_via_clickatell(message, gateway)
        elif gateway.gateway_type == SmsGatewayType.CUSTOM:
            result = _send_via_custom_http(message, gateway)
        else:
            raise ValueError(f"Unsupported gateway type: {gateway.gateway_type}")
        
        # Update message status
        message.status = SmsStatus.SENT
        message.gateway_message_id = result.get('message_id', '')
        message.sent_date = timezone.now()
        message.save(update_fields=['status', 'gateway_message_id', 'sent_date'])
        
        # Update campaign statistics
        if message.sms_campaign:
            message.sms_campaign.total_sent += 1
            message.sms_campaign.save(update_fields=['total_sent'])
        
        logger.info(f"SMS sent successfully: {message.id}")
        
    except Exception as e:
        logger.error(f"Error sending SMS {message.id}: {e}")
        message.status = SmsStatus.FAILED
        message.error = str(e)
        message.save(update_fields=['status', 'error'])
        
        # Update campaign statistics
        if message.sms_campaign:
            message.sms_campaign.total_failed += 1
            message.sms_campaign.save(update_fields=['total_failed'])


def _send_via_twilio(message, gateway):
    """Send SMS via Twilio"""
    try:
        from twilio.rest import Client
        
        client = Client(gateway.account_sid, gateway.auth_token)
        
        result = client.messages.create(
            to=str(message.recipient),
            from_=str(gateway.from_number),
            body=message.message
        )
        
        return {'message_id': result.sid}
        
    except ImportError:
        raise ImportError("twilio package not installed. Run: pip install twilio")


def _send_via_plivo(message, gateway):
    """Send SMS via Plivo"""
    try:
        import plivo
        
        client = plivo.RestClient(gateway.account_sid, gateway.auth_token)
        
        result = client.messages.create(
            src=str(gateway.from_number),
            dst=str(message.recipient),
            text=message.message
        )
        
        return {'message_id': result['message_uuid'][0]}
        
    except ImportError:
        raise ImportError("plivo package not installed. Run: pip install plivo")


def _send_via_nexmo(message, gateway):
    """Send SMS via Nexmo/Vonage"""
    try:
        import vonage
        
        client = vonage.Client(key=gateway.api_key, secret=gateway.auth_token)
        sms = vonage.Sms(client)
        
        result = sms.send_message({
            'from': str(gateway.from_number or gateway.from_name),
            'to': str(message.recipient),
            'text': message.message
        })
        
        if result['messages'][0]['status'] == '0':
            return {'message_id': result['messages'][0]['message-id']}
        else:
            raise Exception(f"Nexmo error: {result['messages'][0]['error-text']}")
        
    except ImportError:
        raise ImportError("vonage package not installed. Run: pip install vonage")


def _send_via_clickatell(message, gateway):
    """Send SMS via Clickatell"""
    import requests
    
    url = "https://platform.clickatell.com/messages/http/send"
    
    params = {
        'apiKey': gateway.api_key,
        'to': str(message.recipient),
        'content': message.message
    }
    
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        data = response.json()
        return {'message_id': data.get('messages', [{}])[0].get('apiMessageId', '')}
    else:
        raise Exception(f"Clickatell error: {response.text}")


def _send_via_custom_http(message, gateway):
    """Send SMS via custom HTTP gateway"""
    import requests
    
    # Custom implementation - depends on gateway's API
    # This is a basic template
    
    url = gateway.base_url
    
    payload = {
        'to': str(message.recipient),
        'from': str(gateway.from_number or gateway.from_name),
        'message': message.message,
        'api_key': gateway.api_key
    }
    
    response = requests.post(url, json=payload)
    
    if response.status_code == 200:
        data = response.json()
        return {'message_id': data.get('message_id', '')}
    else:
        raise Exception(f"Custom gateway error: {response.text}")
