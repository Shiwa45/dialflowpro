"""Views for call center management"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.utils import timezone
from .models import Queue, Agent, Tier, QueueMember
from .serializers import (
    QueueSerializer, AgentSerializer,
    TierSerializer, QueueMemberSerializer
)
from .constants import AgentStatus


class QueueViewSet(viewsets.ModelViewSet):
    """ViewSet for Queue CRUD"""
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant, add counts"""
        user = self.request.user
        return Queue.objects.filter(
            user__tenant=user.tenant
        ).annotate(
            agent_count=Count('tiers', distinct=True),
            active_calls=Count('members', filter=Q(members__abandoned_epoch__isnull=True))
        )
    
    def perform_create(self, serializer):
        """Set user from request"""
        serializer.save(user=self.request.user)


class AgentViewSet(viewsets.ModelViewSet):
    """ViewSet for Agent CRUD and status updates"""
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant"""
        user = self.request.user
        return Agent.objects.filter(
            user__tenant=user.tenant
        ).select_related('user')
    
    @action(detail=True, methods=['post'])
    def set_available(self, request, pk=None):
        """Set agent status to available"""
        agent = self.get_object()
        agent.set_available()
        return Response({
            'status': 'available',
            'state': agent.state
        })
    
    @action(detail=True, methods=['post'])
    def set_on_break(self, request, pk=None):
        """Set agent on break"""
        agent = self.get_object()
        agent.set_on_break()
        return Response({'status': 'on_break'})
    
    @action(detail=True, methods=['post'])
    def set_logged_out(self, request, pk=None):
        """Log out agent"""
        agent = self.get_object()
        agent.set_logged_out()
        return Response({'status': 'logged_out'})
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available agents"""
        agents = self.get_queryset().filter(
            status=AgentStatus.AVAILABLE
        )
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get agent statistics"""
        agent = self.get_object()
        return Response({
            'agent_id': agent.id,
            'agent_name': agent.name,
            'total_calls': agent.calls_answered,
            'total_talk_time': agent.talk_time,
            'avg_talk_time': agent.talk_time / agent.calls_answered if agent.calls_answered > 0 else 0,
            'current_status': agent.get_status_display(),
            'last_call_start': agent.last_bridge_start,
            'last_call_end': agent.last_bridge_end
        })


class TierViewSet(viewsets.ModelViewSet):
    """ViewSet for Tier CRUD"""
    serializer_class = TierSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant via queue"""
        user = self.request.user
        return Tier.objects.filter(
            queue__user__tenant=user.tenant
        ).select_related('queue', 'agent')


class QueueMemberViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for QueueMember (read-only)"""
    serializer_class = QueueMemberSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter by user/tenant via queue"""
        user = self.request.user
        return QueueMember.objects.filter(
            queue__user__tenant=user.tenant
        ).select_related('queue', 'callrequest', 'serving_agent')
    
    @action(detail=False, methods=['get'])
    def waiting(self, request):
        """Get all calls waiting in queue"""
        members = self.get_queryset().filter(
            abandoned_epoch__isnull=True,
            serving_agent__isnull=True
        )
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)
