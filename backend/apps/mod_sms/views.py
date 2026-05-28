"""Views for SMS management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import SmsGateway, SmsMessage, SmsCampaign
from .serializers import (
    SmsGatewaySerializer, SmsMessageSerializer, SmsCampaignSerializer
)
from .constants import SmsCampaignStatus


class SmsGatewayViewSet(viewsets.ModelViewSet):
    """ViewSet for SmsGateway CRUD"""
    serializer_class = SmsGatewaySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return SmsGateway.objects.filter(user__tenant=user.tenant)
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)


class SmsMessageViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for SmsMessage (read-only)"""
    serializer_class = SmsMessageSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return SmsMessage.objects.filter(
            user__tenant=user.tenant
        ).select_related('gateway', 'sms_campaign')


class SmsCampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for SmsCampaign CRUD and actions"""
    serializer_class = SmsCampaignSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return SmsCampaign.objects.filter(user__tenant=user.tenant)
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start SMS campaign"""
        campaign = self.get_object()
        campaign.status = SmsCampaignStatus.START
        campaign.save(update_fields=['status'])
        
        # TODO: Trigger Celery task to send SMS messages
        
        return Response({'status': 'started'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause SMS campaign"""
        campaign = self.get_object()
        campaign.status = SmsCampaignStatus.PAUSE
        campaign.save(update_fields=['status'])
        return Response({'status': 'paused'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop SMS campaign"""
        campaign = self.get_object()
        campaign.status = SmsCampaignStatus.END
        campaign.save(update_fields=['status'])
        return Response({'status': 'stopped'})
