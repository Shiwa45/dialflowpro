"""
Development Settings
"""
from .base import *  # noqa

DEBUG = True

ALLOWED_HOSTS = ['*']

# Ensure Daphne runs when using manage.py runserver
INSTALLED_APPS = ['daphne'] + INSTALLED_APPS

# Security (relaxed for development)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS and CSRF
CORS_ALLOW_ALL_ORIGINS = True
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000',
    'http://127.0.0.1:3000',
    'http://localhost:5173',
    'http://127.0.0.1:5173',
]

# REST Framework (add Browsable API for development)
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
    'rest_framework.renderers.BrowsableAPIRenderer',
]

# Email (console backend for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Celery — use solo pool on Windows (prefork/billiard semaphores fail on Win)
CELERY_TASK_ALWAYS_EAGER = env.bool('CELERY_TASK_ALWAYS_EAGER', default=False)
CELERY_TASK_EAGER_PROPAGATES = True
CELERY_WORKER_POOL = 'solo'

# Debug Toolbar (optional)
if env.bool('USE_DEBUG_TOOLBAR', default=False):
    INSTALLED_APPS += ['debug_toolbar']
    MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
    INTERNAL_IPS = ['127.0.0.1', 'localhost']

# Logging (more verbose in development)
LOGGING['root']['level'] = 'DEBUG'
LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['apps'] = {
    'handlers': ['console'],
    'level': 'DEBUG',
    'propagate': False,
}
# Silence SQL query logging — too noisy (Celery Beat polls DB every 5 s)
LOGGING['loggers']['django.db.backends'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
# Silence Daphne's per-frame WebSocket debug logs (heartbeat noise)
LOGGING['loggers']['daphne'] = {
    'handlers': ['console'],
    'level': 'WARNING',
    'propagate': False,
}
