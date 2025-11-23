"""
Django settings for testing.
Simplified settings without optional dependencies like cookie_consent.
"""
from .development import *

# Remove optional apps that might not be installed
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Remove: 'cookie_consent',
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

# Remove cookie consent middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Remove: 'accounts.cookie_middleware.CookieConsentMiddleware',
]

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable password hashing for faster tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use console email backend for testing
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'

# Disable migrations for faster tests (optional)
# class DisableMigrations:
#     def __contains__(self, item):
#         return True
#     def __getitem__(self, item):
#         return None
# MIGRATION_MODULES = DisableMigrations()

# Keep debug on for tests
DEBUG = True

# Simple secret key for testing
SECRET_KEY = 'test-secret-key-for-testing-only'
