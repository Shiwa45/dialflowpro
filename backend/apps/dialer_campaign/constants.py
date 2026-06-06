"""
Constants for dialer_campaign.
Mirrors original CAMPAIGN_STATUS, SUBSCRIBER_STATUS, AMD_BEHAVIOR enums.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class CampaignStatus(models.IntegerChoices):
    """Campaign status - mirrors original CAMPAIGN_STATUS"""
    PAUSE = 1, _('Pause')
    ABORT = 2, _('Abort')
    START = 3, _('Start')
    END = 4, _('End')
    PENDING = 5, _('Pending')


class SubscriberStatus(models.IntegerChoices):
    """Subscriber status - mirrors original SUBSCRIBER_STATUS"""
    PENDING = 1, _('Pending')
    PAUSE = 2, _('Pause')
    ABORT = 3, _('Abort')
    FAIL = 4, _('Fail')
    SENT = 5, _('Sent')
    IN_PROCESS = 6, _('In Process')
    NOT_AUTHORIZED = 7, _('Not Authorized')
    COMPLETED = 8, _('Completed')


class DialMode(models.IntegerChoices):
    """How the campaign initiates calls and routes them to agents"""
    PREDICTIVE  = 1, _('Predictive')
    PREVIEW     = 2, _('Preview')
    PROGRESSIVE = 3, _('Progressive')
    MANUAL      = 4, _('Manual')


class AmdBehavior(models.IntegerChoices):
    """AMD (Answering Machine Detection) behavior"""
    DISABLE = 0, _('Disable')
    ALWAYS_PLAY = 1, _('Always Play Message')
    ONLY_HUMAN = 2, _('Play Only to Human')
    ONLY_MACHINE = 3, _('Play Only to Machine')
