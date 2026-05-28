"""
Constants for dialer_contact app.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class ContactStatus(models.IntegerChoices):
    """Contact status - mirrors original CONTACT_STATUS"""
    ACTIVE = 1, _('Active')
    INACTIVE = 2, _('Inactive')
