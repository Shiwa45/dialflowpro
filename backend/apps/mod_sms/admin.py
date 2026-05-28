"""Django admin for SMS"""
from django.contrib import admin
from .models import SmsGateway, SmsMessage, SmsCampaign


@admin.register(SmsGateway)
class SmsGatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'gateway_type', 'from_number', 'is_active', 'user']
    list_filter = ['gateway_type', 'is_active', 'created_date']
    search_fields = ['name', 'user__username']


@admin.register(SmsMessage)
class SmsMessageAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'sender', 'status', 'sent_date', 'sms_campaign']
    list_filter = ['status', 'created_date']
    search_fields = ['recipient', 'message']
    readonly_fields = ['gateway_message_id', 'sent_date', 'delivered_date', 'error']
    raw_id_fields = ['gateway', 'sms_campaign', 'user']


@admin.register(SmsCampaign)
class SmsCampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'total_sent', 'total_delivered', 'total_failed', 'user']
    list_filter = ['status', 'created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = ['total_sent', 'total_delivered', 'total_failed', 'created_date', 'updated_date']
