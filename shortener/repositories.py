from typing import Protocol

import redis


class UrlRepository(Protocol):
    """Storage contract the shortener service depends on."""

    def save_if_absent(self, short_code: str, long_url: str) -> bool: ...

    def get(self, short_code: str) -> str | None: ...


class RedisUrlRepository:
    """Saves and reads short code -> long url pairs in Redis."""

    KEY_PREFIX = "url:"

    def __init__(self, client: redis.Redis):
        self._client = client

    def _key(self, short_code: str) -> str:
        return f"{self.KEY_PREFIX}{short_code}"

    def save_if_absent(self, short_code: str, long_url: str) -> bool:
        """Stores the pair only if the code is free; returns False on collision."""
        return bool(self._client.set(self._key(short_code), long_url, nx=True))

    def get(self, short_code: str) -> str | None:
        return self._client.get(self._key(short_code))
