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

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '0.0.0.0', '192.168.1.12', '192.168.1.3']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'ltcboxoffice'),
        'USER': os.environ.get('DB_USER', 'djangodbuser'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'aSdF!234'),
        'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
        'PORT': os.environ.get('DB_PORT', '3306'),
    }
}

# Email Configuration (Development)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
EMAIL_PORT = 2525
EMAIL_HOST_USER = '460a4a880078c8'
EMAIL_HOST_PASSWORD = '1d58de165e2dde'
EMAIL_USE_TLS = True

# Debug toolbar (optional - install django-debug-toolbar)
# INSTALLED_APPS += ['debug_toolbar']
# MIDDLEWARE += ['debug_toolbar.middleware.DebugToolbarMiddleware']
# INTERNAL_IPS = ['127.0.0.1']

# Development-specific settings
CORS_ALLOW_ALL_ORIGINS = True  # Only for development

# Printer Configuration - Development (Emulation Mode)
PRINTER_TYPE = 'dummy'  # Use dummy printer for development (shows emulated output)
