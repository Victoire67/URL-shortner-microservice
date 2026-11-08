import redis
from dependency_injector import containers, providers

from shortener.repositories import RedisUrlRepository
from shortener.services import UrlShortenerService


class Container(containers.DeclarativeContainer):
    """Builds and wires the shortener's dependencies."""

    config = providers.Configuration()

    redis_client = providers.Singleton(
        redis.Redis.from_url,
        config.redis_url,
        decode_responses=True,
    )

    url_repository = providers.Singleton(RedisUrlRepository, client=redis_client)

    url_shortener_service = providers.Singleton(UrlShortenerService, repository=url_repository)
