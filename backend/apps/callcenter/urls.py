"""URL patterns for callcenter"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .monitor_views import MonitorViewSet

app_name = 'callcenter'

router = DefaultRouter()
router.register(r'queues', views.QueueViewSet, basename='queue')
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'tiers', views.TierViewSet, basename='tier')
router.register(r'members', views.QueueMemberViewSet, basename='member')
router.register(r'monitor', MonitorViewSet, basename='monitor')

urlpatterns = [
    path('', include(router.urls)),
    # FreeSWITCH webhooks — called by the Lua script
    path('route-call/', views.route_call, name='route_call'),
    path('call-answered/', views.agent_call_event, name='agent_call_event'),
]
