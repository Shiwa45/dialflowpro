"""Serializers for Campaign and Subscriber"""
from rest_framework import serializers
from .models import Campaign, Subscriber


class SubscriberSerializer(serializers.ModelSerializer):
    """Serializer for Subscriber"""
    contact_info = serializers.CharField(source='contact.__str__', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Subscriber
        fields = [
            'id', 'campaign', 'contact', 'contact_info', 'duplicate_contact',
            'status', 'status_display', 'count_attempt', 'last_attempt',
            'completion_count_attempt', 'last_completion_attempt',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'duplicate_contact', 'created_date', 'updated_date']


class CampaignListSerializer(serializers.ModelSerializer):
    """List serializer for Campaign"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dial_mode_display = serializers.CharField(source='get_dial_mode_display', read_only=True)
    queue_name = serializers.CharField(source='queue.name', read_only=True, default=None)
    subscriber_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Campaign
        fields = [
            'id', 'campaign_code', 'name', 'status', 'status_display',
            'dial_mode', 'dial_mode_display', 'queue', 'queue_name',
            'startingdate', 'expirationdate', 'frequency', 'totalcontact',
            'completed', 'subscriber_count', 'created_date'
        ]


class CampaignSerializer(serializers.ModelSerializer):
    """Full serializer for Campaign create/update"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    dial_mode_display = serializers.CharField(source='get_dial_mode_display', read_only=True)
    queue_name = serializers.CharField(source='queue.name', read_only=True, default=None)

    class Meta:
        model = Campaign
        fields = [
            'id', 'campaign_code', 'name', 'description',
            'status', 'status_display', 'callerid', 'caller_name',
            'dial_mode', 'dial_mode_display', 'queue', 'queue_name',
            'ai_agent', 'ai_max_concurrent',
            'startingdate', 'expirationdate', 'daily_start_time', 'daily_stop_time',
            'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
            'frequency', 'lines_per_agent', 'allow_duplicate_contacts', 'calltimeout', 'callmaxduration', 'maxretry', 'intervalretry',
            'completion_maxretry', 'completion_intervalretry',
            'user', 'phonebook', 'aleg_gateway', 'dnc',
            'voicemail', 'amd_behavior', 'voicemail_audiofile',
            'totalcontact', 'completed', 'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'campaign_code', 'user', 'totalcontact', 'completed', 'created_date', 'updated_date']


class CampaignDetailSerializer(CampaignSerializer):
    """Detailed serializer with subscribers"""
    subscribers = SubscriberSerializer(many=True, read_only=True)
    phonebook_names = serializers.SerializerMethodField()
    
    def get_phonebook_names(self, obj):
        return [pb.name for pb in obj.phonebook.all()]
    
    class Meta(CampaignSerializer.Meta):
        fields = CampaignSerializer.Meta.fields + ['subscribers', 'phonebook_names']
