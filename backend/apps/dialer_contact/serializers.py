"""
Serializers for Contact and Phonebook.
"""
from rest_framework import serializers
from .models import Phonebook, Contact
from .constants import ContactStatus


class PhonebookSerializer(serializers.ModelSerializer):
    """Serializer for Phonebook CRUD"""
    contact_count = serializers.SerializerMethodField()
    active_contacts = serializers.SerializerMethodField()
    user_username = serializers.CharField(source='user.username', read_only=True)

    def get_contact_count(self, obj):
        return obj.contacts.count()

    def get_active_contacts(self, obj):
        return obj.contacts.filter(status=ContactStatus.ACTIVE).count()

    class Meta:
        model = Phonebook
        fields = [
            'id', 'name', 'description', 'user', 'user_username',
            'contact_count', 'active_contacts',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'user', 'created_date', 'updated_date']


class ContactSerializer(serializers.ModelSerializer):
    """Serializer for Contact CRUD"""
    phonebook_name = serializers.CharField(
        source='phonebook.name',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'phonebook', 'phonebook_name', 'contact',
            'status', 'status_display',
            'last_name', 'first_name', 'full_name', 'email',
            'unit_number', 'address', 'city', 'state', 'country',
            'description', 'additional_vars',
            'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'created_date', 'updated_date']


class ContactListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for contact listings"""
    phonebook_name = serializers.CharField(source='phonebook.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = Contact
        fields = [
            'id', 'phonebook', 'phonebook_name', 'contact',
            'first_name', 'last_name', 'email',
            'status', 'status_display', 'updated_date'
        ]


class ContactImportSerializer(serializers.Serializer):
    """Serializer for CSV contact import"""
    phonebook = serializers.PrimaryKeyRelatedField(
        queryset=Phonebook.objects.all()
    )
    csv_file = serializers.FileField()
    skip_duplicates = serializers.BooleanField(default=True)
    # ISO 3166-1 alpha-2 country code used as fallback region when numbers
    # have no + prefix (e.g. "PK" turns 03001234567 → +923001234567)
    country_code = serializers.CharField(
        max_length=2, default='', allow_blank=True, required=False
    )

    def validate_csv_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError('File must be a CSV')
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError('File size must be under 10MB')
        return value

    def validate_country_code(self, value):
        return value.upper().strip() if value else ''
