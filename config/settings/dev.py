"""Development profile: debug mode on, insecure fallback secret key."""

from decouple import config as env

from .base import *  # noqa: F401,F403

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-key")
