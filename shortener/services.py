import secrets
from shortener.exceptions import ShortCodeGenerationError, ShortCodeNotFound
import string

ALPHABET = string.ascii_letters + string.digits


class UrlShortenerService:
    """Creates short codes long urls and resolve them back."""

    MAX_ATTEMPTS = 5

    def __init__(self, repository, code_length: int = 7):
        self._repository = repository
        self._code_length = code_length

    def _generate_code(self) -> str:
        return "".join(secrets.choice(ALPHABET) for _ in range(self._code_length))

    def shorten(self, long_url: str) -> str:
        """Stores the url under a new unique short code and return the code"""
        for _ in range(self.MAX_ATTEMPTS):
            short_code = self._generate_code()
            print(short_code)
            if self._repository.save_if_absent(short_code, long_url):
                return short_code

        raise  ShortCodeGenerationError("Could not generate  a unique short code.")

    def resolve(self , short_code) -> str : 
        """Returns the long url when given the short code"""

        long_url = self._repository.get(short_code)
        if long_url is None : 
            raise ShortCodeNotFound(f"Short code '{short_code}' was not found.")
        return long_url


    