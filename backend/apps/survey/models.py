"""
Survey models for IVR builder.
Supports 10 section types with branching logic.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel
from .constants import SurveySectionType, SurveyStatus


class Survey(TimeStampedModel):
    """
    Survey - IVR flow definition.
    Container for multiple sections with branching.
    """
    name = models.CharField(
        max_length=90,
        verbose_name=_('survey name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Status
    status = models.IntegerField(
        choices=SurveyStatus.choices,
        default=SurveyStatus.DRAFT,
        verbose_name=_('status'),
        help_text=_('Draft surveys can be edited, Sealed surveys are locked')
    )
    
    # Entry point
    entry_section = models.ForeignKey(
        'SurveySection',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='entry_for_surveys',
        verbose_name=_('entry section'),
        help_text=_('First section to play when survey starts')
    )
    
    # Owner
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='surveys',
        verbose_name=_('user')
    )
    
    # Campaign count
    campaign_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('campaign count'),
        help_text=_('Number of campaigns using this survey')
    )
    
    class Meta:
        db_table = 'survey'
        verbose_name = _('survey')
        verbose_name_plural = _('surveys')
        ordering = ['-created_date']
    
    def __str__(self):
        return self.name
    
    def seal(self):
        """Seal survey - lock from editing"""
        self.status = SurveyStatus.SEALED
        self.save(update_fields=['status'])
    
    def is_sealed(self) -> bool:
        """Check if survey is sealed"""
        return self.status == SurveyStatus.SEALED


class SurveySection(TimeStampedModel):
    """
    Survey Section - individual IVR node.
    10 types: play, multi-choice, rating, capture, record, 
              transfer, hangup, conference, DNC, SMS.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='sections',
        verbose_name=_('survey')
    )
    
    # Section type
    section_type = models.IntegerField(
        choices=SurveySectionType.choices,
        verbose_name=_('section type')
    )
    
    # Basic info
    name = models.CharField(
        max_length=90,
        verbose_name=_('section name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    # Order/position in survey
    order = models.PositiveIntegerField(
        default=1,
        verbose_name=_('order')
    )
    
    # Audio file to play (for PLAY_MESSAGE, MULTI_CHOICE, etc.)
    audiofile = models.ForeignKey(
        'audiofield.AudioFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_sections',
        verbose_name=_('audio file')
    )
    
    # ── Type-specific fields ──────────────────────────────
    
    # MULTI_CHOICE, RATING: key choices
    key_0 = models.CharField(max_length=150, blank=True, verbose_name=_('key 0'))
    key_1 = models.CharField(max_length=150, blank=True, verbose_name=_('key 1'))
    key_2 = models.CharField(max_length=150, blank=True, verbose_name=_('key 2'))
    key_3 = models.CharField(max_length=150, blank=True, verbose_name=_('key 3'))
    key_4 = models.CharField(max_length=150, blank=True, verbose_name=_('key 4'))
    key_5 = models.CharField(max_length=150, blank=True, verbose_name=_('key 5'))
    key_6 = models.CharField(max_length=150, blank=True, verbose_name=_('key 6'))
    key_7 = models.CharField(max_length=150, blank=True, verbose_name=_('key 7'))
    key_8 = models.CharField(max_length=150, blank=True, verbose_name=_('key 8'))
    key_9 = models.CharField(max_length=150, blank=True, verbose_name=_('key 9'))
    
    # RATING: rating low/high
    rating_laps = models.PositiveIntegerField(
        default=0,
        verbose_name=_('rating low'),
        help_text=_('Minimum rating value')
    )
    
    rating_high = models.PositiveIntegerField(
        default=0,
        verbose_name=_('rating high'),
        help_text=_('Maximum rating value')
    )
    
    # CAPTURE_DIGITS: min/max digits, timeout
    number_digits = models.PositiveIntegerField(
        default=1,
        verbose_name=_('number of digits'),
        help_text=_('Expected number of digits to capture')
    )
    
    min_number_digits = models.PositiveIntegerField(
        default=1,
        verbose_name=_('min number of digits')
    )
    
    max_number_digits = models.PositiveIntegerField(
        default=10,
        verbose_name=_('max number of digits')
    )
    
    timeout = models.PositiveIntegerField(
        default=5,
        verbose_name=_('timeout'),
        help_text=_('Seconds to wait for input')
    )
    
    # RECORD_MESSAGE: max recording time
    max_record_time = models.PositiveIntegerField(
        default=30,
        verbose_name=_('max record time'),
        help_text=_('Maximum recording duration in seconds')
    )
    
    # CALL_TRANSFER: phone number, dial timeout
    phonenumber = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('phone number'),
        help_text=_('Number to transfer call to')
    )
    
    dial_timeout = models.PositiveIntegerField(
        default=30,
        verbose_name=_('dial timeout'),
        help_text=_('Seconds to wait for transfer answer')
    )
    
    # CONFERENCE: conference number
    conference_number = models.CharField(
        max_length=80,
        blank=True,
        verbose_name=_('conference number')
    )
    
    # SMS: message, gateway
    sms_text = models.TextField(
        blank=True,
        verbose_name=_('SMS text'),
        help_text=_('SMS message to send')
    )
    
    sms_gateway = models.ForeignKey(
        'mod_sms.SmsGateway',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_sections',
        verbose_name=_('SMS gateway')
    )
    
    # Retries
    retries = models.PositiveIntegerField(
        default=0,
        verbose_name=_('retries'),
        help_text=_('Number of retry attempts for invalid input')
    )
    
    # Validations
    validate_number = models.BooleanField(
        default=False,
        verbose_name=_('validate as number')
    )
    
    # Audio for invalid input
    invalid_audiofile = models.ForeignKey(
        'audiofield.AudioFile',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invalid_for_sections',
        verbose_name=_('invalid input audio')
    )
    
    class Meta:
        db_table = 'survey_section'
        verbose_name = _('survey section')
        verbose_name_plural = _('survey sections')
        ordering = ['survey', 'order']
        unique_together = [['survey', 'order']]
    
    def __str__(self):
        return f"{self.name} ({self.get_section_type_display()})"


class SurveyBranch(TimeStampedModel):
    """
    Survey Branch - defines transitions between sections.
    Based on DTMF key pressed or other conditions.
    """
    section = models.ForeignKey(
        SurveySection,
        on_delete=models.CASCADE,
        related_name='branches',
        verbose_name=_('from section')
    )
    
    # Condition: which key/value triggers this branch
    key_value = models.CharField(
        max_length=10,
        verbose_name=_('key value'),
        help_text=_('DTMF key or condition value (0-9, *, #, any, timeout)')
    )
    
    # Target section
    goto_section = models.ForeignKey(
        SurveySection,
        on_delete=models.CASCADE,
        related_name='incoming_branches',
        verbose_name=_('goto section'),
        help_text=_('Section to jump to when condition matches')
    )
    
    class Meta:
        db_table = 'survey_branch'
        verbose_name = _('survey branch')
        verbose_name_plural = _('survey branches')
        unique_together = [['section', 'key_value']]
    
    def __str__(self):
        return f"{self.section.name} [{self.key_value}] → {self.goto_section.name}"


class SurveyResponse(TimeStampedModel):
    """
    Survey Response - stores responses from completed surveys.
    One record per call/survey instance.
    """
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        verbose_name=_('survey')
    )
    
    callrequest = models.ForeignKey(
        'dialer_cdr.Callrequest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='survey_responses',
        verbose_name=_('call request')
    )
    
    # Response data (JSON)
    response_data = models.JSONField(
        default=dict,
        verbose_name=_('response data'),
        help_text=_('JSON object containing all section responses')
    )
    
    # Completion
    completed = models.BooleanField(
        default=False,
        verbose_name=_('completed')
    )
    
    class Meta:
        db_table = 'survey_response'
        verbose_name = _('survey response')
        verbose_name_plural = _('survey responses')
        ordering = ['-created_date']
    
    def __str__(self):
        return f"{self.survey.name} - {self.created_date}"
