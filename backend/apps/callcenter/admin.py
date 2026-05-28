"""Django admin for call center"""
from django.contrib import admin
from .models import Queue, Agent, Tier, QueueMember


@admin.register(Queue)
class QueueAdmin(admin.ModelAdmin):
    list_display = ['name', 'strategy', 'user', 'created_date']
    list_filter = ['strategy', 'tier_rules_apply', 'created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_date', 'updated_date']


@admin.register(Agent)
class AgentAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'state', 'calls_answered', 'talk_time']
    list_filter = ['status', 'state', 'created_date']
    search_fields = ['name', 'user__username']
    readonly_fields = [
        'last_bridge_start', 'last_bridge_end', 'talk_time',
        'calls_answered', 'last_status_change', 'created_date', 'updated_date'
    ]


@admin.register(Tier)
class TierAdmin(admin.ModelAdmin):
    list_display = ['queue', 'agent', 'level', 'position']
    list_filter = ['level', 'queue']
    search_fields = ['queue__name', 'agent__name']
    raw_id_fields = ['queue', 'agent']


@admin.register(QueueMember)
class QueueMemberAdmin(admin.ModelAdmin):
    list_display = ['caller_number', 'queue', 'state', 'serving_agent', 'created_date']
    list_filter = ['state', 'queue', 'created_date']
    search_fields = ['caller_number', 'session_uuid']
    readonly_fields = ['created_date', 'updated_date']
    raw_id_fields = ['queue', 'callrequest', 'serving_agent']
