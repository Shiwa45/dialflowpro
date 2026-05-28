"""Django admin for Gateway"""
from django.contrib import admin
from .models import Gateway


@admin.register(Gateway)
class GatewayAdmin(admin.ModelAdmin):
    list_display = ['name', 'status', 'count_call', 'count_in_use', 'maximum_call', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['name', 'gateways']
    readonly_fields = ['secondused', 'count_call', 'count_in_use', 'created_date', 'updated_date']
    raw_id_fields = ['failover']
