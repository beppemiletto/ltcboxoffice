"""
Django settings module selector.
Loads the appropriate settings based on DJANGO_ENV environment variable.
"""
import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
elif env == 'staging':
    from .staging import *
else:
    from .development import *
