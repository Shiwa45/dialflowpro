"""Serializers for Callrequest and VoIPCall"""
from rest_framework import serializers
from .models import Callrequest, VoIPCall


class CallrequestSerializer(serializers.ModelSerializer):
    """Serializer for Callrequest"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    call_type_display = serializers.CharField(source='get_call_type_display', read_only=True)
    campaign_name = serializers.CharField(source='campaign.name', read_only=True)
    
    class Meta:
        model = Callrequest
        fields = [
            'id', 'request_uuid', 'status', 'status_display', 
            'call_type', 'call_type_display', 'call_time', 'phone_number',
            'callerid', 'timeout', 'timelimit', 'num_attempt',
            'last_attempt_time', 'result', 'hangup_cause', 'completed',
            'user', 'campaign', 'campaign_name', 'subscriber',
            'aleg_gateway', 'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'request_uuid', 'created_date', 'updated_date']


class VoIPCallSerializer(serializers.ModelSerializer):
    """Serializer for VoIPCall CDR"""
    disposition_display = serializers.CharField(source='get_disposition_display', read_only=True)
    amd_status_display = serializers.CharField(source='get_amd_status_display', read_only=True)
    leg_type_display = serializers.CharField(source='get_leg_type_display', read_only=True)
    
    class Meta:
        model = VoIPCall
        fields = [
            'id', 'callid', 'callerid', 'phone_number',
            'starting_date', 'duration', 'billsec',
            'disposition', 'disposition_display', 'hangup_cause',
            'amd_status', 'amd_status_display', 'leg_type', 'leg_type_display',
            'user', 'callrequest', 'created_date'
        ]
        read_only_fields = ['id', 'created_date']
