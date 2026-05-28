"""
DialFlow Pro - Base Settings
All shared configuration between dev and production.
Uses django-environ for 12-factor config.
"""
from pathlib import Path
from datetime import timedelta
import environ
import json

# Build paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ROOT_DIR = BASE_DIR.parent

# Environment
env = environ.Env(
    DEBUG=(bool, False),
    ALLOWED_HOSTS=(list, []),
    USE_S3=(bool, False),
)

# Read .env file if exists
env_file = ROOT_DIR / '.env'
if env_file.exists():
    environ.Env.read_env(str(env_file))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env('DEBUG')

ALLOWED_HOSTS = env.list('ALLOWED_HOSTS')


# Application definition
# django-tenants requires SHARED_APPS + TENANT_APPS split
# SHARED_APPS: run in the public schema (tenant management, auth, admin, celery)
# TENANT_APPS: run in each tenant's own schema (all dialer apps)

SHARED_APPS = [
    'django_tenants',            # must be first
    'apps.tenants',              # Tenant + Domain models live in public schema
    # Django core (shared)
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    # Third-party shared
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    'channels',
    'django_celery_beat',
    'django_celery_results',
    'ordered_model',
    'phonenumber_field',
    'django_countries',
    # Shared local apps
    'apps.accounts',
    'apps.common',
    'apps.dialer_settings',      # Per-user dialer limits — shared schema (FK from UserProfile)
]

TENANT_APPS = [
    # Each tenant gets their own schema with these apps
    'apps.dialer_contact',
    'apps.dialer_gateway',
    'apps.dialer_campaign',
    'apps.dialer_cdr',
    'apps.dnc',
    'apps.audiofield',
    'apps.survey',
    'apps.mod_sms',
    'apps.callcenter',
]

INSTALLED_APPS = list(SHARED_APPS) + TENANT_APPS


MIDDLEWARE = [
    'apps.tenants.middleware.TenantHeaderMiddleware',
    'apps.tenants.middleware.ConditionalTenantMainMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.tenants.middleware.UserTenantMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases
DATABASES = {
    'default': env.db('DATABASE_URL', default='postgres://dialflow:dialflow@localhost:5432/dialflow')
}
DATABASES['default']['ENGINE'] = 'django_tenants.postgresql_backend'

# Tenant Configuration
TENANT_MODEL = "tenants.Tenant"
TENANT_DOMAIN_MODEL = "tenants.Domain"
PUBLIC_SCHEMA_NAME = 'public'
TENANT_CREATION_FAKES_MIGRATIONS = False

# Required by django-tenants
DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}


# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': env('JWT_SECRET_KEY', default=SECRET_KEY),
    'AUTH_HEADER_TYPES': ('Bearer',),
}


# CORS Settings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[
    'http://localhost:5173',
    'http://localhost:3000',
    'http://127.0.0.1:5173',
])
CORS_ALLOW_CREDENTIALS = True


# Channels / WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [env('REDIS_URL', default='redis://localhost:6379/0')],
        },
    },
}


# Celery Configuration
CELERY_BROKER_URL = env('CELERY_BROKER_URL', default='redis://localhost:6379/0')
CELERY_RESULT_BACKEND = env('CELERY_RESULT_BACKEND', default='redis://localhost:6379/1')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes


# FreeSWITCH Configuration
try:
    FREESWITCH_NODES = json.loads(env('FREESWITCH_NODES', default='{}'))
except json.JSONDecodeError:
    FREESWITCH_NODES = {
        'fs1': {
            'host': env('FS1_HOST', default='127.0.0.1'),
            'port': 8021,
            'password': env('FS_SECRET', default='ClueCon'),
        }
    }

FS_LUA_SCRIPT = env('FS_LUA_SCRIPT', default='/opt/dialflow/scripts/dialflow.lua')
HEARTBEAT_MIN = env.int('HEARTBEAT_MIN', default=1)
DELAY_OUTBOUND = env.int('DELAY_OUTBOUND', default=0)

# Directory where FreeSWITCH external profile gateway XMLs live.
# On native Linux:  /etc/freeswitch/sip_profiles/external
# On WSL from Win:  \\wsl.localhost\Ubuntu\etc\freeswitch\sip_profiles\external
FS_GATEWAY_CONFIG_DIR = env(
    'FS_GATEWAY_CONFIG_DIR',
    default='/etc/freeswitch/sip_profiles/external'
)
FS_SOFIA_PROFILE = env('FS_SOFIA_PROFILE', default='external')

# Directory where per-extension XML files live (for SIP registration)
FS_DIRECTORY_DIR = env(
    'FS_DIRECTORY_DIR',
    default='/etc/freeswitch/directory/default'
)

# Dialer Engine
NEWFIES_DIALER_ENGINE = 'esl'  # Reference to original


# Phone Number Configuration
PHONENUMBER_DEFAULT_REGION = 'US'
PHONENUMBER_DB_FORMAT = 'E164'


# Email Configuration
EMAIL_BACKEND = env('EMAIL_BACKEND', default='django.core.mail.backends.console.EmailBackend')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL', default='noreply@dialflow.local')
SERVER_EMAIL = env('SERVER_EMAIL', default='admin@dialflow.local')


# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': env('DJANGO_LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
