"""Development profile: debug mode on, insecure fallback secret key."""

from decouple import config as env

from .base import *  # noqa: F401,F403

DEBUG = True

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-key")


# Browsable API so the debug toolbar has an HTML page to attach to
REST_FRAMEWORK = {
    **REST_FRAMEWORK,  # noqa: F405
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
}

# Debug toolbar: only when it is installed (it comes with requirements-dev.txt)
try:
    import debug_toolbar  # noqa: F401
except ImportError:
    DEBUG_TOOLBAR = False
else:
    DEBUG_TOOLBAR = True
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(1, "debug_toolbar.middleware.DebugToolbarMiddleware")  # noqa: F405
    DEBUG_TOOLBAR_CONFIG = {"SHOW_TOOLBAR_CALLBACK": "config.settings.dev.show_toolbar"}


def show_toolbar(request):
    # Docker gives requests a gateway IP instead of 127.0.0.1, so INTERNAL_IPS
    # would never match; show the toolbar whenever DEBUG is on (tests turn it off)
    from django.conf import settings

    return settings.DEBUG
