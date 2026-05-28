"""
URL patterns for dialer_settings app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dialer_settings'

router = DefaultRouter()
router.register(r'settings', views.DialerSettingViewSet, basename='dialersetting')

urlpatterns = [
    path('', include(router.urls)),
]
