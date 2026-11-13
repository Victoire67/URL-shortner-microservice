import redis
from dependency_injector import containers, providers

from shortener.repositories import DjangoUrlRepository
from shortener.services import UrlShortenerService


class Container(containers.DeclarativeContainer):
    """Builds and wires the shortener's dependencies."""

    config = providers.Configuration()

    # Kept for the upcoming cache layer; urls are stored in Postgres
    redis_client = providers.Singleton(
        redis.Redis.from_url,
        config.redis_url,
        decode_responses=True,
    )

    url_repository = providers.Singleton(DjangoUrlRepository)

    url_shortener_service = providers.Singleton(UrlShortenerService, repository=url_repository)
