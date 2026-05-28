"""
WebSocket URL routing for Django Channels.
All WebSocket paths are defined here.
"""
from django.urls import path
from apps.callcenter.routing import websocket_urlpatterns as callcenter_ws

# WebSocket URL patterns
websocket_urlpatterns = [
    # Call center real-time updates
    *callcenter_ws,
    
    # Future WebSocket consumers will be added here
]
