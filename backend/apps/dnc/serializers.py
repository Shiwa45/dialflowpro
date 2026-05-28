"""Serializers for DNC"""
from rest_framework import serializers
from .models import DNC, DNCContact


class DNCContactSerializer(serializers.ModelSerializer):
    """Serializer for DNCContact"""
    
    class Meta:
        model = DNCContact
        fields = ['id', 'dnc', 'phone_number', 'created_date']


class DNCSerializer(serializers.ModelSerializer):
    """Serializer for DNC"""
    contact_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = DNC
        fields = ['id', 'name', 'description', 'user', 'contact_count', 'created_date', 'updated_date']
        read_only_fields = ['id', 'user', 'created_date', 'updated_date']


class DNCImportSerializer(serializers.Serializer):
    """Serializer for importing contacts into DNC"""
    phonebook = serializers.IntegerField(help_text='Phonebook ID to import from')
