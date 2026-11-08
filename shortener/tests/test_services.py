import pytest

from shortener.exceptions import ShortCodeGenerationError, ShortCodeNotFound
from shortener.services import ALPHABET, UrlShortenerService


class InMemoryRepository:
    def __init__(self):
        self.data = {}

    def save_if_absent(self, short_code, long_url):
        if short_code in self.data:
            return False
        self.data[short_code] = long_url
        return True

    def get(self, short_code):
        return self.data.get(short_code)


class AlwaysTakenRepository(InMemoryRepository):
    def save_if_absent(self, short_code, long_url):
        return False


@pytest.fixture
def repository():
    return InMemoryRepository()


@pytest.fixture
def service(repository):
    return UrlShortenerService(repository)


def test_shorten_stores_url_under_a_new_code(service, repository):
    code = service.shorten("https://example.com")

    assert len(code) == 7
    assert set(code) <= set(ALPHABET)
    assert repository.data[code] == "https://example.com"


def test_shorten_gives_different_codes_for_each_call(service):
    assert service.shorten("https://example.com") != service.shorten("https://example.com")


def test_resolve_returns_the_long_url(service):
    code = service.shorten("https://example.com")

    assert service.resolve(code) == "https://example.com"


def test_resolve_unknown_code_raises_not_found(service):
    with pytest.raises(ShortCodeNotFound):
        service.resolve("missing")


def test_shorten_gives_up_after_max_attempts():
    service = UrlShortenerService(AlwaysTakenRepository())

    with pytest.raises(ShortCodeGenerationError):
        service.shorten("https://example.com")
