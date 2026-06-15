"""
Real-time broadcast helpers for the call center.

This is the missing piece in the original architecture: the consumers in
`consumers.py` only ever *received* group events, but nothing in the codebase
ever called `group_send`. Every status change, presence change and live-call
event now flows through the functions here.

All functions are safe to call from synchronous Django code (views, signals,
the ESL listener thread, Celery tasks). They use `async_to_sync` internally.

Groups
------
  agent_status            broadcast of every agent status/state change
  agent_presence          SIP registration (registered / unregistered)
  dashboard               aggregate metrics for Live Monitoring
  queue_<id>              per-queue waiting/active updates
  monitor_<agent_id>      monitoring session events for a single agent
"""
from __future__ import annotations

import logging
from typing import Any, Optional

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

logger = logging.getLogger(__name__)


def _send(group: str, message: dict[str, Any]) -> None:
    """Fire-and-forget group_send that never raises into the caller."""
    layer = get_channel_layer()
    if layer is None:
        logger.warning("No channel layer configured; cannot broadcast to %s", group)
        return
    try:
        async_to_sync(layer.group_send)(group, message)
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("group_send to %s failed: %s", group, exc)


# --------------------------------------------------------------------------- #
#  Agent status / state
# --------------------------------------------------------------------------- #
def broadcast_agent_status(agent) -> None:
    """
    Broadcast an agent's current status + state to both the agent-status group
    and the dashboard group.

    `agent` is a callcenter.models.Agent instance.
    """
    payload = {
        "type": "agent_status_update",          # -> consumer method agent_status_update
        "agent_id": agent.id,
        "agent_name": agent.name,
        "status": agent.status,
        "status_display": agent.get_status_display(),
        "state": agent.state,
        "state_display": agent.get_state_display(),
        "extension": agent.sip_extension,
        "calls_answered": agent.calls_answered,
        "talk_time": agent.talk_time,
        "timestamp": timezone.now().isoformat(),
    }
    _send("agent_status", payload)
    _send("dashboard", {**payload, "type": "agent_status_update"})


def broadcast_agent_presence(agent, registered: bool, source: str = "sofia") -> None:
    """
    Broadcast a SIP registration change. `registered=True` means the softphone
    just REGISTERed (agent should appear in the "ready to receive" pool);
    `False` means it unregistered / expired.
    """
    payload = {
        "type": "agent_presence_update",
        "agent_id": agent.id,
        "agent_name": agent.name,
        "extension": agent.sip_extension,
        "registered": registered,
        "source": source,
        "timestamp": timezone.now().isoformat(),
    }
    _send("agent_status", payload)
    _send("dashboard", payload)


# --------------------------------------------------------------------------- #
#  Live call events (for the recent-activity feed + agent cards)
# --------------------------------------------------------------------------- #
def broadcast_call_event(
    *,
    event: str,                       # "ringing" | "answered" | "hangup"
    agent_id: Optional[int],
    agent_name: str = "",
    caller: str = "",
    callee: str = "",
    uuid: str = "",
    queue: str = "",
    duration: int = 0,
) -> None:
    payload = {
        "type": "call_event",
        "event": event,
        "agent_id": agent_id,
        "agent_name": agent_name,
        "caller": caller,
        "callee": callee,
        "uuid": uuid,
        "queue": queue,
        "duration": duration,
        "timestamp": timezone.now().isoformat(),
    }
    _send("dashboard", payload)
    if agent_id:
        _send("agent_status", payload)


# --------------------------------------------------------------------------- #
#  Monitoring session events (listen / whisper / barge / takeover)
# --------------------------------------------------------------------------- #
def broadcast_monitor_event(agent_id: int, mode: str, active: bool, by_user: str = "") -> None:
    """
    Tell a specific agent's softphone (and supervisors watching) that a
    supervisor started/stopped monitoring their call.

    mode: "listen" | "whisper" | "barge" | "takeover"
    """
    payload = {
        "type": "monitor_event",
        "agent_id": agent_id,
        "mode": mode,
        "active": active,
        "by_user": by_user,
        "timestamp": timezone.now().isoformat(),
    }
    _send(f"monitor_{agent_id}", payload)
    _send("dashboard", payload)


# --------------------------------------------------------------------------- #
#  Dashboard aggregate snapshot
# --------------------------------------------------------------------------- #
def broadcast_dashboard_snapshot() -> None:
    """
    Compute and broadcast the aggregate metrics used by the Live Monitoring
    header cards. Cheap enough to call after any status change.
    """
    from .models import Agent, Queue, QueueMember
    from .constants import AgentStatus, AgentState

    agents = Agent.objects.all()
    total_agents = agents.count()
    available = agents.filter(status=AgentStatus.AVAILABLE,
                              state=AgentState.WAITING).count()
    on_call = agents.filter(state=AgentState.IN_A_QUEUE_CALL).count()

    waiting = QueueMember.objects.filter(
        abandoned_epoch__isnull=True,
        serving_agent__isnull=True,
    ).count()
    active = QueueMember.objects.filter(
        serving_agent__isnull=False,
        abandoned_epoch__isnull=True,
    ).count()

    payload = {
        "type": "dashboard_update",
        "total_agents": total_agents,
        "available_agents": available,
        "on_call_agents": on_call,
        "total_queues": Queue.objects.count(),
        "total_waiting_calls": waiting,
        "total_active_calls": active,
        "longest_wait_time": 0,
        "avg_wait_time": 0,
        "service_level": 0,
        "timestamp": timezone.now().isoformat(),
    }
    _send("dashboard", payload)
