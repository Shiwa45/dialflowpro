"""
DNC (Do-Not-Call) models.
Manages numbers that should not be called.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import TimeStampedModel


class DNC(TimeStampedModel):
    """
    DNC List - container for do-not-call numbers.
    Can be imported from phonebooks or manually managed.
    """
    name = models.CharField(
        max_length=128,
        verbose_name=_('DNC list name')
    )
    
    description = models.TextField(
        blank=True,
        verbose_name=_('description')
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='dnc_lists',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'dnc'
        verbose_name = _('DNC list')
        verbose_name_plural = _('DNC lists')
        ordering = ['name']
    
    def __str__(self):
        return self.name


class DNCContact(TimeStampedModel):
    """
    Individual phone number in DNC list.
    Numbers in this list will not be called by campaigns.
    """
    dnc = models.ForeignKey(
        DNC,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('DNC list')
    )
    
    phone_number = PhoneNumberField(
        verbose_name=_('phone number'),
        help_text=_('Phone number to exclude from calling')
    )
    
    class Meta:
        db_table = 'dnc_contact'
        verbose_name = _('DNC contact')
        verbose_name_plural = _('DNC contacts')
        unique_together = [['dnc', 'phone_number']]
        indexes = [
            models.Index(fields=['phone_number']),
        ]
    
    def __str__(self):
        return str(self.phone_number)
