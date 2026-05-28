"""Dialer CDR app configuration"""
from django.apps import AppConfig


class DialerCdrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.dialer_cdr'
    verbose_name = 'Dialer CDR'
