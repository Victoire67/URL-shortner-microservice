from django.apps import AppConfig
from django.conf import settings


class ShortenerConfig(AppConfig):
    name = "shortener"

    def ready(self):
        """Builds the DI container once at startup and wires it into the views."""
        from shortener.containers import Container

        self.container = Container()
        self.container.config.redis_url.from_value(settings.REDIS_URL)
        self.container.wire(modules=["shortener.views"])
