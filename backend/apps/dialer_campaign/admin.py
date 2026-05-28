"""Django admin for Campaign and Subscriber"""
from django.contrib import admin
from .models import Campaign, Subscriber


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['name', 'campaign_code', 'status', 'user', 'frequency', 'totalcontact', 'completed', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['name', 'campaign_code', 'user__username']
    readonly_fields = ['campaign_code', 'totalcontact', 'completed', 'created_date', 'updated_date']
    filter_horizontal = ['phonebook']
    
    fieldsets = (
        ('Basic Info', {'fields': ('campaign_code', 'name', 'description', 'status', 'user')}),
        ('Schedule', {'fields': ('startingdate', 'expirationdate', 'daily_start_time', 'daily_stop_time', 
                                 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday')}),
        ('Dialing', {'fields': ('frequency', 'calltimeout', 'callmaxduration', 'maxretry', 'intervalretry')}),
        ('Caller ID', {'fields': ('callerid', 'caller_name')}),
        ('Content', {'fields': ('phonebook', 'aleg_gateway', 'dnc')}),
        ('AMD', {'fields': ('voicemail', 'amd_behavior', 'voicemail_audiofile')}),
        ('Statistics', {'fields': ('totalcontact', 'completed')}),
    )


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['duplicate_contact', 'campaign', 'status', 'count_attempt', 'created_date']
    list_filter = ['status', 'created_date']
    search_fields = ['duplicate_contact', 'campaign__name']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['campaign', 'contact']
