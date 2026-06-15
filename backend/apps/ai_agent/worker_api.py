"""
Worker-facing REST surface (Phase 2).

The LiveKit media worker is a separate process with no user session, so it
authenticates with a shared secret header (X-AI-Worker-Token == settings
AI_WORKER_TOKEN) and passes the tenant schema explicitly. These endpoints let
the worker:

  GET  runtime config for an agent (resolved by called DID or agent id)
  POST a retrieval query  -> top-K knowledge snippets
  POST call results       -> AICallSession + transcript turns + metering
  POST a scheduled callback

Everything is scoped to the tenant schema the worker names, and django-tenants
activates that schema for the request.
"""
import logging

from django.conf import settings
from django.db import connection
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import AIAgent, AICallSession, AITranscriptTurn, AICallback, AISubscription
from .brain import assemble_system_prompt, retrieve_context
from .constants import AIAgentStatus

logger = logging.getLogger(__name__)


def _check_worker(request) -> bool:
    token = request.headers.get("X-AI-Worker-Token", "")
    expected = getattr(settings, "AI_WORKER_TOKEN", "")
    return bool(expected) and token == expected


def _activate_schema(request):
    """Switch to the tenant schema the worker names (header or body)."""
    schema = request.headers.get("X-Tenant") or request.data.get("tenant_schema")
    if schema:
        try:
            connection.set_schema(schema)
        except Exception as exc:
            logger.warning("schema switch failed for %s: %s", schema, exc)
    return schema


@api_view(["GET"])
@authentication_classes([])
@permission_classes([AllowAny])
def worker_agent_config(request):
    """
    Resolve an agent and return everything the worker needs to build the
    AgentSession. Query by ?agent_id= or ?did= (the called number mapped to an
    agent via AIAgent.name match or a DID field you maintain).
    """
    if not _check_worker(request):
        return Response({"error": "unauthorized"}, status=401)
    _activate_schema(request)

    agent_id = request.query_params.get("agent_id")
    qs = AIAgent.objects.filter(status=AIAgentStatus.ACTIVE)
    agent = qs.filter(id=agent_id).first() if agent_id else None
    if not agent:
        return Response({"error": "no active agent"}, status=404)

    # Subscription / quota gate — worker should decline AI if exhausted.
    sub = AISubscription.objects.filter(tenant=agent.user.tenant).first()
    quota_ok = bool(sub and sub.is_active and not sub.quota_exhausted)

    return Response({
        "id": agent.id,
        "name": agent.name,
        "persona_name": agent.persona_name,
        "greeting": agent.greeting,
        "system_prompt": assemble_system_prompt(agent),
        "temperature": agent.temperature,
        "max_response_tokens": agent.max_response_tokens,
        "llm_provider": agent.llm_provider,
        "llm_model": agent.active_llm_model,
        "enable_thinking": agent.enable_thinking,
        "language": agent.primary_language,
        "auto_detect_language": agent.auto_detect_language,
        "stt_model": agent.stt_model,
        "stt_mode": agent.stt_mode,
        "tts_model": agent.tts_model,
        "tts_speaker": agent.tts_speaker,
        "tts_pace": agent.tts_pace,
        "tts_temperature": agent.tts_temperature,
        "allow_human_transfer": agent.allow_human_transfer,
        "transfer_queue_id": agent.transfer_queue_id,
        "allow_callback": agent.allow_callback,
        "confidence_transfer_threshold": agent.confidence_transfer_threshold,
        "max_call_duration_seconds": agent.max_call_duration_seconds,
        "quota_ok": quota_ok,
    })


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def worker_retrieve(request):
    """Return top-K knowledge snippets for a caller utterance (RAG)."""
    if not _check_worker(request):
        return Response({"error": "unauthorized"}, status=401)
    _activate_schema(request)
    agent = AIAgent.objects.filter(id=request.data.get("agent_id")).first()
    if not agent:
        return Response({"error": "agent not found"}, status=404)
    query = request.data.get("query", "")
    top_k = int(request.data.get("top_k", 4))
    snippets = retrieve_context(agent, query, top_k=top_k)
    return Response({"snippets": snippets})


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def worker_call_result(request):
    """
    Persist a finished (or live-updating) AI call. Idempotent on call_uuid:
    upserts the session, replaces transcript turns, updates metering.
    """
    if not _check_worker(request):
        return Response({"error": "unauthorized"}, status=401)
    _activate_schema(request)

    d = request.data
    agent = AIAgent.objects.filter(id=d.get("agent_id")).first()
    if not agent:
        return Response({"error": "agent not found"}, status=404)

    session, _ = AICallSession.objects.update_or_create(
        call_uuid=d.get("call_uuid", ""),
        defaults={
            "agent": agent,
            "livekit_room": d.get("livekit_room", ""),
            "caller_number": d.get("caller_number", ""),
            "started_at": d.get("started_at"),
            "ended_at": d.get("ended_at"),
            "duration_seconds": d.get("duration_seconds", 0),
            "outcome": d.get("outcome", ""),
            "detected_language": d.get("detected_language", ""),
            "transfer_reason": d.get("transfer_reason", ""),
            "sentiment_score": d.get("sentiment_score"),
            "summary": d.get("summary", ""),
        },
    )

    turns = d.get("turns")
    if isinstance(turns, list):
        AITranscriptTurn.objects.filter(session=session).delete()
        AITranscriptTurn.objects.bulk_create([
            AITranscriptTurn(
                session=session,
                role=t.get("role", "system"),
                text=t.get("text", ""),
                language=t.get("language", ""),
                confidence=t.get("confidence"),
                started_at=t.get("started_at"),
            ) for t in turns
        ])

    # Metering: add minutes to the tenant subscription.
    mins = max(0, round(session.duration_seconds / 60))
    if mins:
        sub = AISubscription.objects.filter(tenant=agent.user.tenant).first()
        if sub:
            sub.minutes_used_this_period += mins
            sub.save(update_fields=["minutes_used_this_period", "updated_date"])

    return Response({"id": session.id, "status": "saved"}, status=status.HTTP_200_OK)


@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def worker_schedule_callback(request):
    if not _check_worker(request):
        return Response({"error": "unauthorized"}, status=401)
    _activate_schema(request)
    agent = AIAgent.objects.filter(id=request.data.get("agent_id")).first()
    if not agent:
        return Response({"error": "agent not found"}, status=404)
    cb = AICallback.objects.create(
        agent=agent,
        session=AICallSession.objects.filter(call_uuid=request.data.get("call_uuid", "")).first(),
        caller_number=request.data.get("caller_number", ""),
        requested_for=request.data.get("requested_for") or timezone.now(),
        notes=request.data.get("notes", ""),
    )
    return Response({"id": cb.id, "status": "scheduled"})
