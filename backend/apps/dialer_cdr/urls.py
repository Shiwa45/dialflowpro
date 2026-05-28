"""URL patterns for dialer_cdr"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dialer_cdr'

router = DefaultRouter()
router.register(r'callrequests', views.CallrequestViewSet, basename='callrequest')
router.register(r'voipcalls', views.VoIPCallViewSet, basename='voipcall')

urlpatterns = [
    path('', include(router.urls)),
]
