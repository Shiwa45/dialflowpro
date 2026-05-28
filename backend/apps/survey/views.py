"""Views for Survey management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Count
from .models import Survey, SurveySection, SurveyBranch, SurveyResponse
from .serializers import (
    SurveySerializer, SurveyListSerializer,
    SurveySectionSerializer, SurveyBranchSerializer,
    SurveyResponseSerializer
)
from .constants import SurveyStatus


class SurveyViewSet(viewsets.ModelViewSet):
    """ViewSet for Survey CRUD and actions"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return Survey.objects.filter(
            user__tenant=user.tenant
        ).annotate(section_count=Count('sections'))
    
    def get_serializer_class(self):
        """Use list serializer for list action"""
        if self.action == 'list':
            return SurveyListSerializer
        return SurveySerializer
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def seal(self, request, pk=None):
        """Seal survey - lock from editing"""
        survey = self.get_object()
        if survey.is_sealed():
            return Response(
                {'error': 'Survey already sealed'},
                status=status.HTTP_400_BAD_REQUEST
            )
        survey.seal()
        return Response({'status': 'sealed'})
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def get_survey_data(self, request, pk=None):
        """
        Get survey data for FreeSWITCH Lua script.
        Public endpoint called from Lua.
        Returns simplified JSON for IVR execution.
        """
        survey = self.get_object()
        
        # Build simplified structure for Lua
        sections_data = []
        for section in survey.sections.all().prefetch_related('branches'):
            section_data = {
                'id': section.id,
                'type': section.section_type,
                'name': section.name,
                'audio_url': section.audiofile.audio_file.url if section.audiofile else None,
                'branches': [
                    {'key': b.key_value, 'goto': b.goto_section_id}
                    for b in section.branches.all()
                ]
            }
            
            # Add type-specific fields
            if section.section_type == 2:  # MULTI_CHOICE
                section_data['keys'] = {
                    str(i): getattr(section, f'key_{i}')
                    for i in range(10)
                    if getattr(section, f'key_{i}')
                }
            elif section.section_type == 4:  # CAPTURE_DIGITS
                section_data['min_digits'] = section.min_number_digits
                section_data['max_digits'] = section.max_number_digits
                section_data['timeout'] = section.timeout
            elif section.section_type == 5:  # RECORD_MESSAGE
                section_data['max_time'] = section.max_record_time
            elif section.section_type == 6:  # CALL_TRANSFER
                section_data['number'] = section.phonenumber
                section_data['dial_timeout'] = section.dial_timeout
            
            sections_data.append(section_data)
        
        return Response({
            'survey_id': survey.id,
            'name': survey.name,
            'entry_section': survey.entry_section_id,
            'sections': sections_data
        })


class SurveySectionViewSet(viewsets.ModelViewSet):
    """ViewSet for SurveySection"""
    serializer_class = SurveySectionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant via survey"""
        user = self.request.user
        return SurveySection.objects.filter(
            survey__user__tenant=user.tenant
        ).select_related('survey', 'audiofile')


class SurveyBranchViewSet(viewsets.ModelViewSet):
    """ViewSet for SurveyBranch"""
    serializer_class = SurveyBranchSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant via section"""
        user = self.request.user
        return SurveyBranch.objects.filter(
            section__survey__user__tenant=user.tenant
        )


class SurveyResponseViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SurveyResponse (read-only)"""
    serializer_class = SurveyResponseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return SurveyResponse.objects.filter(
            survey__user__tenant=user.tenant
        ).select_related('survey', 'callrequest')
