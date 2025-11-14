"""
Staging settings for ltcboxoffice project.
Inherits from production but with debug enabled for testing.
"""
from .production import *

DEBUG = True

# Less strict security for staging
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Email to console in staging
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
