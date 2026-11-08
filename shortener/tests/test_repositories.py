import pytest

from shortener.repositories import RedisUrlRepository


@pytest.fixture
def repository(redis_client):
    return RedisUrlRepository(redis_client)


def test_save_and_get(repository, redis_client):
    assert repository.save_if_absent("abc1234", "https://example.com") is True

    assert repository.get("abc1234") == "https://example.com"
    assert redis_client.get("url:abc1234") == "https://example.com"


def test_save_does_not_overwrite_existing_code(repository):
    repository.save_if_absent("abc1234", "https://example.com")

    assert repository.save_if_absent("abc1234", "https://other.com") is False
    assert repository.get("abc1234") == "https://example.com"


def test_get_unknown_code_returns_none(repository):
    assert repository.get("missing") is None
