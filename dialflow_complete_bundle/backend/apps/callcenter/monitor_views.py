"""
Supervisor live-monitoring REST endpoints.

These complement the WebSocket feed: the panel loads the current snapshot on
mount via `live_agents`, then receives deltas over the socket. Listen / whisper
/ barge / takeover are actions that issue ESL commands and need a registered
supervisor extension.
"""
import logging

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.dialer_cdr.models import VoIPCall  # noqa: F401 (kept for future CDR lookups)

from .models import Agent
from .constants import AgentStatus, AgentState
from .monitoring import start_monitor, stop_monitor, takeover_call
from .realtime import broadcast_monitor_event

logger = logging.getLogger(__name__)


def _supervisor_extension(request) -> str:
    """Resolve the calling supervisor's SIP extension from their Agent profile."""
    try:
        return request.user.agent_profile.sip_extension or ""
    except Exception:
        return ""


def _agent_live_uuid(agent: Agent) -> str:
    """
    Best-effort lookup of the agent's currently active channel UUID.

    The event listener stores it via realtime broadcast; for a robust source we
    query FreeSWITCH directly for a channel whose user matches the extension.
    """
    from apps.dialer_cdr.esl import get_esl_connection
    conn = get_esl_connection("fs1")
    if not conn or not agent.sip_extension:
        return ""
    try:
        resp = conn.send(
            f"api show channels like {agent.sip_extension} as json"
        )
        import json as _json
        text = str(getattr(resp, "data", resp) or "")
        # crude parse: find first uuid field
        start = text.find("{")
        if start >= 0:
            data = _json.loads(text[start:])
            rows = data.get("rows") or []
            if rows:
                return rows[0].get("uuid", "")
    except Exception as exc:
        logger.warning("uuid lookup failed for ext %s: %s", agent.sip_extension, exc)
    return ""


class MonitorViewSet(viewsets.ViewSet):
    """
    Routes under /api/callcenter/monitor/
    """
    permission_classes = [IsAuthenticated]

    def _get_agent(self, request, pk):
        return Agent.objects.filter(
            user__tenant=request.user.tenant, pk=pk
        ).select_related("user").first()

    @action(detail=False, methods=["get"])
    def live_agents(self, request):
        """
        Snapshot of every agent with their status/state for the panel's initial
        render. The 'registered' flag mirrors whether they are in the ready pool
        (status != LOGGED_OUT).
        """
        qs = Agent.objects.filter(user__tenant=request.user.tenant).select_related("user")
        data = [{
            "id": a.id,
            "name": a.name,
            "extension": a.sip_extension,
            "status": a.status,
            "status_display": a.get_status_display(),
            "state": a.state,
            "state_display": a.get_state_display(),
            "registered": a.status != AgentStatus.LOGGED_OUT,
            "on_call": a.state == AgentState.IN_A_QUEUE_CALL,
            "calls_answered": a.calls_answered,
            "talk_time": a.talk_time,
        } for a in qs]
        return Response(data)

    @action(detail=True, methods=["post"])
    def listen(self, request, pk=None):
        return self._monitor(request, pk, "listen")

    @action(detail=True, methods=["post"])
    def whisper(self, request, pk=None):
        return self._monitor(request, pk, "whisper")

    @action(detail=True, methods=["post"])
    def barge(self, request, pk=None):
        return self._monitor(request, pk, "barge")

    def _monitor(self, request, pk, mode):
        agent = self._get_agent(request, pk)
        if not agent:
            return Response({"error": "Agent not found"}, status=404)
        sup_ext = _supervisor_extension(request)
        if not sup_ext:
            return Response(
                {"error": "Your user has no SIP extension; cannot monitor."},
                status=400,
            )
        uuid = _agent_live_uuid(agent)
        if not uuid:
            return Response({"error": "Agent is not on a live call."}, status=409)

        ok, resp = start_monitor(agent_uuid=uuid, supervisor_ext=sup_ext, mode=mode)
        if not ok:
            return Response({"error": resp}, status=502)
        broadcast_monitor_event(agent.id, mode, True, by_user=request.user.username)
        return Response({"status": "monitoring", "mode": mode, "agent_uuid": uuid})

    @action(detail=True, methods=["post"])
    def takeover(self, request, pk=None):
        agent = self._get_agent(request, pk)
        if not agent:
            return Response({"error": "Agent not found"}, status=404)
        sup_ext = _supervisor_extension(request)
        if not sup_ext:
            return Response({"error": "Your user has no SIP extension."}, status=400)
        uuid = _agent_live_uuid(agent)
        if not uuid:
            return Response({"error": "Agent is not on a live call."}, status=409)

        ok, resp = takeover_call(agent_uuid=uuid, supervisor_ext=sup_ext)
        if not ok:
            return Response({"error": resp}, status=502)
        broadcast_monitor_event(agent.id, "takeover", True, by_user=request.user.username)
        return Response({"status": "takeover", "agent_uuid": uuid})

    @action(detail=True, methods=["post"])
    def stop(self, request, pk=None):
        agent = self._get_agent(request, pk)
        if not agent:
            return Response({"error": "Agent not found"}, status=404)
        sup_uuid = request.data.get("supervisor_uuid", "")
        if sup_uuid:
            stop_monitor(supervisor_uuid=sup_uuid)
        broadcast_monitor_event(agent.id, "listen", False, by_user=request.user.username)
        return Response({"status": "stopped"})
