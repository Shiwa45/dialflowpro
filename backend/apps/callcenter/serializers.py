"""Serializers for call center"""
from rest_framework import serializers
from .models import Queue, Agent, Tier, QueueMember


class QueueSerializer(serializers.ModelSerializer):
    """Serializer for Queue"""
    strategy_display = serializers.CharField(source='get_strategy_display', read_only=True)
    agent_count = serializers.IntegerField(read_only=True)
    active_calls = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Queue
        fields = [
            'id', 'name', 'description', 'strategy', 'strategy_display',
            'moh_sound', 'time_base_score', 'tier_rules_apply',
            'tier_rule_wait_second', 'tier_rule_wait_multiply_level',
            'tier_rule_no_agent_no_wait', 'max_wait_time',
            'max_wait_time_with_no_agent', 'discard_abandoned_after',
            'ring_progressively_delay', 'user', 'agent_count', 'active_calls',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'user', 'created_date', 'updated_date']


class AgentSerializer(serializers.ModelSerializer):
    """Serializer for Agent"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    state_display = serializers.CharField(source='get_state_display', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = Agent
        fields = [
            'id', 'name', 'user', 'username', 'status', 'status_display',
            'state', 'state_display', 'contact',
            'sip_extension', 'sip_password',
            'no_answer_delay_time', 'max_no_answer',
            'wrap_up_time', 'reject_delay_time', 'busy_delay_time',
            'last_bridge_start', 'last_bridge_end',
            'talk_time', 'calls_answered', 'last_status_change',
            'created_date', 'updated_date'
        ]
        read_only_fields = [
            'id', 'last_bridge_start', 'last_bridge_end', 'talk_time',
            'calls_answered', 'last_status_change', 'created_date', 'updated_date'
        ]
        extra_kwargs = {'sip_password': {'write_only': True}}


class TierSerializer(serializers.ModelSerializer):
    """Serializer for Tier"""
    queue_name = serializers.CharField(source='queue.name', read_only=True)
    agent_name = serializers.CharField(source='agent.name', read_only=True)
    level_display = serializers.CharField(source='get_level_display', read_only=True)
    position_display = serializers.CharField(source='get_position_display', read_only=True)
    
    class Meta:
        model = Tier
        fields = [
            'id', 'queue', 'queue_name', 'agent', 'agent_name',
            'level', 'level_display', 'position', 'position_display',
            'created_date'
        ]


class QueueMemberSerializer(serializers.ModelSerializer):
    """Serializer for QueueMember"""
    queue_name = serializers.CharField(source='queue.name', read_only=True)
    agent_name = serializers.CharField(source='serving_agent.name', read_only=True)
    wait_time = serializers.SerializerMethodField()
    
    class Meta:
        model = QueueMember
        fields = [
            'id', 'queue', 'queue_name', 'callrequest', 'session_uuid',
            'caller_number', 'caller_name', 'joined_epoch', 'serving_agent',
            'agent_name', 'serving_system', 'state', 'abandoned_epoch',
            'wait_time', 'created_date'
        ]
    
    def get_wait_time(self, obj):
        """Calculate wait time in seconds"""
        from django.utils import timezone
        import time
        if obj.abandoned_epoch:
            return obj.abandoned_epoch - obj.joined_epoch
        current_time = int(time.time())
        return current_time - obj.joined_epoch
