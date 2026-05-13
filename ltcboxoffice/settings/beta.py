"""
Beta testing settings for ltcboxoffice project.
- Inherits from staging (WhiteNoise, DEBUG=True, no SSL redirect)
- Uses production email server (real emails delivered)
- ALLOWED_HOSTS and DB configurable via env vars
- Printer in emulation mode (dummy)
"""
import os
from .staging import *

# Beta-specific SECRET_KEY with fallback (staging inherits production which raises if missing)
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-beta-410%jpm^odm^!zj7*3u5^v@ae=p!-4#p0&#cw)k%eu5fj9$te0'
)

# Allow beta host IPs/domains via env var, fallback to local
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

# Add beta origins to CSRF trusted origins
CSRF_TRUSTED_ORIGINS = [
    f'http://{host}' for host in ALLOWED_HOSTS if host not in ('*',)
] + [
    f'https://{host}' for host in ALLOWED_HOSTS if host not in ('*',)
]

# Database — reuse development DB defaults so no extra env vars needed for local beta
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ltcboxoffice'),
        'USER': os.environ.get('DB_USER', 'djangodbuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'aSdF!234'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            'charset': 'utf8mb4',
        },
    }
}

# Production email server — real emails delivered
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'ltcboxoffice@teatrocambiano.com')

# Printer in emulation mode for beta
PRINTER_TYPE = 'dummy'

# No Redis needed for beta — use local memory cache
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}
