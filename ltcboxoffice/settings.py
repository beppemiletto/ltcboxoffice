"""
DEPRECATED: This file is kept for backward compatibility only.
The settings have been reorganized into the settings/ directory.

Please use environment-based settings by setting DJANGO_ENV:
- development (default)
- staging
- production

All new configuration should be done in the appropriate settings file.
"""

# Import all settings from the new structure
from .settings import *  # noqa: F401, F403

import warnings
warnings.warn(
    "Importing from ltcboxoffice.settings is deprecated. "
    "The settings have been reorganized into ltcboxoffice.settings module. "
    "Please update your DJANGO_SETTINGS_MODULE if needed.",
    DeprecationWarning,
    stacklevel=2
)
