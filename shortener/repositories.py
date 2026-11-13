from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

import redis
from django.db import IntegrityError, transaction

from shortener.models import Tag, Url


class UrlRepository(Protocol):
    """Storage contract the shortener service depends on."""

    def save_if_absent(
        self,
        short_code: str,
        long_url: str,
        *,
        owner=None,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
        tags: Sequence[str] = (),
    ) -> bool: ...

    def get(self, short_code: str) -> str | None: ...


class DjangoUrlRepository:
    """Saves and reads urls in the Url table through the Django ORM."""

    def save_if_absent(
        self,
        short_code: str,
        long_url: str,
        *,
        owner=None,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
        tags: Sequence[str] = (),
    ) -> bool:
        """Creates the row; returns False when the unique constraint rejects the code."""
        try:
            with transaction.atomic():
                url = Url.objects.create(
                    short_code=short_code,
                    original_url=long_url,
                    owner=owner,
                    custom_alias=custom_alias,
                    expires_at=expires_at,
                )
                if tags:
                    url.tags.set(Tag.objects.get_or_create(name=name)[0] for name in tags)
        except IntegrityError:
            return False
        return True

    def get(self, short_code: str) -> str | None:
        """Returns the long url of an active, unexpired short code."""
        return (
            Url.objects.active_urls()
            .filter(short_code=short_code)
            .values_list("original_url", flat=True)
            .first()
        )


class RedisUrlRepository:
    """Saves and reads short code -> long url pairs in Redis."""

    KEY_PREFIX = "url:"

    def __init__(self, client: redis.Redis):
        self._client = client

    def _key(self, short_code: str) -> str:
        return f"{self.KEY_PREFIX}{short_code}"

    def save_if_absent(self, short_code: str, long_url: str, **options) -> bool:
        """Stores the pair only if the code is free; returns False on collision."""
        return bool(self._client.set(self._key(short_code), long_url, nx=True))

    def get(self, short_code: str) -> str | None:
        return self._client.get(self._key(short_code))
