import pytest

from shortener.exceptions import CustomAliasTaken, ShortCodeGenerationError, ShortCodeNotFound
from shortener.domain import Visit
from shortener.services import ALPHABET, UrlShortenerService


class InMemoryRepository:
    def __init__(self):
        self.data = {}
        self.options = {}
        self.clicks = []

    def save_if_absent(self, short_code, long_url, **options):
        if short_code in self.data:
            return False
        self.data[short_code] = long_url
        self.options[short_code] = options
        return True

    def get(self, short_code):
        return self.data.get(short_code)

    def record_click(self, short_code, visit):
        self.clicks.append((short_code, visit))


class AlwaysTakenRepository(InMemoryRepository):
    def save_if_absent(self, short_code, long_url, **options):
        return False


class AliasTakenRepository(InMemoryRepository):
    def __init__(self):
        super().__init__()
        self.attempts = 0

    def save_if_absent(self, short_code, long_url, **options):
        self.attempts += 1
        raise CustomAliasTaken()


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


def test_shorten_passes_url_options_to_the_repository(service, repository):
    code = service.shorten(
        "https://example.com",
        owner="ana",
        custom_alias="docs",
        expires_at=None,
        tags=["Work"],
        title="Docs",
        description="Project docs",
    )

    assert repository.options[code] == {
        "owner": "ana",
        "custom_alias": "docs",
        "expires_at": None,
        "tags": ["Work"],
        "title": "Docs",
        "description": "Project docs",
    }


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


def test_shorten_stops_at_once_when_custom_alias_is_taken():
    repository = AliasTakenRepository()
    service = UrlShortenerService(repository)

    with pytest.raises(CustomAliasTaken):
        service.shorten("https://example.com", custom_alias="docs")
    assert repository.attempts == 1


def test_resolve_records_the_visit(service, repository):
    code = service.shorten("https://example.com")
    visit = Visit(ip_address="203.0.113.5", user_agent="Mozilla/5.0", referrer="https://t.co/x")

    service.resolve(code, visit)

    assert repository.clicks == [(code, visit)]


def test_resolve_without_visit_records_nothing(service, repository):
    code = service.shorten("https://example.com")

    service.resolve(code)

    assert repository.clicks == []


def test_resolve_unknown_code_records_nothing(service, repository):
    with pytest.raises(ShortCodeNotFound):
        service.resolve("missing", Visit(ip_address="203.0.113.5"))

    assert repository.clicks == []
