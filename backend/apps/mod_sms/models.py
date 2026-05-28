"""SMS models for SMS campaigns"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import TimeStampedModel
from .constants import SmsGatewayType, SmsStatus, SmsCampaignStatus


class SmsGateway(TimeStampedModel):
    """
    SMS Gateway configuration.
    Supports Twilio, Plivo, Nexmo, etc.
    """
    name = models.CharField(
        max_length=128,
        verbose_name=_('gateway name')
    )
    
    gateway_type = models.IntegerField(
        choices=SmsGatewayType.choices,
        default=SmsGatewayType.TWILIO,
        verbose_name=_('gateway type')
    )
    
    # API credentials
    account_sid = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('account SID'),
        help_text=_('Twilio Account SID or equivalent')
    )
    
    auth_token = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('auth token'),
        help_text=_('API authentication token')
    )
    
    api_key = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('API key')
    )
    
    # Custom HTTP gateway
    base_url = models.URLField(
        blank=True,
        verbose_name=_('base URL'),
        help_text=_('For custom HTTP gateways')
    )
    
    # From number
    from_number = PhoneNumberField(
        blank=True,
        null=True,
        verbose_name=_('from number'),
        help_text=_('Sender phone number')
    )
    
    from_name = models.CharField(
        max_length=15,
        blank=True,
        verbose_name=_('from name'),
        help_text=_('Sender ID (alphanumeric)')
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('active')
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sms_gateways',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'sms_gateway'
        verbose_name = _('SMS gateway')
        verbose_name_plural = _('SMS gateways')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} ({self.get_gateway_type_display()})"


class SmsMessage(TimeStampedModel):
    """
    Individual SMS message.
    Tracks delivery status.
    """
    recipient = PhoneNumberField(
        verbose_name=_('recipient')
    )
    
    sender = models.CharField(
        max_length=80,
        verbose_name=_('sender'),
        help_text=_('From number or sender ID')
    )
    
    message = models.TextField(
        max_length=1600,
        verbose_name=_('message text'),
        help_text=_('SMS message content (max 1600 chars)')
    )
    
    # Gateway
    gateway = models.ForeignKey(
        SmsGateway,
        on_delete=models.SET_NULL,
        null=True,
        related_name='messages',
        verbose_name=_('gateway')
    )
    
    # Status
    status = models.IntegerField(
        choices=SmsStatus.choices,
        default=SmsStatus.PENDING,
        verbose_name=_('status')
    )
    
    # External ID from gateway
    gateway_message_id = models.CharField(
        max_length=255,
        blank=True,
        verbose_name=_('gateway message ID'),
        help_text=_('External message ID from SMS provider')
    )
    
    # Timestamps
    sent_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('sent date')
    )
    
    delivered_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('delivered date')
    )
    
    # Error info
    error = models.TextField(
        blank=True,
        verbose_name=_('error message')
    )
    
    # Link to campaign
    sms_campaign = models.ForeignKey(
        'SmsCampaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='messages',
        verbose_name=_('SMS campaign')
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sms_messages',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'sms_message'
        verbose_name = _('SMS message')
        verbose_name_plural = _('SMS messages')
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['recipient']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"SMS to {self.recipient} - {self.get_status_display()}"


class SmsCampaign(TimeStampedModel):
    """
    SMS campaign for mass texting.
    Similar to voice campaigns but for SMS.
    """
    name = models.CharField(
        max_length=128,
        verbose_name=_('campaign name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Status
    status = models.IntegerField(
        choices=SmsCampaignStatus.choices,
        default=SmsCampaignStatus.DRAFT,
        verbose_name=_('status')
    )
    
    # Message
    message_text = models.TextField(
        max_length=1600,
        verbose_name=_('message text')
    )
    
    # Gateway
    gateway = models.ForeignKey(
        SmsGateway,
        on_delete=models.PROTECT,
        related_name='campaigns',
        verbose_name=_('SMS gateway')
    )
    
    # Recipients
    phonebook = models.ManyToManyField(
        'dialer_contact.Phonebook',
        verbose_name=_('phonebooks'),
        help_text=_('Contact lists to send to')
    )
    
    # Schedule
    startingdate = models.DateTimeField(
        verbose_name=_('start date')
    )
    
    expirationdate = models.DateTimeField(
        verbose_name=_('expiration date')
    )
    
    # Frequency (messages per minute)
    frequency = models.IntegerField(
        default=10,
        verbose_name=_('frequency'),
        help_text=_('Messages per minute')
    )
    
    # Statistics
    total_sent = models.PositiveIntegerField(
        default=0,
        verbose_name=_('total sent')
    )
    
    total_delivered = models.PositiveIntegerField(
        default=0,
        verbose_name=_('total delivered')
    )
    
    total_failed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('total failed')
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='sms_campaigns',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'sms_campaign'
        verbose_name = _('SMS campaign')
        verbose_name_plural = _('SMS campaigns')
        ordering = ['-created_date']
    
    def __str__(self):
        return self.name
