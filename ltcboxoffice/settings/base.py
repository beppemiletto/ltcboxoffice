"""
Base Django settings for ltcboxoffice project.
Common settings shared across all environments.
"""
import os
from pathlib import Path

try:
    from celery.schedules import crontab
except ImportError:
    crontab = None

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cookie_consent',
    'billboard',
    'accounts',
    'store',
    'hall',
    'carts',
    'orders',
    'tickets',
    'boxoffice',
    'fiscalmgm',
    'booking',
    'history',
    'subscriptions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'accounts.cookie_middleware.CookieConsentMiddleware',
]

COOKIE_CONSENT_NAME = "cookie_consent"

ROOT_URLCONF = 'ltcboxoffice.urls'

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
                'billboard.context_processors.menu_links',
                'carts.context_processors.counter',
            ],
        },
    },
]

WSGI_APPLICATION = 'ltcboxoffice.wsgi.application'

AUTH_USER_MODEL = 'accounts.Account'

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'it-it'
TIME_ZONE = 'Europe/Rome'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'ltcboxoffice' / 'static',
    BASE_DIR / 'static',  # For dynamically generated files like barcodes
]

# Media files configurations
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Event CSV files HALL STATUS configurations
HALL_STATUS_FILES_ROOT = BASE_DIR / 'hall_jsons'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Message tags
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: "danger",
}

# Session configuration
SESSION_COOKIE_AGE = 3600  # 60 minutes
SESSION_SAVE_EVERY_REQUEST = True  # Users are logged out if inactive
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # Set to True in production with HTTPS

# Celery Configuration
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379')
CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379')
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/Rome'

if crontab is not None:
    CELERY_BEAT_SCHEDULE = {
        'task-number-one': {
            'task': 'tickets.tasks.scheduledTask',
            'schedule': crontab(minute='*/5')
        },
        # NOTA: Celery non compatibile con Python 3.13 - usare cron + comando management
        # 'cleanup-abandoned-carts': {
        #     'task': 'boxoffice.cleanup_abandoned_carts',
        #     'schedule': crontab(minute='*/15'),
        #     'kwargs': {'timeout_minutes': 15},
        # },
    }
else:
    CELERY_BEAT_SCHEDULE = {}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Printer Configuration - Default values (override in environment-specific settings)
PRINTER_TYPE = 'dummy'  # Options: 'usb', 'network', 'dummy'

# USB Printer Settings (for environments that need it)
PRINTER_USB_VENDOR = 0x0483
PRINTER_USB_PRODUCT = 0x5840
PRINTER_USB_TIMEOUT = 0
PRINTER_USB_IN_EP = 0x81
PRINTER_USB_OUT_EP = 0x03

# Network Printer Settings (override in production.py)
PRINTER_NETWORK_HOST = '192.168.1.100'
PRINTER_NETWORK_PORT = 9100
PRINTER_NETWORK_TIMEOUT = 60
