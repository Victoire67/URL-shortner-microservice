from collections.abc import Sequence
from datetime import datetime
from typing import Protocol

import redis
from django.db import IntegrityError, transaction
from django.db.models import F

from shortener.domain import Visit
from shortener.exceptions import CustomAliasTaken
from shortener.models import Click, Tag, Url


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
        title: str = "",
        description: str = "",
    ) -> bool:
        """Saves the url; returns False if the short code is taken.

        Raises CustomAliasTaken if the custom alias is already used.
        """
        ...

    def get(self, short_code: str) -> str | None: ...

    def record_click(self, short_code: str, visit: Visit) -> None:
        """Saves one visit and adds 1 to the url's click count."""
        ...


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
        title: str = "",
        description: str = "",
    ) -> bool:
        """Creates the row; the unique constraints decide whether the code or alias is free."""
        try:
            with transaction.atomic():
                url = Url.objects.create(
                    short_code=short_code,
                    original_url=long_url,
                    owner=owner,
                    custom_alias=custom_alias,
                    expires_at=expires_at,
                    title=title,
                    description=description,
                )
                if tags:
                    url.tags.set(Tag.objects.get_or_create(name=name)[0] for name in tags)
        except IntegrityError:
            if custom_alias and Url.objects.filter(custom_alias=custom_alias).exists():
                raise CustomAliasTaken(f"Custom alias '{custom_alias}' is already taken.")
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

    def record_click(self, short_code: str, visit: Visit) -> None:
        """Saves a Click and increments click_count in one transaction.

        F("click_count") + 1 makes Postgres do the addition itself, so
        simultaneous visits can never overwrite each other's count.
        """
        url_id = Url.objects.filter(short_code=short_code).values_list("pk", flat=True).first()
        if url_id is None:
            return
        with transaction.atomic():
            Click.objects.create(
                url_id=url_id,
                ip_address=visit.ip_address,
                user_agent=visit.user_agent,
                referrer=visit.referrer,
            )
            Url.objects.filter(pk=url_id).update(click_count=F("click_count") + 1)


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
