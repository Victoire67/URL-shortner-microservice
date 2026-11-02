from .base import *  # noqa: F401,F403

DEBUG = False

# Extra security headers for production
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
