"""URL patterns for audiofield"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'audiofield'

router = DefaultRouter()
router.register(r'audio', views.AudioFileViewSet, basename='audiofile')

urlpatterns = [
    path('', include(router.urls)),
]
