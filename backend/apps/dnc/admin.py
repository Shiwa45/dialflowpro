"""Django admin for DNC"""
from django.contrib import admin
from .models import DNC, DNCContact


@admin.register(DNC)
class DNCAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'created_date']
    list_filter = ['created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_date', 'updated_date']


@admin.register(DNCContact)
class DNCContactAdmin(admin.ModelAdmin):
    list_display = ['phone_number', 'dnc', 'created_date']
    list_filter = ['dnc', 'created_date']
    search_fields = ['phone_number']
    raw_id_fields = ['dnc']
