"""CallCenter app configuration"""
from django.apps import AppConfig


class CallCenterConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.callcenter'
    verbose_name = 'Call Center'

    def ready(self):
        # Register post_save broadcasting signals.
        from . import signals  # noqa: F401
