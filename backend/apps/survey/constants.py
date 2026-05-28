"""
Constants for survey app.
Mirrors original 10 IVR section types from Newfies-Dialer.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SurveySectionType(models.IntegerChoices):
    """
    Survey section types - 10 IVR node types.
    Mirrors original SECTION_TYPE from survey app.
    """
    PLAY_MESSAGE = 1, _('Play Message')
    MULTI_CHOICE = 2, _('Multi-Choice')
    RATING_QUESTION = 3, _('Rating Question')
    CAPTURE_DIGITS = 4, _('Capture Digits')
    RECORD_MESSAGE = 5, _('Record Message')
    CALL_TRANSFER = 6, _('Call Transfer')
    HANGUP = 7, _('Hangup')
    CONFERENCE = 8, _('Conference')
    DNC = 9, _('DNC (Do Not Call)')
    SMS = 10, _('Send SMS')


class SurveyStatus(models.IntegerChoices):
    """Survey status"""
    DRAFT = 1, _('Draft')
    SEALED = 2, _('Sealed')
    ARCHIVED = 3, _('Archived')
