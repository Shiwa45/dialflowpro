"""Serializers for Survey, SurveySection, SurveyBranch"""
from rest_framework import serializers
from .models import Survey, SurveySection, SurveyBranch, SurveyResponse


class SurveyBranchSerializer(serializers.ModelSerializer):
    """Serializer for SurveyBranch"""
    goto_section_name = serializers.CharField(source='goto_section.name', read_only=True)
    
    class Meta:
        model = SurveyBranch
        fields = ['id', 'section', 'key_value', 'goto_section', 'goto_section_name']


class SurveySectionSerializer(serializers.ModelSerializer):
    """Serializer for SurveySection"""
    section_type_display = serializers.CharField(source='get_section_type_display', read_only=True)
    branches = SurveyBranchSerializer(many=True, read_only=True)
    
    class Meta:
        model = SurveySection
        fields = [
            'id', 'survey', 'section_type', 'section_type_display', 'name',
            'description', 'order', 'audiofile',
            # Multi-choice/Rating keys
            'key_0', 'key_1', 'key_2', 'key_3', 'key_4',
            'key_5', 'key_6', 'key_7', 'key_8', 'key_9',
            # Rating
            'rating_laps', 'rating_high',
            # Capture digits
            'number_digits', 'min_number_digits', 'max_number_digits', 'timeout',
            # Record
            'max_record_time',
            # Transfer
            'phonenumber', 'dial_timeout',
            # Conference
            'conference_number',
            # SMS
            'sms_text', 'sms_gateway',
            # Validation
            'retries', 'validate_number', 'invalid_audiofile',
            # Branches
            'branches'
        ]


class SurveyListSerializer(serializers.ModelSerializer):
    """List serializer for Survey"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    section_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'entry_section', 'section_count', 'campaign_count', 'created_date'
        ]


class SurveySerializer(serializers.ModelSerializer):
    """Full serializer for Survey"""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    sections = SurveySectionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Survey
        fields = [
            'id', 'name', 'description', 'status', 'status_display',
            'entry_section', 'user', 'campaign_count',
            'sections', 'created_date', 'updated_date'
        ]
        read_only_fields = ['id', 'user', 'campaign_count', 'created_date', 'updated_date']


class SurveyResponseSerializer(serializers.ModelSerializer):
    """Serializer for SurveyResponse"""
    survey_name = serializers.CharField(source='survey.name', read_only=True)
    
    class Meta:
        model = SurveyResponse
        fields = [
            'id', 'survey', 'survey_name', 'callrequest',
            'response_data', 'completed', 'created_date'
        ]
