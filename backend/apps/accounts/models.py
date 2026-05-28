"""
User and authentication models.
Custom User model with role-based access control.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.common.models import TimeStampedModel


class UserRole(models.IntegerChoices):
    """User role types - mirrors original MANAGER/STAFF/AGENT roles"""
    SUPERADMIN = 1, _('Super Administrator')
    MANAGER = 2, _('Manager')
    AGENT = 3, _('Agent')
    CALENDAR_USER = 4, _('Calendar User')


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Adds role-based access and tenant relationship.
    """
    role = models.IntegerField(
        choices=UserRole.choices,
        default=UserRole.MANAGER,
        help_text=_('User role in the system')
    )
    
    # Tenant relationship (null for superadmins in public schema)
    tenant = models.ForeignKey(
        'tenants.Tenant',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='users',
        help_text=_('Tenant this user belongs to')
    )
    
    # Additional fields
    phone = models.CharField(max_length=50, blank=True)
    company = models.CharField(max_length=100, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=50, blank=True)
    country = models.CharField(max_length=50, blank=True)
    zip_code = models.CharField(max_length=20, blank=True)
    
    # Timestamps (inherited fields from AbstractUser don't have auto_now)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'auth_user'
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_superadmin(self) -> bool:
        """Check if user is a superadmin"""
        return self.role == UserRole.SUPERADMIN
    
    @property
    def is_manager(self) -> bool:
        """Check if user is a manager"""
        return self.role == UserRole.MANAGER
    
    @property
    def is_agent(self) -> bool:
        """Check if user is an agent"""
        return self.role == UserRole.AGENT
    
    @property
    def full_name(self) -> str:
        """Return full name or username"""
        return self.get_full_name() or self.username


class UserProfile(TimeStampedModel):
    """
    Extended user profile with dialer-specific settings.
    Links user to their DialerSetting configuration.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        primary_key=True
    )
    
    # Dialer settings reference
    dialersetting = models.ForeignKey(
        'dialer_settings.DialerSetting',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='user_profiles',
        help_text=_('Dialer limits and settings for this user')
    )
    
    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    sms_notifications = models.BooleanField(default=False)
    
    # UI preferences
    timezone = models.CharField(max_length=50, default='UTC')
    language = models.CharField(max_length=10, default='en')
    
    class Meta:
        db_table = 'user_profile'
        verbose_name = _('user profile')
        verbose_name_plural = _('user profiles')
    
    def __str__(self):
        return f"Profile: {self.user.username}"
