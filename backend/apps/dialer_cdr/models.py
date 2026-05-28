"""
Callrequest and VoIPCall models.
Core CDR (Call Detail Record) models for the dialer.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import uuid
from apps.common.models import TimeStampedModel
from .constants import (
    CallrequestStatus, CallrequestType, LegType, 
    CallDisposition, AmdStatus
)


class CallrequestManager(models.Manager):
    """Manager for Callrequest with custom queries"""
    
    def get_pending_callrequests(self):
        """Get pending callrequests ready to dial"""
        return self.filter(status=CallrequestStatus.PENDING).order_by('call_time')


class Callrequest(TimeStampedModel):
    """
    Callrequest - individual call to be made.
    Created by campaign spooling, executed by init_callrequest task.
    Mirrors original dialer_cdr.Callrequest model.
    """
    # Unique identifier
    request_uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True,
        unique=True,
        verbose_name=_('request UUID')
    )
    
    # Status
    status = models.IntegerField(
        choices=CallrequestStatus.choices,
        default=CallrequestStatus.PENDING,
        db_index=True,
        verbose_name=_('status')
    )
    
    call_type = models.IntegerField(
        choices=CallrequestType.choices,
        default=CallrequestType.ALLOW_RETRY,
        verbose_name=_('call type')
    )
    
    # Call details
    call_time = models.DateTimeField(
        db_index=True,
        verbose_name=_('scheduled call time'),
        help_text=_('When this call should be initiated')
    )
    
    phone_number = models.CharField(
        max_length=80,
        db_index=True,
        verbose_name=_('phone number')
    )
    
    callerid = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('caller ID')
    )
    
    # Call parameters
    timeout = models.PositiveIntegerField(
        default=30,
        verbose_name=_('timeout'),
        help_text=_('Seconds to wait for answer')
    )
    
    timelimit = models.PositiveIntegerField(
        default=3600,
        verbose_name=_('time limit'),
        help_text=_('Maximum call duration in seconds')
    )
    
    extra_dial_string = models.CharField(
        max_length=500,
        blank=True,
        verbose_name=_('extra dial string'),
        help_text=_('Additional FreeSWITCH dial parameters')
    )
    
    # Attempt tracking
    num_attempt = models.PositiveIntegerField(
        default=0,
        verbose_name=_('number of attempts')
    )
    
    last_attempt_time = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('last attempt time')
    )
    
    # Result
    result = models.CharField(
        max_length=180,
        blank=True,
        verbose_name=_('result')
    )
    
    hangup_cause = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('hangup cause')
    )
    
    # Completion flag
    completed = models.BooleanField(
        default=False,
        db_index=True,
        verbose_name=_('completed')
    )
    
    # Extra data
    extra_data = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('extra data')
    )
    
    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='callrequests',
        verbose_name=_('user')
    )
    
    campaign = models.ForeignKey(
        'dialer_campaign.Campaign',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='callrequests',
        verbose_name=_('campaign')
    )
    
    subscriber = models.ForeignKey(
        'dialer_campaign.Subscriber',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='callrequests',
        verbose_name=_('subscriber')
    )
    
    aleg_gateway = models.ForeignKey(
        'dialer_gateway.Gateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='callrequests',
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
    
    # Parent callrequest (for transfer scenarios)
    parent_callrequest = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_callrequests',
        verbose_name=_('parent callrequest')
    )
    
    # Appointment/alarm reference
    alarm_request_id = models.PositiveIntegerField(
        default=0,
        verbose_name=_('alarm request ID')
    )
    
    # Manager
    objects = CallrequestManager()
    
    class Meta:
        db_table = 'dialer_callrequest'
        verbose_name = _('call request')
        verbose_name_plural = _('call requests')
        ordering = ['call_time']
        indexes = [
            models.Index(fields=['status', 'call_time']),
            models.Index(fields=['campaign', 'status']),
        ]
    
    def __str__(self):
        return f"{self.phone_number} [{self.get_status_display()}]"


class VoIPCall(TimeStampedModel):
    """
    VoIPCall - CDR record after call completes.
    Created by FreeSWITCH hangup webhook.
    Mirrors original dialer_cdr.VoIPCall model.
    """
    # Call identification
    callid = models.CharField(
        max_length=120,
        db_index=True,
        verbose_name=_('call ID'),
        help_text=_('FreeSWITCH UUID')
    )
    
    callerid = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('caller ID')
    )
    
    phone_number = models.CharField(
        max_length=120,
        db_index=True,
        verbose_name=_('phone number')
    )
    
    # Call timestamps
    starting_date = models.DateTimeField(
        db_index=True,
        verbose_name=_('start time')
    )
    
    duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('duration'),
        help_text=_('Call duration in seconds')
    )
    
    billsec = models.PositiveIntegerField(
        default=0,
        verbose_name=_('bill seconds'),
        help_text=_('Billable seconds (after answer)')
    )
    
    # Call result
    disposition = models.CharField(
        max_length=40,
        choices=CallDisposition.choices,
        blank=True,
        db_index=True,
        verbose_name=_('disposition')
    )
    
    hangup_cause = models.CharField(
        max_length=40,
        blank=True,
        verbose_name=_('hangup cause')
    )
    
    hangup_cause_q850 = models.CharField(
        max_length=10,
        blank=True,
        verbose_name=_('Q.850 cause code')
    )
    
    # AMD (Answering Machine Detection)
    amd_status = models.IntegerField(
        choices=AmdStatus.choices,
        null=True,
        blank=True,
        verbose_name=_('AMD status')
    )
    
    # Call leg type
    leg_type = models.IntegerField(
        choices=LegType.choices,
        default=LegType.A_LEG,
        verbose_name=_('leg type')
    )
    
    # Billing/cost (optional)
    buy_rate = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_('buy rate')
    )
    
    buy_cost = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_('buy cost')
    )
    
    sell_rate = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_('sell rate')
    )
    
    sell_cost = models.DecimalField(
        max_digits=10,
        decimal_places=5,
        null=True,
        blank=True,
        verbose_name=_('sell cost')
    )
    
    # Relationships
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='voip_calls',
        verbose_name=_('user')
    )
    
    callrequest = models.ForeignKey(
        Callrequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voip_calls',
        verbose_name=_('call request')
    )
    
    # Extra data from FreeSWITCH
    extradata = models.TextField(
        blank=True,
        verbose_name=_('extra data'),
        help_text=_('Additional CDR data from FreeSWITCH')
    )
    
    class Meta:
        db_table = 'dialer_cdr'
        verbose_name = _('VoIP call')
        verbose_name_plural = _('VoIP calls')
        ordering = ['-starting_date']
        indexes = [
            models.Index(fields=['disposition', 'starting_date']),
            models.Index(fields=['user', 'starting_date']),
        ]
    
    def __str__(self):
        return f"{self.callid} - {self.phone_number}"
