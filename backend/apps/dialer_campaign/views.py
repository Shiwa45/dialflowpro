"""Views for Campaign and Subscriber management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from .models import Campaign, Subscriber
from .serializers import (
    CampaignSerializer, CampaignListSerializer,
    CampaignDetailSerializer, SubscriberSerializer
)
from .constants import CampaignStatus
from .tasks import collect_subscriber


class CampaignViewSet(viewsets.ModelViewSet):
    """ViewSet for Campaign CRUD and actions"""
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status']
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return Campaign.objects.filter(
            user__tenant=user.tenant
        ).annotate(subscriber_count=Count('subscribers'))
    
    def get_serializer_class(self):
        """Use appropriate serializer"""
        if self.action == 'list':
            return CampaignListSerializer
        elif self.action == 'retrieve':
            return CampaignDetailSerializer
        return CampaignSerializer
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Start campaign"""
        campaign = self.get_object()
        campaign.status = CampaignStatus.START
        campaign.has_been_started = True
        campaign.save(update_fields=['status', 'has_been_started'])
        
        # Pass tenant schema so task runs in the correct DB schema
        tenant_schema = getattr(request.user.tenant, 'schema_name', '')
        collect_subscriber.delay(campaign.id, tenant_schema)

        return Response({'status': 'started', 'campaign': CampaignSerializer(campaign).data})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause campaign"""
        campaign = self.get_object()
        campaign.status = CampaignStatus.PAUSE
        campaign.save(update_fields=['status'])
        return Response({'status': 'paused'})
    
    @action(detail=True, methods=['post'])
    def stop(self, request, pk=None):
        """Stop/abort campaign"""
        campaign = self.get_object()
        campaign.status = CampaignStatus.ABORT
        campaign.save(update_fields=['status'])
        return Response({'status': 'stopped'})

    @action(detail=True, methods=['post'])
    def reset(self, request, pk=None):
        """
        Reset the campaign for re-dialing: all subscribers (FAIL/COMPLETED/
        IN_PROCESS) go back to PENDING and stuck CALLING callrequests are
        cleared. Useful for re-running a finished campaign or repeat testing.
        """
        from .models import Subscriber
        from .constants import SubscriberStatus
        from apps.dialer_cdr.models import Callrequest
        from apps.dialer_cdr.constants import CallrequestStatus

        campaign = self.get_object()
        subs = Subscriber.objects.filter(campaign=campaign).exclude(
            status=SubscriberStatus.PENDING
        ).update(status=SubscriberStatus.PENDING, count_attempt=0)
        crs = Callrequest.objects.filter(
            campaign=campaign, status=CallrequestStatus.CALLING
        ).update(status=CallrequestStatus.FAILURE)

        pending = Subscriber.objects.filter(
            campaign=campaign, status=SubscriberStatus.PENDING
        ).count()
        return Response({
            'status': 'reset',
            'subscribers_reset': subs,
            'calls_cleared': crs,
            'pending_now': pending,
        })


class SubscriberViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for Subscriber (read-only)"""
    serializer_class = SubscriberSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['campaign', 'status']
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return Subscriber.objects.filter(
            campaign__user__tenant=user.tenant
        ).select_related('campaign', 'contact')
