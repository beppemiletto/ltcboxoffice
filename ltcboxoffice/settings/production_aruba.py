"""
Production settings per il server Aruba (80.88.90.77).
Usa SQLite invece di MySQL e cache locale invece di Redis.
"""
import os
from .production import *

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'prenota.teatrocambiano.com').split(',')

# Database SQLite — il file vive fuori dalla cartella di deploy
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.environ.get('DB_PATH', '/var/lib/ltcboxoffice/db.sqlite3'),
    }
}

# Cache locale (niente Redis)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

# File media fuori dalla cartella di deploy
MEDIA_ROOT = os.environ.get('MEDIA_ROOT', '/var/lib/ltcboxoffice/media')
