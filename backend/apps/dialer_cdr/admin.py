"""Django admin for Callrequest and VoIPCall"""
from django.contrib import admin
from .models import Callrequest, VoIPCall


@admin.register(Callrequest)
class CallrequestAdmin(admin.ModelAdmin):
    list_display = ['request_uuid', 'phone_number', 'status', 'campaign', 'num_attempt', 'created_date']
    list_filter = ['status', 'call_type', 'completed', 'created_date']
    search_fields = ['request_uuid', 'phone_number', 'campaign__name']
    readonly_fields = ['request_uuid', 'created_date', 'updated_date']
    raw_id_fields = ['user', 'campaign', 'subscriber', 'aleg_gateway']


@admin.register(VoIPCall)
class VoIPCallAdmin(admin.ModelAdmin):
    list_display = ['callid', 'phone_number', 'disposition', 'duration', 'billsec', 'starting_date']
    list_filter = ['disposition', 'amd_status', 'leg_type', 'starting_date']
    search_fields = ['callid', 'phone_number']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['user', 'callrequest']
