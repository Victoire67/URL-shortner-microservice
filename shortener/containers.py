import redis

from dependency_injector import container, provider

from shortener.repositories import RedisUrlRepository
from shortener.services import UrlShortenerService


class Container(container.DeclarativeContainer):
    """Builds and wires the shortener's dependencies"""

    config = provider.configuration()
    redis_client = provider.singleton(
        redis.Redis.from_url,
        config.redis_url,
        decode_responses=True
  )

    url_repository = providers.Singleton(RedisUrlRepository , client = redis_client)
    url_shortner_service = provider.Singleton(UrlShortenerService , repository = url_repository)



    
