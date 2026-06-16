"""Views for the AI Agent app."""
import logging

from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    AISubscription, AIAgent, AIKnowledgeItem, AICallSession, AICallback,
)
from .serializers import (
    AISubscriptionSerializer, AIAgentSerializer, AIKnowledgeItemSerializer,
    AICallSessionSerializer, AICallSessionListSerializer, AICallbackSerializer,
)
from .permissions import HasActiveAISubscription, IsTenantAdminForAI, get_subscription
from .constants import AIAgentStatus

logger = logging.getLogger(__name__)


class AISubscriptionView(viewsets.ViewSet):
    """Read-only view of the tenant's AI subscription + usage."""
    permission_classes = [IsAuthenticated]

    def list(self, request):
        sub = get_subscription(request)
        if not sub:
            return Response(
                {"is_active": False, "detail": "No AI subscription for this tenant."},
                status=status.HTTP_200_OK,
            )
        return Response(AISubscriptionSerializer(sub).data)


class AIAgentViewSet(viewsets.ModelViewSet):
    serializer_class = AIAgentSerializer
    permission_classes = [IsAuthenticated, HasActiveAISubscription, IsTenantAdminForAI]

    def get_queryset(self):
        return AIAgent.objects.filter(
            user__tenant=self.request.user.tenant
        ).select_related("transfer_queue")

    def perform_create(self, serializer):
        sub = get_subscription(self.request)
        existing = AIAgent.objects.filter(user__tenant=self.request.user.tenant).count()
        if sub and existing >= sub.max_agents:
            from rest_framework.exceptions import ValidationError
            raise ValidationError(
                f"Your plan allows {sub.max_agents} AI agent(s). "
                f"Upgrade to add more."
            )
        serializer.save(user=self.request.user)

    @action(detail=True, methods=["post"])
    def activate(self, request, pk=None):
        agent = self.get_object()
        if agent.kb_chunk_count == 0 and not agent.knowledge_items.filter(is_active=True).exists():
            return Response(
                {"error": "Add at least one knowledge item before activating."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        agent.status = AIAgentStatus.ACTIVE
        agent.save(update_fields=["status", "updated_date"])
        return Response({"status": "active"})

    @action(detail=True, methods=["post"])
    def pause(self, request, pk=None):
        agent = self.get_object()
        agent.status = AIAgentStatus.PAUSED
        agent.save(update_fields=["status", "updated_date"])
        return Response({"status": "paused"})

    @action(detail=True, methods=["post"])
    def train(self, request, pk=None):
        """
        Kick off knowledge-base indexing. In Phase 1 this marks the agent as
        TRAINING and enqueues the (Phase 2) embedding task; if Celery isn't
        wired for embeddings yet it falls back to a synchronous chunk count so
        the UI still reflects reality.
        """
        agent = self.get_object()
        agent.status = AIAgentStatus.TRAINING
        agent.save(update_fields=["status", "updated_date"])
        try:
            from .tasks import index_agent_knowledge
            index_agent_knowledge.delay(agent.id)
            return Response({"status": "training", "mode": "async"})
        except Exception as exc:
            logger.warning("Async indexing unavailable (%s); counting items only", exc)
            count = agent.knowledge_items.filter(is_active=True).count()
            agent.kb_chunk_count = count
            agent.kb_last_indexed = timezone.now()
            agent.status = AIAgentStatus.DRAFT
            agent.save(update_fields=[
                "kb_chunk_count", "kb_last_indexed", "status", "updated_date"
            ])
            return Response({"status": "indexed", "mode": "sync", "chunks": count})

    @action(detail=True, methods=["get"])
    def preview_prompt(self, request, pk=None):
        """Return the full assembled system prompt (persona + KB) for review."""
        from .brain import assemble_system_prompt
        agent = self.get_object()
        return Response({"system_prompt": assemble_system_prompt(agent)})


class AIKnowledgeItemViewSet(viewsets.ModelViewSet):
    serializer_class = AIKnowledgeItemSerializer
    permission_classes = [IsAuthenticated, HasActiveAISubscription, IsTenantAdminForAI]

    def get_queryset(self):
        qs = AIKnowledgeItem.objects.filter(
            agent__user__tenant=self.request.user.tenant
        )
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs


class AICallSessionViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = AICallSession.objects.filter(
            agent__user__tenant=self.request.user.tenant
        ).select_related("agent")
        agent_id = self.request.query_params.get("agent")
        if agent_id:
            qs = qs.filter(agent_id=agent_id)
        return qs

    def get_serializer_class(self):
        if self.action == "retrieve":
            return AICallSessionSerializer
        return AICallSessionListSerializer


class AICallbackViewSet(viewsets.ModelViewSet):
    serializer_class = AICallbackSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AICallback.objects.filter(
            agent__user__tenant=self.request.user.tenant
        ).select_related("agent", "assigned_agent")
