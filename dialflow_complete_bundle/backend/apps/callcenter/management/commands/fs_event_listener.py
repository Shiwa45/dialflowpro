"""
Long-running FreeSWITCH event listener.

Run as a separate process (supervisor / systemd / `python manage.py fs_event_listener`).
It opens an inbound ESL connection, subscribes to the events we care about, and
translates them into:

  * Agent presence  (CUSTOM sofia::register / sofia::unregister)
  * Agent state     (CHANNEL_CREATE / CHANNEL_ANSWER / CHANNEL_HANGUP / CHANNEL_BRIDGE)

Each translation updates the Agent row AND broadcasts over Channels via
apps.callcenter.realtime, so the admin Live Monitoring panel and the agent
softphone update in real time with no polling.

Because django-tenants puts each tenant's Agent rows in its own schema, the
listener resolves the tenant from the agent's SIP extension by scanning tenant
schemas. For a single-tenant dev setup this is just one schema.

Notes
-----
greenswitch's InboundESL exposes `register_handle(event_name, callback)` and
`process_events()`. We subscribe with `events plain ALL`-style filtering by
registering handlers for specific event names.
"""
from __future__ import annotations

import logging
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection

import greenswitch

from apps.callcenter.constants import AgentStatus, AgentState

logger = logging.getLogger(__name__)


# Map a SIP user (extension) -> Agent across all tenant schemas. Cached per loop.
def _iter_tenant_schemas():
    """Yield schema_name for every tenant (plus 'public' fallback)."""
    try:
        from django_tenants.utils import get_tenant_model
        TenantModel = get_tenant_model()
        for t in TenantModel.objects.exclude(schema_name="public"):
            yield t.schema_name
    except Exception:
        # Non-tenant / dev fallback
        yield connection.schema_name if hasattr(connection, "schema_name") else "public"


def _find_agent_by_extension(ext: str):
    """
    Search every tenant schema for an Agent whose sip_extension matches `ext`.
    Returns (agent, schema_name) or (None, None). Sets the connection schema as
    a side effect so the caller can save within the right schema.
    """
    from apps.callcenter.models import Agent
    for schema in _iter_tenant_schemas():
        try:
            connection.set_schema(schema)
        except Exception:
            pass
        agent = Agent.objects.filter(sip_extension=ext).select_related("user").first()
        if agent:
            return agent, schema
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
            f"Connecting ESL listener to {cfg['host']}:{cfg['port']} ..."
        ))

        while True:
            try:
                self._run(cfg)
            except Exception as exc:
                logger.error("ESL listener crashed: %s; reconnecting in 5s", exc)
                time.sleep(5)

    # ----------------------------------------------------------------- #
    def _run(self, cfg):
        conn = greenswitch.InboundESL(
            host=cfg["host"], port=cfg["port"], password=cfg["password"]
        )
        conn.connect()
        if not conn.connected:
            raise RuntimeError("ESL connect failed")

        # Subscribe to the events we translate.
        for ev in (
            "CHANNEL_CREATE", "CHANNEL_ANSWER", "CHANNEL_BRIDGE",
            "CHANNEL_HANGUP", "CHANNEL_HANGUP_COMPLETE",
            "CUSTOM",
        ):
            conn.register_handle(ev, self._dispatch)
        conn.send("events plain CHANNEL_CREATE CHANNEL_ANSWER CHANNEL_BRIDGE "
                  "CHANNEL_HANGUP CHANNEL_HANGUP_COMPLETE "
                  "CUSTOM sofia::register sofia::unregister sofia::expire")

        self.stdout.write(self.style.SUCCESS("ESL listener connected; processing events."))
        conn.process_events()  # blocks

    # ----------------------------------------------------------------- #
    def _dispatch(self, event):
        try:
            self._handle_event(event)
        except Exception as exc:
            logger.error("Error handling event: %s", exc)

    def _handle_event(self, event):
        from apps.callcenter.realtime import (
            broadcast_agent_status, broadcast_agent_presence,
            broadcast_call_event, broadcast_dashboard_snapshot,
        )

        name = event.headers.get("Event-Name", "")
        subclass = event.headers.get("Event-Subclass", "")

        # ---- SIP registration => presence -------------------------------- #
        if name == "CUSTOM" and subclass in ("sofia::register", "sofia::unregister", "sofia::expire"):
            ext = event.headers.get("from-user") or event.headers.get("username") or ""
            if not ext:
                return
            agent, _ = _find_agent_by_extension(ext)
            if not agent:
                return
            registered = subclass == "sofia::register"
            if registered:
                # Newly registered softphone => mark Available/Waiting (ready pool)
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
        # Determine the agent extension on this channel.
        ext = (
            event.headers.get("Caller-Caller-ID-Number")
            or event.headers.get("variable_user_name")
            or event.headers.get("Caller-Username")
            or ""
        )
        uuid = event.headers.get("Unique-ID", "")
        other = event.headers.get("Other-Leg-Caller-ID-Number", "")
        agent, _ = _find_agent_by_extension(ext)
        if not agent:
            return

        if name == "CHANNEL_CREATE":
            agent.state = AgentState.RECEIVING
            agent.save(update_fields=["state", "last_status_change"])
            broadcast_call_event(event="ringing", agent_id=agent.id,
                                 agent_name=agent.name, caller=other,
                                 callee=ext, uuid=uuid)
        elif name in ("CHANNEL_ANSWER", "CHANNEL_BRIDGE"):
            agent.state = AgentState.IN_A_QUEUE_CALL
            agent.last_bridge_start = _now()
            agent.save(update_fields=["state", "last_bridge_start", "last_status_change"])
            broadcast_call_event(event="answered", agent_id=agent.id,
                                 agent_name=agent.name, caller=other,
                                 callee=ext, uuid=uuid)
        elif name in ("CHANNEL_HANGUP", "CHANNEL_HANGUP_COMPLETE"):
            billsec = int(event.headers.get("variable_billsec", 0) or 0)
            agent.state = AgentState.WAITING
            agent.last_bridge_end = _now()
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


def _now():
    from django.utils import timezone
    return timezone.now()
