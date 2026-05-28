"""Dialer Gateway app configuration"""
from django.apps import AppConfig


class DialerGatewayConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dialer_gateway'
    verbose_name = 'Dialer Gateway'
