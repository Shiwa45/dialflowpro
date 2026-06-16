"""
WebSocket routing for callcenter app.
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/callcenter/agents/$', consumers.AgentStatusConsumer.as_asgi()),
    re_path(r'ws/callcenter/queues/(?P<queue_id>\d+)/$', consumers.QueueStatusConsumer.as_asgi()),
    re_path(r'ws/callcenter/dashboard/$', consumers.LiveDashboardConsumer.as_asgi()),
    re_path(r'ws/callcenter/monitor/(?P<agent_id>\d+)/$', consumers.AgentMonitorConsumer.as_asgi()),
]
