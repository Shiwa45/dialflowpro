"""URL patterns for dialer_gateway"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dialer_gateway'

router = DefaultRouter()
router.register(r'gateways', views.GatewayViewSet, basename='gateway')

urlpatterns = [
    path('', include(router.urls)),
]
