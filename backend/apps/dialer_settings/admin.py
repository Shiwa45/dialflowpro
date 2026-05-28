"""
Django admin for DialerSetting.
"""
from django.contrib import admin
from .models import DialerSetting


@admin.register(DialerSetting)
class DialerSettingAdmin(admin.ModelAdmin):
    """Admin interface for DialerSetting"""
    list_display = [
        'name', 'tenant', 'max_frequency', 'maxretry', 
        'max_cpg', 'max_contact', 'created_date'
    ]
    list_filter = ['created_date']
    search_fields = ['name', 'tenant__name']
    readonly_fields = ['created_date', 'updated_date']
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'tenant')
        }),
        ('Voice Campaign Limits', {
            'fields': (
                'max_frequency', 'callmaxduration', 'maxretry',
                'max_calltimeout', 'max_cpg', 'max_subr_cpg', 'max_contact'
            )
        }),
        ('Number Filtering', {
            'fields': ('whitelist', 'blacklist'),
            'classes': ('collapse',)
        }),
        ('SMS Limits', {
            'fields': (
                'sms_max_frequency', 'sms_maxretry',
                'sms_max_number_campaign', 'sms_max_number_subscriber_campaign'
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_date', 'updated_date'),
            'classes': ('collapse',)
        }),
    )
