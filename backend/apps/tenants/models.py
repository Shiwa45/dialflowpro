"""
Tenant models for multi-tenancy support.
Uses django-tenants for schema-based isolation.
"""
from django.db import models
from django_tenants.models import TenantMixin, DomainMixin


class Tenant(TenantMixin):
    """
    Tenant model - each organization gets its own PostgreSQL schema.
    Inherits from TenantMixin which provides schema_name field.
    """
    name = models.CharField(max_length=100)
    created_date = models.DateTimeField(auto_now_add=True)
    updated_date = models.DateTimeField(auto_now=True)
    
    # Subscription/Plan info
    is_active = models.BooleanField(default=True)
    plan = models.CharField(max_length=50, default='free')
    
    # Contact info
    contact_name = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(max_length=50, blank=True)
    
    # Billing
    billing_email = models.EmailField(blank=True)
    
    class Meta:
        db_table = 'tenants_tenant'
        verbose_name = 'Tenant'
        verbose_name_plural = 'Tenants'
    
    def __str__(self):
        return self.name


class Domain(DomainMixin):
    """
    Domain model - maps subdomains to tenants.
    tenant1.dialflow.com -> Tenant(schema_name='tenant1')
    """
    pass
