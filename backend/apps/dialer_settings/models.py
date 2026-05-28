"""
DialerSetting model - per-tenant dialer configuration and limits.
Preserves all fields from original dialer_settings.DialerSetting model.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel


class DialerSetting(TimeStampedModel):
    """
    Per-tenant dialer limit configuration.
    All fields preserved 1-to-1 from original Newfies-Dialer.
    
    Controls:
    - Voice campaign limits (frequency, duration, retries, timeouts)
    - SMS campaign limits
    - Contact/subscriber limits
    - Whitelist/blacklist regex patterns
    """
    name = models.CharField(
        max_length=50,
        verbose_name=_('name'),
        help_text=_('Settings name')
    )
    
    # Tenant relationship (one setting per tenant)
    tenant = models.OneToOneField(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        related_name='dialer_setting',
        help_text=_('Tenant these settings apply to')
    )
    
    # ── Voice Campaign Limits ──────────────────────────────────
    
    max_frequency = models.PositiveIntegerField(
        default=100,
        verbose_name=_('max frequency'),
        help_text=_('Maximum calls per minute')
    )
    
    callmaxduration = models.PositiveIntegerField(
        default=1800,
        verbose_name=_('max call duration'),
        help_text=_('Maximum call duration in seconds (1800 = 30 minutes)')
    )
    
    maxretry = models.PositiveIntegerField(
        default=3,
        verbose_name=_('max retries'),
        help_text=_('Maximum retries per contact')
    )
    
    max_calltimeout = models.PositiveIntegerField(
        default=45,
        verbose_name=_('timeout on call'),
        help_text=_('Maximum call timeout in seconds')
    )
    
    max_cpg = models.PositiveIntegerField(
        default=100,
        verbose_name=_('maximum number of campaigns'),
        help_text=_('Maximum number of campaigns per tenant')
    )
    
    max_subr_cpg = models.PositiveIntegerField(
        default=100000,
        verbose_name=_('maximum subscribers per campaign'),
        help_text=_('Maximum subscribers per campaign. Unlimited if 0')
    )
    
    max_contact = models.PositiveIntegerField(
        default=1000000,
        verbose_name=_('maximum number of contacts'),
        help_text=_('Maximum number of contacts per tenant. Unlimited if 0')
    )
    
    # ── Number Filtering (Regex Patterns) ─────────────────────
    
    blacklist = models.TextField(
        blank=True,
        default='',
        verbose_name=_('blacklist'),
        help_text=_(
            "Use regular expressions to blacklist phone numbers. "
            "Example: '^[2-4][1]+' blocks numbers starting with 2,3,4 followed by 1"
        )
    )
    
    whitelist = models.TextField(
        blank=True,
        default='',
        verbose_name=_('whitelist'),
        help_text=_('Use regular expressions to whitelist phone numbers')
    )
    
    # ── SMS Campaign Limits ────────────────────────────────────
    
    sms_max_frequency = models.PositiveIntegerField(
        default=100,
        verbose_name=_('max SMS frequency'),
        help_text=_('Maximum SMS per minute')
    )
    
    sms_maxretry = models.PositiveIntegerField(
        default=3,
        verbose_name=_('max SMS retries'),
        help_text=_('Maximum SMS retries per contact')
    )
    
    sms_max_number_campaign = models.PositiveIntegerField(
        default=10,
        verbose_name=_('max SMS campaigns'),
        help_text=_('Maximum number of SMS campaigns')
    )
    
    sms_max_number_subscriber_campaign = models.PositiveIntegerField(
        default=10000,
        verbose_name=_('max subscribers of SMS campaigns'),
        help_text=_('Maximum subscribers per SMS campaign')
    )
    
    class Meta:
        db_table = 'dialer_setting'
        verbose_name = _('dialer setting')
        verbose_name_plural = _('dialer settings')
        ordering = ['name']
    
    def __str__(self):
        return f'{self.name} ({self.tenant.name})'
    
    def check_frequency_limit(self, current_frequency: int) -> bool:
        """Check if frequency is within limits"""
        return current_frequency <= self.max_frequency
    
    def check_campaign_limit(self, current_campaigns: int) -> bool:
        """Check if campaign count is within limits"""
        return current_campaigns < self.max_cpg
    
    def check_contact_limit(self, current_contacts: int) -> bool:
        """Check if contact count is within limits"""
        if self.max_contact == 0:  # Unlimited
            return True
        return current_contacts < self.max_contact
