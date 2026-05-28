"""AudioField app configuration"""
from django.apps import AppConfig


class AudioFieldConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.audiofield'
    verbose_name = 'Audio Files'
