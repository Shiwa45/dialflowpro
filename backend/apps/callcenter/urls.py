"""URL patterns for callcenter"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'callcenter'

router = DefaultRouter()
router.register(r'queues', views.QueueViewSet, basename='queue')
router.register(r'agents', views.AgentViewSet, basename='agent')
router.register(r'tiers', views.TierViewSet, basename='tier')
router.register(r'members', views.QueueMemberViewSet, basename='member')

urlpatterns = [
    path('', include(router.urls)),
]
