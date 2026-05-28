"""
Serializers for Tenant management.
"""
from rest_framework import serializers
from .models import Tenant, Domain


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for Domain"""
    class Meta:
        model = Domain
        fields = ['id', 'domain', 'is_primary']


class TenantSerializer(serializers.ModelSerializer):
    """Serializer for Tenant"""
    domains = DomainSerializer(many=True, read_only=True)
    
    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'schema_name', 'is_active', 'plan',
            'contact_name', 'contact_email', 'contact_phone',
            'billing_email', 'domains', 'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'schema_name', 'created_date', 'updated_date']


class TenantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new tenant"""
    domain_url = serializers.CharField(write_only=True, help_text="Primary domain (e.g., tenant1.dialflow.com)")
    
    class Meta:
        model = Tenant
        fields = [
            'name', 'schema_name', 'plan',
            'contact_name', 'contact_email', 'contact_phone',
            'billing_email', 'domain_url'
        ]
    
    def create(self, validated_data):
        """Create tenant and primary domain"""
        domain_url = validated_data.pop('domain_url')
        
        # Create tenant
        tenant = Tenant.objects.create(**validated_data)
        
        # Create primary domain
        Domain.objects.create(
            domain=domain_url,
            tenant=tenant,
            is_primary=True
        )
        
        return tenant
