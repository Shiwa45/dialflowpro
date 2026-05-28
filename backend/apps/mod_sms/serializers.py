"""Serializers for SMS"""
from rest_framework import serializers
from .models import SmsGateway, SmsMessage, SmsCampaign


class SmsGatewaySerializer(serializers.ModelSerializer):
    """Serializer for SmsGateway"""
    gateway_type_display = serializers.CharField(source='get_gateway_type_display', read_only=True)
    
    class Meta:
        model = SmsGateway
        fields = [
            'id', 'name', 'gateway_type', 'gateway_type_display',
            'account_sid', 'auth_token', 'api_key', 'base_url',
            'from_number', 'from_name', 'is_active', 'user',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'user', 'created_date', 'updated_date']
        extra_kwargs = {
            'auth_token': {'write_only': True},
            'api_key': {'write_only': True}
        }


class SmsMessageSerializer(serializers.ModelSerializer):
    """Serializer for SmsMessage"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SmsMessage
        fields = [
            'id', 'recipient', 'sender', 'message', 'gateway',
            'status', 'status_display', 'gateway_message_id',
            'sent_date', 'delivered_date', 'error', 'sms_campaign',
            'user', 'created_date'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'gateway_message_id',
            'sent_date', 'delivered_date', 'error', 'created_date'
        ]


class SmsCampaignSerializer(serializers.ModelSerializer):
    """Serializer for SmsCampaign"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = SmsCampaign
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'message_text', 'gateway', 'phonebook', 'startingdate',
            'expirationdate', 'frequency', 'total_sent', 'total_delivered',
            'total_failed', 'user', 'created_date', 'updated_date'
        ]
        read_only_fields = [
            'id', 'user', 'total_sent', 'total_delivered', 'total_failed',
            'created_date', 'updated_date'
        ]
