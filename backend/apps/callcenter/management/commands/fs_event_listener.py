"""
Long-running FreeSWITCH event listener — the real-time event source.

Run as a separate always-on process:
    python manage.py fs_event_listener --node fs1

It opens a DEDICATED inbound ESL connection, subscribes to sofia registration +
channel-lifecycle events, and translates them into:

  * Agent presence  (CUSTOM sofia::register / sofia::unregister / sofia::expire)
  * Agent state     (CHANNEL_CREATE / CHANNEL_ANSWER / CHANNEL_BRIDGE / CHANNEL_HANGUP)

Each translation updates the Agent row AND broadcasts over Channels via
apps.callcenter.realtime, so the admin Agent Tracking panel updates in real time.

Implementation note
-------------------
This uses the project's synchronous socket-based ESLClient (apps.dialer_cdr.esl)
rather than greenswitch. greenswitch is gevent-based and hangs ("operation would
block forever") when its loop isn't driven — which is the case in a plain
management-command process. The synchronous reader blocks cleanly on the event
stream and reconnects with backoff.

Multi-tenant: agent rows live per tenant schema, so we resolve the tenant from
the SIP extension by scanning tenant schemas (one schema in single-tenant dev).
"""
from __future__ import annotations

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.callcenter.constants import AgentStatus, AgentState

logger = logging.getLogger(__name__)

# Events we translate. CUSTOM subclasses (sofia::*) must be listed explicitly.
EVENT_SUBSCRIPTION = (
    "plain CHANNEL_CREATE CHANNEL_ANSWER CHANNEL_BRIDGE "
    "CHANNEL_HANGUP CHANNEL_HANGUP_COMPLETE "
    "CUSTOM sofia::register sofia::unregister sofia::expire"
)


def _iter_tenant_schemas():
    """Yield schema_name for every non-public tenant (fallback: 'public')."""
    try:
        from django_tenants.utils import get_tenant_model
        TenantModel = get_tenant_model()
        schemas = list(
            TenantModel.objects.exclude(schema_name="public")
            .values_list("schema_name", flat=True)
        )
        if schemas:
            yield from schemas
            return
    except Exception:
        pass
    yield "public"


def _find_agent_by_extension(ext: str):
    """
    Search every tenant schema for an Agent whose sip_extension matches `ext`.
    Returns (agent, schema_name) or (None, None). The agent is loaded inside a
    schema_context; callers re-enter schema_context(schema) to save.
    """
    from django_tenants.utils import schema_context
    from apps.callcenter.models import Agent
    if not ext:
        return None, None
    for schema in _iter_tenant_schemas():
        try:
            with schema_context(schema):
                agent = Agent.objects.filter(sip_extension=ext).select_related("user").first()
                if agent:
                    return agent, schema
        except Exception:
            continue
    return None, None


class Command(BaseCommand):
    help = "Run the FreeSWITCH ESL event listener for real-time agent tracking."

    def add_arguments(self, parser):
        parser.add_argument("--node", default="fs1")

    def handle(self, *args, **opts):
        node = opts["node"]
        cfg = settings.FREESWITCH_NODES.get(node)
        if not cfg:
            self.stderr.write(self.style.ERROR(f"Node '{node}' not configured"))
            return

        self.stdout.write(self.style.SUCCESS(
            f"Starting ESL event listener for {cfg['host']}:{cfg['port']} ..."
        ))

        while True:
            try:
                self._run(cfg)
            except Exception as exc:
                logger.error("ESL listener crashed: %s; reconnecting in 5s", exc)
                time.sleep(5)

    # ----------------------------------------------------------------- #
    def _run(self, cfg):
        from apps.dialer_cdr.esl import ESLClient

        conn = ESLClient(host=cfg["host"], port=int(cfg["port"]), password=cfg["password"])
        conn.connect()
        reply = conn.subscribe(EVENT_SUBSCRIPTION)
        logger.info("ESL listener subscribed: %s", reply.headers.get("Reply-Text", ""))
        self.stdout.write(self.style.SUCCESS("ESL listener connected; processing events."))

        # Block indefinitely on the event stream.
        conn.set_read_timeout(None)
        try:
            while True:
                event = conn.recv_event()
                self._dispatch(event)
        finally:
            conn.close()

    # ----------------------------------------------------------------- #
    def _dispatch(self, event):
        try:
            self._handle_event(event)
        except Exception as exc:
            logger.error("Error handling event: %s", exc)

    def _handle_event(self, event):
        from django.utils import timezone
        from django_tenants.utils import schema_context
        from apps.callcenter.realtime import (
            broadcast_agent_status, broadcast_agent_presence,
            broadcast_call_event, broadcast_dashboard_snapshot,
        )

        name = event.headers.get("Event-Name", "")
        subclass = event.headers.get("Event-Subclass", "")

        # ---- SIP registration => presence -------------------------------- #
        if name == "CUSTOM" and subclass in ("sofia::register", "sofia::unregister", "sofia::expire"):
            ext = event.headers.get("from-user") or event.headers.get("username") or ""
            agent, schema = _find_agent_by_extension(ext)
            if not agent:
                return
            registered = subclass == "sofia::register"
            with schema_context(schema):
                if registered:
                    # Newly registered softphone => ready pool if logged out
                    if agent.status == AgentStatus.LOGGED_OUT:
                        agent.status = AgentStatus.AVAILABLE
                        agent.state = AgentState.WAITING
                        agent.save(update_fields=["status", "state", "last_status_change"])
                else:
                    agent.status = AgentStatus.LOGGED_OUT
                    agent.state = AgentState.WAITING
                    agent.save(update_fields=["status", "state", "last_status_change"])
                broadcast_agent_presence(agent, registered)
                broadcast_agent_status(agent)
                broadcast_dashboard_snapshot()
            return

        # ---- Channel lifecycle => agent state ---------------------------- #
        ext = (
            event.headers.get("Caller-Caller-ID-Number")
            or event.headers.get("variable_user_name")
            or event.headers.get("Caller-Username")
            or ""
        )
        uuid = event.headers.get("Unique-ID", "")
        other = event.headers.get("Other-Leg-Caller-ID-Number", "")
        agent, schema = _find_agent_by_extension(ext)
        if not agent:
            return

        with schema_context(schema):
            if name == "CHANNEL_CREATE":
                agent.state = AgentState.RECEIVING
                agent.save(update_fields=["state", "last_status_change"])
                broadcast_call_event(event="ringing", agent_id=agent.id,
                                     agent_name=agent.name, caller=other,
                                     callee=ext, uuid=uuid)
            elif name in ("CHANNEL_ANSWER", "CHANNEL_BRIDGE"):
                agent.state = AgentState.IN_A_QUEUE_CALL
                agent.last_bridge_start = timezone.now()
                agent.save(update_fields=["state", "last_bridge_start", "last_status_change"])
                broadcast_call_event(event="answered", agent_id=agent.id,
                                     agent_name=agent.name, caller=other,
                                     callee=ext, uuid=uuid)
            elif name in ("CHANNEL_HANGUP", "CHANNEL_HANGUP_COMPLETE"):
                billsec = int(event.headers.get("variable_billsec", 0) or 0)
                # Go to IDLE (after-call work), NOT Waiting — the agent must
                # submit a disposition before becoming available again. Keeps
                # the mandatory-wrap-up gating consistent with hangup_webhook.
                agent.state = AgentState.IDLE
                agent.last_bridge_end = timezone.now()
                if billsec:
                    agent.talk_time = (agent.talk_time or 0) + billsec
                    agent.calls_answered = (agent.calls_answered or 0) + 1
                agent.save(update_fields=[
                    "state", "last_bridge_end", "talk_time",
                    "calls_answered", "last_status_change",
                ])
                broadcast_call_event(event="hangup", agent_id=agent.id,
                                     agent_name=agent.name, caller=other,
                                     callee=ext, uuid=uuid, duration=billsec)
            else:
                return

            broadcast_agent_status(agent)
            broadcast_dashboard_snapshot()
