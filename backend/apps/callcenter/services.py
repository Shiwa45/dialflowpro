"""
Predictive Dialing Service.

Handles routing of connected calls to available agents via the WS channel layer.
Called by the campaign_spool_contact task and FreeSWITCH webhooks when calls connect.
"""
from __future__ import annotations
import logging
from typing import Optional
from django.utils import timezone
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from datetime import timedelta

from django.conf import settings

from .models import Agent, Queue, Tier, QueueMember
from .constants import AgentStatus, AgentState

logger = logging.getLogger(__name__)

# An agent's WebSocket heartbeat must be newer than this to count as "present".
# Client sends a heartbeat every ~15 s, so 60 s tolerates a couple of misses
# (e.g. during a brief reconnect) without flapping the agent offline.
HEARTBEAT_STALE_SECONDS = 60


def get_registered_extensions(node: str = 'fs1') -> Optional[set]:
    """
    Query FreeSWITCH for the set of currently-registered SIP extensions.

    Returns:
        set[str] of registered extension numbers, or
        None if the registration state could not be determined (ESL down).
    """
    import json as _json
    from apps.dialer_cdr.esl import get_esl_connection
    try:
        conn = get_esl_connection(node)
        if not conn:
            logger.warning("Cannot verify SIP registrations — no ESL connection")
            return None
        resp = conn.send('api show registrations as json')
        data = (getattr(resp, 'data', '') or '').strip()
        if not data.startswith('{'):
            # "show registrations" returns nothing when zero are registered
            return set()
        parsed = _json.loads(data)
        return {
            str(row.get('reg_user', '')).strip()
            for row in parsed.get('rows', [])
            if row.get('reg_user')
        }
    except Exception as exc:
        logger.error(f"Failed to query SIP registrations: {exc}")
        return None


def agent_is_present(agent: Agent, registered: Optional[set], now=None) -> bool:
    """
    An agent is truly available only when their Agent Desktop WebSocket is
    alive (fresh heartbeat) AND their SIP phone is registered.

    Presence is driven by heartbeat freshness rather than the ws_connected
    flag, so overlapping/duplicate sockets reconnecting don't flap the agent.
    """
    now = now or timezone.now()

    if not agent.last_heartbeat:
        return False
    if (now - agent.last_heartbeat).total_seconds() > HEARTBEAT_STALE_SECONDS:
        return False

    # registered is None → could not verify (ESL down). Fail-closed: not available.
    if registered is None:
        return False
    if (agent.sip_extension or '').strip() not in registered:
        return False

    return True


def _present_agents(queue: Queue, registered: Optional[set] = None) -> list:
    """Return agents in the queue that are AVAILABLE/WAITING and truly present."""
    if registered is None:
        registered = get_registered_extensions()
    now = timezone.now()
    tiers = (
        Tier.objects.filter(
            queue=queue,
            agent__status=AgentStatus.AVAILABLE,
            agent__state=AgentState.WAITING,
        )
        .select_related('agent')
        .order_by('level', 'position')
    )
    return [t.agent for t in tiers if agent_is_present(t.agent, registered, now)]


def count_available_agents(queue: Queue, registered: Optional[set] = None) -> int:
    """Number of agents ready to receive a call right now (presence-verified)."""
    return len(_present_agents(queue, registered))


def find_available_agent(queue: Queue) -> Optional[Agent]:
    """
    Find the best available agent for a queue based on the queue's strategy.
    Only considers agents that are WebSocket-connected AND SIP-registered.

    Strategies:
        1 = Ring All          → return first available (caller rings all)
        2 = Longest Idle      → agent with oldest last_bridge_end
        3 = Round Robin       → agent with least calls_answered
        4 = Top Down          → agent with lowest tier position
        5 = Least Talk Time   → agent with least total talk_time
        6 = Random            → random available agent
    """
    agents = _present_agents(queue)
    if not agents:
        return None

    strategy = queue.strategy

    if strategy == 2:  # Longest Idle
        agents.sort(key=lambda a: a.last_bridge_end or timezone.datetime.min.replace(tzinfo=timezone.utc))
        return agents[0]
    elif strategy == 3:  # Round Robin
        agents.sort(key=lambda a: a.calls_answered)
        return agents[0]
    elif strategy == 5:  # Least Talk Time
        agents.sort(key=lambda a: a.talk_time)
        return agents[0]
    elif strategy == 6:  # Random
        import random
        return random.choice(agents)
    else:  # 1 = Ring All, 4 = Top Down, default
        return agents[0]


def route_call_to_agent(
    agent: Agent,
    call_id: str,
    caller_number: str,
    caller_name: str = '',
    queue_name: str = '',
    campaign_name: str = '',
    lead: Optional[dict] = None,
) -> bool:
    """
    Push an incoming_call event to a specific agent's desktop WS channel.

    Returns True if the message was sent to the channel layer.
    """
    try:
        channel_layer = get_channel_layer()
        group = f'agent_desktop_{agent.id}'

        # Update agent state to receiving
        agent.state = 'Receiving'
        agent.save(update_fields=['state'])

        async_to_sync(channel_layer.group_send)(group, {
            'type': 'incoming_call',
            'call_id': call_id,
            'caller_number': caller_number,
            'caller_name': caller_name,
            'queue_name': queue_name,
            'campaign_name': campaign_name,
            'lead': lead or {},
            'timestamp': timezone.now().isoformat(),
        })

        logger.info(
            f"Routed call {call_id} to agent {agent.name} (ID={agent.id})"
        )
        return True

    except Exception as exc:
        logger.error(f"Failed to route call to agent {agent.id}: {exc}")
        return False


def route_call_to_queue(
    queue: Queue,
    call_id: str,
    caller_number: str,
    caller_name: str = '',
    campaign_name: str = '',
    lead: Optional[dict] = None,
) -> Optional[Agent]:
    """
    Find an available agent in the queue and route the call to them.

    Returns the Agent the call was routed to, or None if no agent available.
    """
    agent = find_available_agent(queue)
    if not agent:
        logger.warning(f"No available agents in queue '{queue.name}' for call {call_id}")
        return None

    success = route_call_to_agent(
        agent=agent,
        call_id=call_id,
        caller_number=caller_number,
        caller_name=caller_name,
        queue_name=queue.name,
        campaign_name=campaign_name,
        lead=lead,
    )

    return agent if success else None


def push_lead_to_agent(
    agent: Agent,
    call_id: str,
    lead: dict,
    campaign: dict,
    script: str = '',
) -> bool:
    """
    Push campaign lead information to the agent after a predictive-dialer
    call connects. The agent sees the lead info before/as the call bridges.
    """
    try:
        channel_layer = get_channel_layer()
        group = f'agent_desktop_{agent.id}'

        async_to_sync(channel_layer.group_send)(group, {
            'type': 'campaign_lead',
            'call_id': call_id,
            'lead': lead,
            'campaign': campaign,
            'script': script,
        })
        return True
    except Exception as exc:
        logger.error(f"Failed to push lead to agent {agent.id}: {exc}")
        return False


def notify_call_ended(agent_id: int, call_id: str, duration: int = 0, hangup_cause: str = ''):
    """
    Push call_ended event to agent desktop when FreeSWITCH reports hangup.
    """
    try:
        channel_layer = get_channel_layer()
        group = f'agent_desktop_{agent_id}'

        async_to_sync(channel_layer.group_send)(group, {
            'type': 'call_ended',
            'call_id': call_id,
            'duration': duration,
            'hangup_cause': hangup_cause,
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as exc:
        logger.error(f"Failed to notify agent {agent_id} of call end: {exc}")


def broadcast_dashboard_update():
    """
    Push updated dashboard metrics to all admin dashboard listeners.
    Call this after any agent/queue state change.
    """
    try:
        from .models import Agent, Queue, QueueMember

        channel_layer = get_channel_layer()
        total_agents = Agent.objects.count()
        available = Agent.objects.filter(status=AgentStatus.AVAILABLE).count()
        on_call = Agent.objects.filter(state='In a queue call').count()
        total_queues = Queue.objects.count()
        waiting = QueueMember.objects.filter(
            abandoned_epoch__isnull=True,
            serving_agent__isnull=True,
        ).count()

        async_to_sync(channel_layer.group_send)('dashboard', {
            'type': 'dashboard_update',
            'total_agents': total_agents,
            'available_agents': available,
            'on_call_agents': on_call,
            'total_queues': total_queues,
            'total_waiting_calls': waiting,
            'total_active_calls': on_call,
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as exc:
        logger.error(f"Failed to broadcast dashboard update: {exc}")
