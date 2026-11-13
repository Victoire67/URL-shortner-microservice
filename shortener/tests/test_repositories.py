from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import pytest
from django.db import connection
from django.utils import timezone

from shortener.domain import Visit
from shortener.exceptions import CustomAliasTaken
from shortener.models import Click, Url
from shortener.repositories import DjangoUrlRepository, RedisUrlRepository
from shortener.tests.factories import UserFactory


@pytest.mark.django_db
class TestDjangoUrlRepository:

    @pytest.fixture
    def repository(self):
        return DjangoUrlRepository()

    def test_save_and_get(self, repository):
        assert repository.save_if_absent("abc1234", "https://example.com") is True

        assert repository.get("abc1234") == "https://example.com"
        assert Url.objects.get(short_code="abc1234").original_url == "https://example.com"

    def test_save_does_not_overwrite_existing_code(self, repository):
        repository.save_if_absent("abc1234", "https://example.com")

        assert repository.save_if_absent("abc1234", "https://other.com") is False
        assert repository.get("abc1234") == "https://example.com"

    def test_save_raises_when_custom_alias_is_taken(self, repository):
        repository.save_if_absent("abc1234", "https://example.com", custom_alias="docs")

        with pytest.raises(CustomAliasTaken):
            repository.save_if_absent("xyz9876", "https://other.com", custom_alias="docs")
        assert not Url.objects.filter(short_code="xyz9876").exists()

    def test_taken_code_with_free_alias_returns_false(self, repository):
        repository.save_if_absent("abc1234", "https://example.com")

        assert repository.save_if_absent("abc1234", "https://other.com", custom_alias="docs") is False

    def test_save_stores_owner_expiry_and_tags(self, repository):
        owner = UserFactory()
        expires_at = timezone.now() + timedelta(days=1)

        repository.save_if_absent(
            "abc1234",
            "https://example.com",
            owner=owner,
            custom_alias="docs",
            expires_at=expires_at,
            tags=["Work", "Social"],
        )

        url = Url.objects.get(short_code="abc1234")
        assert url.owner == owner
        assert url.custom_alias == "docs"
        assert url.expires_at == expires_at
        assert set(url.tags.values_list("name", flat=True)) == {"Work", "Social"}

    def test_get_unknown_code_returns_none(self, repository):
        assert repository.get("missing") is None

    def test_get_ignores_expired_and_inactive_urls(self, repository):
        repository.save_if_absent(
            "expired", "https://example.com", expires_at=timezone.now() - timedelta(days=1)
        )
        repository.save_if_absent("inactive", "https://example.com")
        Url.objects.filter(short_code="inactive").update(is_active=False)

        assert repository.get("expired") is None
        assert repository.get("inactive") is None


    def test_record_click_saves_click_and_increments_count(self, repository):
        repository.save_if_absent("abc1234", "https://example.com")
        visit = Visit(ip_address="203.0.113.5", user_agent="Mozilla/5.0", referrer="https://t.co/x")

        repository.record_click("abc1234", visit)

        url = Url.objects.get(short_code="abc1234")
        assert url.click_count == 1
        click = url.clicks.get()
        assert click.ip_address == "203.0.113.5"
        assert click.user_agent == "Mozilla/5.0"
        assert click.referrer == "https://t.co/x"

    def test_record_click_on_unknown_code_does_nothing(self, repository):
        repository.record_click("missing", Visit(ip_address="203.0.113.5"))

        assert Click.objects.count() == 0


@pytest.mark.django_db(transaction=True)
def test_click_count_is_correct_under_concurrent_visits():
    """20 visits at the same time must give click_count == 20 (no lost updates)."""
    repository = DjangoUrlRepository()
    repository.save_if_absent("abc1234", "https://example.com")
    visits = 20

    def visit(_):
        try:
            repository.record_click("abc1234", Visit(ip_address="203.0.113.5"))
        finally:
            connection.close()  # each thread opens its own database connection

    with ThreadPoolExecutor(max_workers=10) as pool:
        list(pool.map(visit, range(visits)))

    url = Url.objects.get(short_code="abc1234")
    assert url.click_count == visits
    assert url.clicks.count() == visits


class TestRedisUrlRepository:

    @pytest.fixture
    def repository(self, redis_client):
        return RedisUrlRepository(redis_client)

    def test_save_and_get(self, repository, redis_client):
        assert repository.save_if_absent("abc1234", "https://example.com") is True

        assert repository.get("abc1234") == "https://example.com"
        assert redis_client.get("url:abc1234") == "https://example.com"

    def test_save_does_not_overwrite_existing_code(self, repository):
        repository.save_if_absent("abc1234", "https://example.com")

        assert repository.save_if_absent("abc1234", "https://other.com") is False
        assert repository.get("abc1234") == "https://example.com"
