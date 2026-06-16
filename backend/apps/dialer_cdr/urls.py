"""URL patterns for dialer_cdr"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import webhooks

app_name = 'dialer_cdr'

router = DefaultRouter()
router.register(r'callrequests', views.CallrequestViewSet, basename='callrequest')
router.register(r'voipcalls', views.VoIPCallViewSet, basename='voipcall')

urlpatterns = [
    path('', include(router.urls)),
    # FreeSWITCH webhooks (called by the Lua script — no auth, tenant via body)
    path('webhook/hangup/', webhooks.hangup_webhook, name='hangup_webhook'),
    path('webhook/amd/', webhooks.amd_webhook, name='amd_webhook'),
]
