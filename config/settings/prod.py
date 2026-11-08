"""Production profile: debug off, secret key required, hardened headers."""

from decouple import config as env

from .base import *  # noqa: F401,F403

DEBUG = False

# No default: the app refuses to start without a real secret key
SECRET_KEY = env("SECRET_KEY")

SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
