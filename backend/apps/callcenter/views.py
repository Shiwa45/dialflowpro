"""Views for call center management"""
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.conf import settings
from django.db.models import Count, Q, Avg, Sum
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Queue, Agent, Tier, QueueMember
from .serializers import (
    QueueSerializer, AgentSerializer,
    TierSerializer, QueueMemberSerializer
)
from .constants import AgentStatus, AgentState
from .services import route_call_to_queue

logger = logging.getLogger(__name__)


class QueueViewSet(viewsets.ModelViewSet):
    """ViewSet for Queue CRUD"""
    serializer_class = QueueSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Queue.objects.filter(
            user__tenant=user.tenant
        ).annotate(
            agent_count=Count('tiers', distinct=True),
            active_calls=Count(
                'members',
                filter=Q(members__abandoned_epoch__isnull=True),
            ),
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    @action(detail=True, methods=['get'])
    def stats(self, request, pk=None):
        """Get detailed queue statistics."""
        queue = self.get_object()
        waiting = QueueMember.objects.filter(
            queue=queue,
            abandoned_epoch__isnull=True,
            serving_agent__isnull=True,
        ).count()
        active = Tier.objects.filter(
            queue=queue,
            agent__status=AgentStatus.AVAILABLE,
        ).count()
        return Response({
            'queue_id': queue.id,
            'queue_name': queue.name,
            'waiting_calls': waiting,
            'active_agents': active,
        })


class AgentViewSet(viewsets.ModelViewSet):
    """ViewSet for Agent CRUD and status updates"""
    serializer_class = AgentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Agent.objects.filter(
            user__tenant=user.tenant
        ).select_related('user')

    # ────────────────────────────────────────────────────────
    #  /agents/me/  — the logged-in agent's own profile
    # ────────────────────────────────────────────────────────
    @action(detail=False, methods=['get'])
    def me(self, request):
        """
        Return the current user's agent profile + queues + today's stats.
        GET /api/callcenter/agents/me/
        """
        try:
            agent = Agent.objects.select_related('user').get(user=request.user)
        except Agent.DoesNotExist:
            return Response(
                {'detail': 'No agent profile linked to this user.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Queues the agent belongs to
        tiers = Tier.objects.filter(agent=agent).select_related('queue')
        queues = []
        for t in tiers:
            waiting = QueueMember.objects.filter(
                queue=t.queue,
                abandoned_epoch__isnull=True,
                serving_agent__isnull=True,
            ).count()
            queues.append({
                'id': t.queue.id,
                'name': t.queue.name,
                'strategy': t.queue.strategy,
                'strategy_display': t.queue.get_strategy_display(),
                'level': t.level,
                'position': t.position,
                'waiting_calls': waiting,
            })

        # Today's stats from CDR
        today_start = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        from apps.dialer_cdr.models import VoIPCall
        today_calls = VoIPCall.objects.filter(
            user=request.user,
            starting_date__gte=today_start,
        )
        today_stats = today_calls.aggregate(
            total_calls=Count('id'),
            total_duration=Sum('billsec'),
            avg_duration=Avg('billsec'),
        )

        return Response({
            'id': agent.id,
            'name': agent.name,
            'status': agent.status,
            'status_display': agent.get_status_display(),
            'state': agent.state,
            'sip_extension': agent.sip_extension,
            'calls_answered': agent.calls_answered,
            'talk_time': agent.talk_time,
            'wrap_up_time': agent.wrap_up_time,
            'max_no_answer': agent.max_no_answer,
            'last_bridge_start': agent.last_bridge_start,
            'last_bridge_end': agent.last_bridge_end,
            'queues': queues,
            'today': {
                'calls': today_stats['total_calls'] or 0,
                'duration': today_stats['total_duration'] or 0,
                'avg_duration': round(today_stats['avg_duration'] or 0, 1),
            },
            'user': {
                'id': agent.user.id,
                'username': agent.user.username,
                'first_name': agent.user.first_name,
                'last_name': agent.user.last_name,
                'email': agent.user.email,
            },
        })

    # ────────────────────────────────────────────────────────
    #  Status transitions (also broadcast via WS)
    # ────────────────────────────────────────────────────────
    def _broadcast_status(self, agent):
        """Push agent status change to WS channel layer."""
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)('agent_status', {
                'type': 'agent_status_update',
                'agent_id': agent.id,
                'agent_name': agent.name,
                'status': agent.status,
                'status_display': agent.get_status_display(),
                'state': agent.state,
                'calls_answered': agent.calls_answered,
                'talk_time': agent.talk_time,
                'timestamp': timezone.now().isoformat(),
            })
        except Exception:
            pass  # WS broadcast is best-effort

    @action(detail=True, methods=['post'])
    def set_available(self, request, pk=None):
        agent = self.get_object()
        agent.status = AgentStatus.AVAILABLE
        agent.state = AgentState.WAITING
        agent.save(update_fields=['status', 'state'])
        self._broadcast_status(agent)
        serializer = self.get_serializer(agent)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_on_break(self, request, pk=None):
        agent = self.get_object()
        agent.status = AgentStatus.ON_BREAK
        agent.save(update_fields=['status'])
        self._broadcast_status(agent)
        serializer = self.get_serializer(agent)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def set_logged_out(self, request, pk=None):
        agent = self.get_object()
        agent.status = AgentStatus.LOGGED_OUT
        agent.state = AgentState.WAITING
        agent.save(update_fields=['status', 'state'])
        self._broadcast_status(agent)
        serializer = self.get_serializer(agent)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def available(self, request):
        agents = self.get_queryset().filter(status=AgentStatus.AVAILABLE)
        serializer = self.get_serializer(agents, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        agent = self.get_object()
        return Response({
            'agent_id': agent.id,
            'agent_name': agent.name,
            'total_calls': agent.calls_answered,
            'total_talk_time': agent.talk_time,
            'avg_talk_time': (
                agent.talk_time / agent.calls_answered
                if agent.calls_answered > 0
                else 0
            ),
            'current_status': agent.get_status_display(),
            'last_call_start': agent.last_bridge_start,
            'last_call_end': agent.last_bridge_end,
        })


class TierViewSet(viewsets.ModelViewSet):
    serializer_class = TierSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Tier.objects.filter(
            queue__user__tenant=user.tenant
        ).select_related('queue', 'agent')
        queue_id = self.request.query_params.get('queue')
        if queue_id:
            qs = qs.filter(queue_id=queue_id)
        return qs


class QueueMemberViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = QueueMemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return QueueMember.objects.filter(
            queue__user__tenant=user.tenant
        ).select_related('queue', 'callrequest', 'serving_agent')

    @action(detail=False, methods=['get'])
    def waiting(self, request):
        members = self.get_queryset().filter(
            abandoned_epoch__isnull=True,
            serving_agent__isnull=True,
        )
        serializer = self.get_serializer(members, many=True)
        return Response(serializer.data)


# ── FreeSWITCH webhook ────────────────────────────────────────────────────────
@api_view(['POST'])
@permission_classes([AllowAny])
def route_call(request):
    """
    Called by the FreeSWITCH Lua script when a predictive-dialing call is
    answered by a human. Finds an available agent in the campaign's queue,
    sends them an `incoming_call` WS event, and returns their SIP extension
    so the Lua script can bridge the call.

    Auth: FS_SECRET value in POST body or X-FS-Secret header.
    """
    fs_secret = (
        request.data.get('fs_secret')
        or request.headers.get('X-Fs-Secret', '')
    )
    expected = getattr(settings, 'FS_SECRET', '')
    if expected and fs_secret != expected:
        return Response({'error': 'Unauthorized'}, status=403)

    call_id       = request.data.get('call_id', '')
    campaign_id   = request.data.get('campaign_id')
    caller_number = request.data.get('caller_number', '')
    tenant_id     = request.data.get('tenant_id')
    tenant_schema = request.data.get('tenant_schema', '')

    if not call_id or not campaign_id:
        return Response({'error': 'call_id and campaign_id are required'}, status=400)

    try:
        from apps.dialer_campaign.models import Campaign
        from django_tenants.utils import schema_context

        # Prefer explicit tenant_schema; fall back to lookup via tenant_id
        schema = tenant_schema or 'public'
        if not schema and tenant_id:
            try:
                from apps.tenants.models import Tenant
                tenant = Tenant.objects.get(id=tenant_id)
                schema = tenant.schema_name
            except Exception:
                pass

        with schema_context(schema):
            campaign = Campaign.objects.select_related('queue').get(id=campaign_id)

            if not campaign.queue:
                return Response(
                    {'available': False, 'error': 'Campaign has no queue assigned'},
                    status=400,
                )

            agent = route_call_to_queue(
                queue=campaign.queue,
                call_id=call_id,
                caller_number=caller_number,
                campaign_name=campaign.name,
            )

            if not agent:
                return Response({'available': False, 'error': 'No agents available'}, status=503)

            return Response({
                'available': True,
                'agent_id': agent.id,
                'agent_name': agent.name,
                'agent_extension': agent.sip_extension or '',
            })

    except Exception as exc:
        logger.exception(f'route_call error: {exc}')
        return Response({'error': str(exc)}, status=500)
