"""
WebSocket routing for callcenter app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # Admin dashboard listeners
    re_path(r'ws/callcenter/agents/$', consumers.AgentStatusConsumer.as_asgi()),
    re_path(r'ws/callcenter/queues/(?P<queue_id>\d+)/$', consumers.QueueStatusConsumer.as_asgi()),
    re_path(r'ws/callcenter/dashboard/$', consumers.LiveDashboardConsumer.as_asgi()),

    # Agent desktop — bidirectional, per-agent channel
    re_path(r'ws/callcenter/agent-desktop/$', consumers.AgentDesktopConsumer.as_asgi()),

    # Supervisor per-agent monitor channel (listen/whisper/barge indicators)
    re_path(r'ws/callcenter/monitor/(?P<agent_id>\d+)/$', consumers.AgentMonitorConsumer.as_asgi()),
]
