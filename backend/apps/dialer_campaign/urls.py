"""URL patterns for dialer_campaign"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dialer_campaign'

router = DefaultRouter()
router.register(r'campaigns', views.CampaignViewSet, basename='campaign')
router.register(r'subscribers', views.SubscriberViewSet, basename='subscriber')

urlpatterns = [
    path('', include(router.urls)),
]
