"""Constants for SMS app"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SmsGatewayType(models.IntegerChoices):
    """SMS gateway types"""
    TWILIO = 1, _('Twilio')
    PLIVO = 2, _('Plivo')
    CLICKATELL = 3, _('Clickatell')
    NEXMO = 4, _('Nexmo/Vonage')
    CUSTOM = 99, _('Custom HTTP')


class SmsStatus(models.IntegerChoices):
    """SMS delivery status"""
    PENDING = 1, _('Pending')
    SENT = 2, _('Sent')
    DELIVERED = 3, _('Delivered')
    FAILED = 4, _('Failed')
    UNSENT = 5, _('Unsent')


class SmsCampaignStatus(models.IntegerChoices):
    """SMS campaign status"""
    DRAFT = 1, _('Draft')
    PENDING = 2, _('Pending')
    START = 3, _('Started')
    PAUSE = 4, _('Paused')
    ABORT = 5, _('Aborted')
    END = 6, _('Ended')
