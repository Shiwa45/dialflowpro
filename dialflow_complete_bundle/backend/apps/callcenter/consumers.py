"""
WebSocket consumers for real-time call center updates.

Sends agent status changes, SIP presence, live-call events and queue updates to
connected clients. These consumers receive events fan-out from
apps.callcenter.realtime via the channel layer.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer
import logging

logger = logging.getLogger(__name__)


class AgentStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    Live agent status + presence + call events.

    ws://<host>/ws/callcenter/agents/
    """

    async def connect(self):
        self.group_name = "agent_status"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()
        logger.info("Agent status WS connected: %s", self.channel_name)

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    # --- handlers (event["type"] -> method name) --- #
    async def agent_status_update(self, event):
        await self.send_json({
            "type": "agent_status",
            "agent_id": event["agent_id"],
            "agent_name": event["agent_name"],
            "status": event["status"],
            "status_display": event["status_display"],
            "state": event["state"],
            "state_display": event.get("state_display", event["state"]),
            "extension": event.get("extension", ""),
            "calls_answered": event.get("calls_answered", 0),
            "talk_time": event.get("talk_time", 0),
            "timestamp": event.get("timestamp"),
        })

    async def agent_presence_update(self, event):
        await self.send_json({
            "type": "agent_presence",
            "agent_id": event["agent_id"],
            "agent_name": event["agent_name"],
            "extension": event.get("extension", ""),
            "registered": event["registered"],
            "source": event.get("source", ""),
            "timestamp": event.get("timestamp"),
        })

    async def call_event(self, event):
        await self.send_json({
            "type": "call_event",
            "event": event["event"],
            "agent_id": event.get("agent_id"),
            "agent_name": event.get("agent_name", ""),
            "caller": event.get("caller", ""),
            "callee": event.get("callee", ""),
            "uuid": event.get("uuid", ""),
            "queue": event.get("queue", ""),
            "duration": event.get("duration", 0),
            "timestamp": event.get("timestamp"),
        })


class QueueStatusConsumer(AsyncJsonWebsocketConsumer):
    """ws://<host>/ws/callcenter/queues/{queue_id}/"""

    async def connect(self):
        self.queue_id = self.scope["url_route"]["kwargs"]["queue_id"]
        self.group_name = f"queue_{self.queue_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def queue_update(self, event):
        await self.send_json({
            "type": "queue_update",
            "queue_id": event["queue_id"],
            "queue_name": event["queue_name"],
            "waiting_calls": event["waiting_calls"],
            "active_agents": event["active_agents"],
            "members": event.get("members", []),
        })


class LiveDashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    Aggregate dashboard + every agent/presence/call/monitor event, so the Live
    Monitoring page needs only ONE socket.

    ws://<host>/ws/callcenter/dashboard/
    """

    async def connect(self):
        self.group_name = "dashboard"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def dashboard_update(self, event):
        await self.send_json({
            "type": "dashboard_update",
            "total_agents": event["total_agents"],
            "available_agents": event["available_agents"],
            "on_call_agents": event.get("on_call_agents", 0),
            "total_queues": event["total_queues"],
            "total_waiting_calls": event["total_waiting_calls"],
            "total_active_calls": event["total_active_calls"],
            "longest_wait_time": event.get("longest_wait_time", 0),
            "avg_wait_time": event.get("avg_wait_time", 0),
            "service_level": event.get("service_level", 0),
            "timestamp": event.get("timestamp"),
        })

    # The dashboard also wants the granular events:
    async def agent_status_update(self, event):
        await AgentStatusConsumer.agent_status_update(self, event)

    async def agent_presence_update(self, event):
        await AgentStatusConsumer.agent_presence_update(self, event)

    async def call_event(self, event):
        await AgentStatusConsumer.call_event(self, event)

    async def monitor_event(self, event):
        await self.send_json({
            "type": "monitor_event",
            "agent_id": event["agent_id"],
            "mode": event["mode"],
            "active": event["active"],
            "by_user": event.get("by_user", ""),
            "timestamp": event.get("timestamp"),
        })


class AgentMonitorConsumer(AsyncJsonWebsocketConsumer):
    """
    Per-agent monitor channel. The agent's own softphone subscribes here so it
    can show a "supervisor is listening" indicator; supervisors can also watch a
    single agent.

    ws://<host>/ws/callcenter/monitor/{agent_id}/
    """

    async def connect(self):
        self.agent_id = self.scope["url_route"]["kwargs"]["agent_id"]
        self.group_name = f"monitor_{self.agent_id}"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def monitor_event(self, event):
        await self.send_json({
            "type": "monitor_event",
            "agent_id": event["agent_id"],
            "mode": event["mode"],
            "active": event["active"],
            "by_user": event.get("by_user", ""),
            "timestamp": event.get("timestamp"),
        })
