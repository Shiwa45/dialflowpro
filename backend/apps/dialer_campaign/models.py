"""
Campaign and Subscriber models.
Core of the dialer system - mirrors original dialer_campaign app.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from datetime import datetime, timedelta
import uuid
from apps.common.models import TimeStampedModel
from .constants import CampaignStatus, SubscriberStatus, AmdBehavior


def generate_campaign_code():
    """Generate unique campaign code"""
    return uuid.uuid4().hex[:5].upper()


class CampaignManager(models.Manager):
    """Campaign manager with custom querysets"""
    
    def get_running_campaigns(self):
        """Return all currently running campaigns"""
        now = timezone.now()
        today = now.strftime('%A').lower()
        
        return self.filter(
            status=CampaignStatus.START,
            startingdate__lte=now,
            expirationdate__gte=now,
        ).filter(**{today: True})


class Campaign(TimeStampedModel):
    """
    Campaign model - voice/SMS broadcast campaign.
    Mirrors original dialer_campaign.Campaign with all fields.
    """
    # Basic info
    campaign_code = models.CharField(
        max_length=20,
        unique=True,
        default=generate_campaign_code,
        editable=False,
        verbose_name=_('campaign code')
    )
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('campaign name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Status
    status = models.IntegerField(
        choices=CampaignStatus.choices,
        default=CampaignStatus.PENDING,
        verbose_name=_('status')
    )
    
    # Caller ID
    callerid = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('caller ID')
    )
    
    caller_name = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('caller name')
    )
    
    # Schedule
    startingdate = models.DateTimeField(
        verbose_name=_('starting date')
    )
    
    expirationdate = models.DateTimeField(
        verbose_name=_('expiration date')
    )
    
    daily_start_time = models.TimeField(
        default='00:00:00',
        verbose_name=_('daily start time')
    )
    
    daily_stop_time = models.TimeField(
        default='23:59:59',
        verbose_name=_('daily stop time')
    )
    
    # Days of week
    monday = models.BooleanField(default=True)
    tuesday = models.BooleanField(default=True)
    wednesday = models.BooleanField(default=True)
    thursday = models.BooleanField(default=True)
    friday = models.BooleanField(default=True)
    saturday = models.BooleanField(default=True)
    sunday = models.BooleanField(default=True)
    
    # Dialing settings
    frequency = models.PositiveIntegerField(
        default=10,
        verbose_name=_('frequency'),
        help_text=_('Calls per minute')
    )
    
    calltimeout = models.PositiveIntegerField(
        default=30,
        verbose_name=_('call timeout'),
        help_text=_('Seconds to wait for answer')
    )
    
    callmaxduration = models.PositiveIntegerField(
        default=1800,
        verbose_name=_('max call duration'),
        help_text=_('Maximum call duration in seconds')
    )
    
    maxretry = models.PositiveIntegerField(
        default=0,
        verbose_name=_('max retries'),
        help_text=_('Maximum retries per contact')
    )
    
    intervalretry = models.PositiveIntegerField(
        default=300,
        verbose_name=_('interval retry'),
        help_text=_('Seconds between retries')
    )
    
    completion_maxretry = models.PositiveIntegerField(
        default=0,
        verbose_name=_('completion max retries'),
        help_text=_('Retries for incomplete calls')
    )
    
    completion_intervalretry = models.PositiveIntegerField(
        default=900,
        verbose_name=_('completion interval retry'),
        help_text=_('Seconds between completion retries')
    )
    
    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='campaigns',
        verbose_name=_('user')
    )
    
    phonebook = models.ManyToManyField(
        'dialer_contact.Phonebook',
        blank=True,
        related_name='campaigns',
        verbose_name=_('phonebooks')
    )
    
    # DNC (Do-Not-Call) integration
    dnc_list = models.ForeignKey(
        'dnc.DNC',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name=_('DNC list'),
        help_text=_('Numbers in this DNC list will be skipped')
    )
    
    check_dnc = models.BooleanField(
        default=False,
        verbose_name=_('check DNC'),
        help_text=_('Check DNC list before calling')
    )
    
    aleg_gateway = models.ForeignKey(
        'dialer_gateway.Gateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='campaigns',
        verbose_name=_('A-leg gateway')
    )
    
    # Content - generic FK to Survey or AudioFile
    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # DNC
    dnc = models.ForeignKey(
        'dnc.DNC',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('DNC list')
    )
    
    # AMD (Answering Machine Detection)
    voicemail = models.BooleanField(
        default=False,
        verbose_name=_('detect voicemail')
    )
    
    amd_behavior = models.IntegerField(
        choices=AmdBehavior.choices,
        default=AmdBehavior.DISABLE,
        verbose_name=_('AMD behavior')
    )
    
    voicemail_audiofile = models.ForeignKey(
        'audiofield.AudioFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voicemail_campaigns',
        verbose_name=_('voicemail audio file')
    )
    
    # Meta fields
    extra_data = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('extra data')
    )
    
    external_link = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('external link')
    )
    
    # Flags
    has_been_started = models.BooleanField(
        default=False,
        verbose_name=_('has been started')
    )
    
    has_been_duplicated = models.BooleanField(
        default=False,
        verbose_name=_('has been duplicated')
    )
    
    # Import tracking
    imported_phonebook = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('imported phonebook')
    )
    
    # Statistics
    totalcontact = models.PositiveIntegerField(
        default=0,
        verbose_name=_('total contacts')
    )
    
    completed = models.PositiveIntegerField(
        default=0,
        verbose_name=_('completed')
    )
    
    # Manager
    objects = CampaignManager()
    
    class Meta:
        db_table = 'dialer_campaign'
        verbose_name = _('campaign')
        verbose_name_plural = _('campaigns')
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.name} [{self.get_status_display()}]"
    
    def is_running(self) -> bool:
        """Check if campaign should be running now"""
        now = timezone.now()
        today = now.strftime('%A').lower()
        
        return (
            self.status == CampaignStatus.START and
            self.startingdate <= now <= self.expirationdate and
            self.daily_start_time <= now.time() <= self.daily_stop_time and
            getattr(self, today) is True
        )


class Subscriber(TimeStampedModel):
    """
    Subscriber - links a contact to a campaign.
    Mirrors original dialer_campaign.Subscriber model.
    """
    campaign = models.ForeignKey(
        Campaign,
        on_delete=models.CASCADE,
        related_name='subscribers',
        verbose_name=_('campaign')
    )
    
    contact = models.ForeignKey(
        'dialer_contact.Contact',
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('contact')
    )
    
    # Duplicate contact (cached phone number)
    duplicate_contact = models.CharField(
        max_length=90,
        verbose_name=_('duplicate contact'),
        help_text=_('Cached phone number from contact')
    )
    
    # Status
    status = models.IntegerField(
        choices=SubscriberStatus.choices,
        default=SubscriberStatus.PENDING,
        verbose_name=_('status')
    )
    
    # Attempt tracking
    count_attempt = models.PositiveIntegerField(
        default=0,
        verbose_name=_('attempt count')
    )
    
    last_attempt = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last attempt')
    )
    
    # Completion tracking
    completion_count_attempt = models.PositiveIntegerField(
        default=0,
        verbose_name=_('completion attempt count')
    )
    
    last_completion_attempt = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last completion attempt')
    )
    
    class Meta:
        db_table = 'dialer_subscriber'
        verbose_name = _('subscriber')
        verbose_name_plural = _('subscribers')
        unique_together = [['campaign', 'contact']]
        ordering = ['created_date']
    
    def __str__(self):
        return f"{self.duplicate_contact} -> {self.campaign.name}"
