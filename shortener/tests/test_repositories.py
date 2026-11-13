from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from shortener.models import Url
from shortener.repositories import DjangoUrlRepository, RedisUrlRepository


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

    def test_save_rejects_taken_custom_alias(self, repository):
        repository.save_if_absent("abc1234", "https://example.com", custom_alias="docs")

        assert repository.save_if_absent("xyz9876", "https://other.com", custom_alias="docs") is False
        assert not Url.objects.filter(short_code="xyz9876").exists()

    def test_save_stores_owner_expiry_and_tags(self, repository):
        owner = get_user_model().objects.create_user(username="ana", email="ana@example.com")
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
