"""
Contact and Phonebook models.
Preserves all fields from original dialer_contact app.
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField
from phonenumber_field.modelfields import PhoneNumberField
from apps.common.models import TimeStampedModel
from .constants import ContactStatus


class Phonebook(TimeStampedModel):
    """
    Phonebook - collection of contacts.
    Each campaign can be linked to multiple phonebooks.
    
    Preserves original dialer_phonebook fields.
    """
    name = models.CharField(
        max_length=90,
        verbose_name=_('name'),
        help_text=_('Phonebook name')
    )
    
    description = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('description'),
        help_text=_('Phonebook notes')
    )
    
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='phonebooks',
        verbose_name=_('user')
    )
    
    class Meta:
        db_table = 'dialer_phonebook'
        verbose_name = _('phonebook')
        verbose_name_plural = _('phonebooks')
        ordering = ['-created_date']
    
    def __str__(self):
        return self.name
    
    @property
    def phonebook_contacts(self) -> int:
        return self.contacts.count()

    @property
    def active_contacts_count(self) -> int:
        return self.contacts.filter(status=ContactStatus.ACTIVE).count()


class Contact(TimeStampedModel):
    """
    Contact - individual phone number with metadata.
    Belongs to a phonebook, can be imported via CSV.
    
    Preserves all original dialer_contact fields.
    """
    phonebook = models.ForeignKey(
        Phonebook,
        on_delete=models.CASCADE,
        related_name='contacts',
        verbose_name=_('phonebook')
    )
    
    # Phone number (stored in E.164 format)
    contact = PhoneNumberField(
        verbose_name=_('contact number'),
        help_text=_('Phone number in E.164 format (e.g., +14155552671)')
    )
    
    status = models.IntegerField(
        choices=ContactStatus.choices,
        default=ContactStatus.ACTIVE,
        db_index=True,
        verbose_name=_('status')
    )
    
    # Personal info
    last_name = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('last name')
    )
    
    first_name = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('first name')
    )
    
    email = models.EmailField(
        blank=True,
        verbose_name=_('email')
    )
    
    # Address fields
    unit_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('unit number')
    )
    
    address = models.CharField(
        max_length=250,
        blank=True,
        verbose_name=_('address')
    )
    
    city = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('city')
    )
    
    state = models.CharField(
        max_length=120,
        blank=True,
        verbose_name=_('state/province')
    )
    
    country = CountryField(
        blank=True,
        null=True,
        verbose_name=_('country')
    )
    
    # Additional data
    description = models.TextField(
        blank=True,
        verbose_name=_('description'),
        help_text=_('Notes about this contact')
    )
    
    additional_vars = models.JSONField(
        blank=True,
        null=True,
        verbose_name=_('additional variables'),
        help_text=_('Additional contact data in JSON format')
    )
    
    class Meta:
        db_table = 'dialer_contact'
        verbose_name = _('contact')
        verbose_name_plural = _('contacts')
        ordering = ['-created_date']
        indexes = [
            models.Index(fields=['contact', 'status']),
            models.Index(fields=['phonebook', 'status']),
        ]
    
    def __str__(self):
        if self.first_name or self.last_name:
            return f"{self.first_name} {self.last_name} ({self.contact})"
        return str(self.contact)
    
    @property
    def full_name(self) -> str:
        """Return full name or empty string"""
        parts = [self.first_name, self.last_name]
        return ' '.join(p for p in parts if p).strip()
    
    def is_active(self) -> bool:
        """Check if contact is active"""
        return self.status == ContactStatus.ACTIVE
