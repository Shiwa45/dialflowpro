"""Serializers for Gateway"""
from rest_framework import serializers
from .models import Gateway


class GatewaySerializer(serializers.ModelSerializer):
    """Serializer for Gateway"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    fs_dial_string_prefix = serializers.CharField(read_only=True)

    class Meta:
        model = Gateway
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            # SIP / FreeSWITCH connection
            'sip_host', 'sip_port', 'register', 'sip_username', 'sip_password',
            'caller_id_in_from',
            # Dial string (auto-set to sofia/gateway/<name>/ if blank)
            'gateways', 'fs_dial_string_prefix',
            # Advanced
            'gateway_codecs', 'gateway_timeouts', 'gateway_retries',
            'originate_dial_string', 'addparameter',
            'addprefix', 'removeprefix',
            'maximum_call', 'failover',
            'secondused', 'count_call',
            'created_date', 'updated_date',
        ]
        read_only_fields = [
            'id', 'fs_dial_string_prefix',
            'secondused', 'count_call',
            'created_date', 'updated_date',
        ]
        extra_kwargs = {
            'sip_password': {'write_only': True},
            'gateways': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        # Auto-fill gateways dial string from name if left blank
        name = attrs.get('name') or (self.instance.name if self.instance else '')
        if not attrs.get('gateways') and name:
            attrs['gateways'] = f'sofia/gateway/{name}/'
        return attrs
