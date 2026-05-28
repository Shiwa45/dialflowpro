"""URL patterns for SMS"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'mod_sms'

router = DefaultRouter()
router.register(r'gateways', views.SmsGatewayViewSet, basename='gateway')
router.register(r'messages', views.SmsMessageViewSet, basename='message')
router.register(r'campaigns', views.SmsCampaignViewSet, basename='campaign')

urlpatterns = [
    path('', include(router.urls)),
]
