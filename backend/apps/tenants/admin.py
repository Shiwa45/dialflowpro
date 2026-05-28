"""
Django admin for Tenant and Domain.
"""
from django.contrib import admin
from django_tenants.admin import TenantAdminMixin
from .models import Tenant, Domain


@admin.register(Tenant)
class TenantAdmin(TenantAdminMixin, admin.ModelAdmin):
    """Admin interface for Tenant"""
    list_display = ['name', 'schema_name', 'plan', 'is_active', 'created_date']
    list_filter = ['is_active', 'plan', 'created_date']
    search_fields = ['name', 'schema_name', 'contact_email']
    readonly_fields = ['created_date', 'updated_date']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'schema_name', 'is_active', 'plan')
        }),
        ('Contact Information', {
            'fields': ('contact_name', 'contact_email', 'contact_phone')
        }),
        ('Billing', {
            'fields': ('billing_email',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    """Admin interface for Domain"""
    list_display = ['domain', 'tenant', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['domain', 'tenant__name']
