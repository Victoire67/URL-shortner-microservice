import logging
import secrets
import string
from collections.abc import Sequence
from datetime import datetime

from shortener.exceptions import ShortCodeGenerationError, ShortCodeNotFound
from shortener.repositories import UrlRepository

logger = logging.getLogger(__name__)

ALPHABET = string.ascii_letters + string.digits


class UrlShortenerService:
    """Creates short codes for long urls and resolves them back."""

    MAX_ATTEMPTS = 5

    def __init__(self, repository: UrlRepository, code_length: int = 7):
        self._repository = repository
        self._code_length = code_length

    def _generate_code(self) -> str:
        return "".join(secrets.choice(ALPHABET) for _ in range(self._code_length))

    def shorten(
        self,
        long_url: str,
        *,
        owner=None,
        custom_alias: str | None = None,
        expires_at: datetime | None = None,
        tags: Sequence[str] = (),
        title: str = "",
        description: str = "",
    ) -> str:
        """Stores the url under a new unique short code and returns the code."""
        for _ in range(self.MAX_ATTEMPTS):
            short_code = self._generate_code()
            saved = self._repository.save_if_absent(
                short_code,
                long_url,
                owner=owner,
                custom_alias=custom_alias,
                expires_at=expires_at,
                tags=tags,
                title=title,
                description=description,
            )
            if saved:
                logger.info("Created short code %s", short_code)
                return short_code
            logger.warning("Short code collision on %s, retrying", short_code)

        raise ShortCodeGenerationError("Could not generate a unique short code.")

    def resolve(self, short_code: str) -> str:
        """Returns the long url stored under the short code."""
        long_url = self._repository.get(short_code)
        if long_url is None:
            raise ShortCodeNotFound(f"Short code '{short_code}' was not found.")
        return long_url
