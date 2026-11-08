"""Gunicorn settings used by the production image."""

import multiprocessing

from decouple import config as env

bind = "0.0.0.0:8000"

# Production profile: one worker per core plus headroom
workers = env("GUNICORN_WORKERS", default=multiprocessing.cpu_count() * 2 + 1, cast=int)

# Requests are logged by the Django middleware, so only errors go here
errorlog = "-"
loglevel = env("LOG_LEVEL", default="info").lower()
