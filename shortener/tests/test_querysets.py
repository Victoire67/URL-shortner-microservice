from datetime import timedelta

import pytest
from django.utils import timezone

from shortener.models import Url
from shortener.tests.factories import UrlFactory


@pytest.fixture
def urls():
    now = timezone.now()
    return {
        "no_expiry": UrlFactory(click_count=5),
        "future": UrlFactory(click_count=20, expires_at=now + timedelta(days=1)),
        "expired": UrlFactory(click_count=50, expires_at=now - timedelta(days=1)),
        "inactive": UrlFactory(click_count=10, is_active=False),
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
