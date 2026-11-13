from datetime import timedelta

import pytest
from django.utils import timezone

from shortener.models import Url


@pytest.fixture
def urls():
    now = timezone.now()
    return {
        "no_expiry": Url.objects.create(original_url="https://a.com", short_code="a", click_count=5),
        "future": Url.objects.create(original_url="https://b.com", short_code="b", click_count=20,
                                     expires_at=now + timedelta(days=1)),
        "expired": Url.objects.create(original_url="https://c.com", short_code="c", click_count=50,
                                      expires_at=now - timedelta(days=1)),
        "inactive": Url.objects.create(original_url="https://d.com", short_code="d", click_count=10,
                                       is_active=False),
    }


@pytest.mark.django_db
def test_active_urls_excludes_expired_and_inactive(urls):
    assert set(Url.objects.active_urls()) == {urls["no_expiry"], urls["future"]}


@pytest.mark.django_db
def test_expired_urls_returns_only_expired(urls):
    assert list(Url.objects.expired_urls()) == [urls["expired"]]


@pytest.mark.django_db
def test_popular_urls_orders_by_click_count(urls):
    assert list(Url.objects.popular_urls()) == [
        urls["expired"], urls["future"], urls["inactive"], urls["no_expiry"]
    ]


@pytest.mark.django_db
def test_active_and_popular_chain(urls):
    assert list(Url.objects.active_urls().popular_urls()) == [urls["future"], urls["no_expiry"]]
