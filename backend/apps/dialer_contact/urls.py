"""URL patterns for dialer_contact app"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'dialer_contact'

router = DefaultRouter()
router.register(r'phonebooks', views.PhonebookViewSet, basename='phonebook')
router.register(r'contacts', views.ContactViewSet, basename='contact')

urlpatterns = [
    path('', include(router.urls)),
]
