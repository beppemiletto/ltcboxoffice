"""
Development settings for ltcboxoffice project.
"""
import os
from .base import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get(
    'SECRET_KEY',
    'django-insecure-410%jpm^odm^!zj7*3u5^v@ae=p!-4#p0&#cw)k%eu5fj9$te0'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# In development, permetti tutti gli host (inclusi ngrok dinamici)
# ATTENZIONE: Usare SOLO in development!
ALLOWED_HOSTS = ['*']

# Aggiungi middleware per ngrok (SOLO in development) - per CSRF
MIDDLEWARE = [
    'ltcboxoffice.middleware.NgrokMiddleware',  # Per gestire CSRF_TRUSTED_ORIGINS
] + MIDDLEWARE  # MIDDLEWARE viene da base.py

# Database
# Use ltcboxoffice_dev by default for development
# Override with DB_NAME environment variable if needed
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ltcboxoffice'),  # Changed back to production DB
        'USER': os.environ.get('DB_USER', 'djangodbuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'aSdF!234'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

# Email Configuration (Development)
# Option 1: Console backend (prints emails to console)
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Option 2: SMTP with imitate.email using custom backend (bypasses SSL verification)
EMAIL_BACKEND = 'ltcboxoffice.email_backend.UnverifiedSSLEmailBackend'
EMAIL_HOST = 'smtp.imitate.email'
EMAIL_PORT = 465
EMAIL_HOST_USER = 'W9z83PN9fEuMJQGatmkGjQ'
EMAIL_HOST_PASSWORD = 'IXmTJGg7XBY0G3GFtkpA'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True  # Custom backend will use unverified SSL context
EMAIL_TIMEOUT = 10  # Timeout in seconds

# Debug toolbar (optional - install django-debug-toolbar)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Development-specific settings
CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Printer Configuration - Development (Emulation Mode)
PRINTER_TYPE = 'dummy'  # Use dummy printer for development (shows emulated output)


# Per CSRF - ngrok origins vengono aggiunti dinamicamente dal middleware
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    # ngrok URLs vengono aggiunti automaticamente dal NgrokMiddleware
]