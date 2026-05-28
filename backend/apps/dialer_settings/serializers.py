"""
Serializers for DialerSetting.
"""
from rest_framework import serializers
from .models import DialerSetting


class DialerSettingSerializer(serializers.ModelSerializer):
    """Serializer for DialerSetting CRUD"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    class Meta:
        model = DialerSetting
        fields = [
            'id', 'name', 'tenant', 'tenant_name',
            # Voice limits
            'max_frequency', 'callmaxduration', 'maxretry', 'max_calltimeout',
            'max_cpg', 'max_subr_cpg', 'max_contact',
            # Filtering
            'blacklist', 'whitelist',
            # SMS limits
            'sms_max_frequency', 'sms_maxretry', 
            'sms_max_number_campaign', 'sms_max_number_subscriber_campaign',
            # Timestamps
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'tenant', 'created_date', 'updated_date']


class DialerSettingDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with usage statistics"""
    tenant_name = serializers.CharField(source='tenant.name', read_only=True)
    
    # Usage stats (to be calculated in view)
    current_campaigns = serializers.IntegerField(read_only=True, default=0)
    current_contacts = serializers.IntegerField(read_only=True, default=0)
    
    class Meta:
        model = DialerSetting
        fields = '__all__'
