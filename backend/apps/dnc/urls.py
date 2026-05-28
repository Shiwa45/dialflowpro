"""URL patterns for DNC"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dnc'

router = DefaultRouter()
router.register(r'dnc', views.DNCViewSet, basename='dnc')
router.register(r'contacts', views.DNCContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
