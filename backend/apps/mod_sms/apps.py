"""SMS app configuration"""
from django.apps import AppConfig


class ModSmsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.mod_sms'
    verbose_name = 'SMS'
