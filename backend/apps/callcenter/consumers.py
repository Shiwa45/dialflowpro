"""
WebSocket consumers for real-time call center updates.
Sends agent status changes and queue updates to connected clients.
"""
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)


class AgentStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for agent status updates.
    
    Usage:
    ws://localhost:8000/ws/callcenter/agents/
    
    Sends:
    {
        "type": "agent_status",
        "agent_id": 1,
        "agent_name": "John Doe",
        "status": 1,
        "status_display": "Available",
        "state": "Waiting"
    }
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        # Join agent status group
        self.group_name = 'agent_status'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Agent status WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Leave group on disconnect"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Agent status WebSocket disconnected: {self.channel_name}")
    
    async def agent_status_update(self, event):
        """Receive agent status update from group and send to WebSocket"""
        await self.send_json({
            'type': 'agent_status',
            'agent_id': event['agent_id'],
            'agent_name': event['agent_name'],
            'status': event['status'],
            'status_display': event['status_display'],
            'state': event['state']
        })


class QueueStatusConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for queue status updates.
    
    Usage:
    ws://localhost:8000/ws/callcenter/queues/{queue_id}/
    
    Sends:
    {
        "type": "queue_update",
        "queue_id": 1,
        "queue_name": "Support",
        "waiting_calls": 3,
        "active_agents": 5,
        "members": [...]
    }
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.queue_id = self.scope['url_route']['kwargs']['queue_id']
        self.group_name = f'queue_{self.queue_id}'
        
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Queue status WebSocket connected: {self.channel_name} for queue {self.queue_id}")
    
    async def disconnect(self, close_code):
        """Leave group on disconnect"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Queue status WebSocket disconnected: {self.channel_name}")
    
    async def queue_update(self, event):
        """Receive queue update from group and send to WebSocket"""
        await self.send_json({
            'type': 'queue_update',
            'queue_id': event['queue_id'],
            'queue_name': event['queue_name'],
            'waiting_calls': event['waiting_calls'],
            'active_agents': event['active_agents'],
            'members': event.get('members', [])
        })


class LiveDashboardConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket consumer for live dashboard updates.
    Aggregates all call center metrics.
    
    Usage:
    ws://localhost:8000/ws/callcenter/dashboard/
    
    Sends:
    {
        "type": "dashboard_update",
        "total_agents": 10,
        "available_agents": 7,
        "total_queues": 3,
        "total_waiting_calls": 5,
        "total_active_calls": 12
    }
    """
    
    async def connect(self):
        """Accept WebSocket connection"""
        self.group_name = 'dashboard'
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()
        logger.info(f"Dashboard WebSocket connected: {self.channel_name}")
    
    async def disconnect(self, close_code):
        """Leave group on disconnect"""
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name
        )
        logger.info(f"Dashboard WebSocket disconnected: {self.channel_name}")
    
    async def dashboard_update(self, event):
        """Receive dashboard update from group and send to WebSocket"""
        await self.send_json({
            'type': 'dashboard_update',
            'total_agents': event['total_agents'],
            'available_agents': event['available_agents'],
            'total_queues': event['total_queues'],
            'total_waiting_calls': event['total_waiting_calls'],
            'total_active_calls': event['total_active_calls'],
            'timestamp': event.get('timestamp')
        })
