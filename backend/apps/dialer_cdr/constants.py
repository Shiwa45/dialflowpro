"""
Constants for dialer_cdr app.
Mirrors original callrequest and voipcall status enums.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class CallrequestStatus(models.IntegerChoices):
    """Callrequest status - mirrors original CALLREQUEST_STATUS"""
    PENDING = 1, _('Pending')
    FAILURE = 2, _('Failure')
    RETRY = 3, _('Retry')
    SUCCESS = 4, _('Success')
    ABORT = 5, _('Abort')
    PAUSE = 6, _('Pause')
    IN_PROCESS = 7, _('In Process')
    CALLING = 8, _('Calling')


class CallrequestType(models.IntegerChoices):
    """Callrequest type - retry allowed or not"""
    ALLOW_RETRY = 1, _('Allow Retry')
    CANNOT_RETRY = 2, _('Cannot Retry')


class LegType(models.IntegerChoices):
    """Call leg type"""
    A_LEG = 1, _('A-Leg')
    B_LEG = 2, _('B-Leg')


class CallDisposition(models.TextChoices):
    """Call disposition - FreeSWITCH hangup causes"""
    ANSWER = 'ANSWER', _('Answer')
    BUSY = 'BUSY', _('Busy')
    NOANSWER = 'NOANSWER', _('No Answer')
    CANCEL = 'CANCEL', _('Cancel')
    CONGESTION = 'CONGESTION', _('Congestion')
    CHANUNAVAIL = 'CHANUNAVAIL', _('Channel Unavailable')
    DONTCALL = 'DONTCALL', _('Do Not Call')
    TORTURE = 'TORTURE', _('Torture')
    INVALIDARGS = 'INVALIDARGS', _('Invalid Arguments')
    NORMAL_CLEARING = 'NORMAL_CLEARING', _('Normal Clearing')
    ORIGINATOR_CANCEL = 'ORIGINATOR_CANCEL', _('Originator Cancel')
    NORMAL_TEMPORARY_FAILURE = 'NORMAL_TEMPORARY_FAILURE', _('Temporary Failure')
    INVALID_GATEWAY = 'INVALID_GATEWAY', _('Invalid Gateway')


class AmdStatus(models.IntegerChoices):
    """AMD (Answering Machine Detection) status"""
    PERSON = 1, _('Person')
    MACHINE = 2, _('Machine')
    NOTSURE = 3, _('Not Sure')
