"""
Celery configuration for DialFlow Pro.
Uses Redis as broker and result backend.
"""
import os
from celery import Celery

# Set default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

app = Celery('dialflow')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Task queues configuration
app.conf.task_routes = {
    'apps.dialer_campaign.tasks.*': {'queue': 'campaigns'},
    'apps.dialer_cdr.tasks.*': {'queue': 'calls'},
    'apps.mod_sms.tasks.*': {'queue': 'sms'},
    'apps.appointment.tasks.*': {'queue': 'appointments'},
}

# Beat schedule configuration
# Note: This is the default schedule. In production, use django-celery-beat
# to manage schedules via the database for dynamic configuration.
app.conf.beat_schedule = {
    'campaign-heartbeat': {
        'task': 'dialer_campaign.campaign_running',
        'schedule': 60.0,  # Run every 60 seconds (adjustable via HEARTBEAT_MIN)
        'options': {'queue': 'campaigns'}
    },
    'sms-campaign-heartbeat': {
        'task': 'sms_campaign_running',
        'schedule': 60.0,  # Run every 60 seconds
        'options': {'queue': 'sms'}
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    """Debug task to test Celery is working."""
    print(f'Request: {self.request!r}')
