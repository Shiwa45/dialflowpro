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
# Patterns match against the task NAME (the name= kwarg in @shared_task),
# not the Python module path — so use the actual registered task names.
app.conf.task_routes = {
    'dialer_campaign.*':  {'queue': 'campaigns'},
    'dialer_cdr.*':       {'queue': 'calls'},
    'sms_campaign_*':     {'queue': 'sms'},
    'sms_send_*':         {'queue': 'sms'},
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
