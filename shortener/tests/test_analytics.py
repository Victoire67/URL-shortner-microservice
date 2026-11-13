from datetime import date, datetime, timezone

import pytest

from shortener.models import Click, Url


def at(day, hour=12):
    return datetime(2026, 11, day, hour, tzinfo=timezone.utc)


def seed_clicks(url, rows):
    """rows: (country, referrer, clicked_at). clicked_at is set after create
    because auto_now_add ignores any value passed to create()."""
    for country, referrer, clicked_at in rows:
        click = Click.objects.create(
            url=url, ip_address="203.0.113.5", user_agent="test", country=country, referrer=referrer
        )
        Click.objects.filter(pk=click.pk).update(clicked_at=clicked_at)


@pytest.fixture
def url():
    return Url.objects.create(original_url="https://example.com", short_code="abc1234")


@pytest.fixture
def seeded(url):
    other = Url.objects.create(original_url="https://other.com", short_code="other12")
    seed_clicks(
        url,
        [
            ("Ghana", "https://t.co/", at(11, 9)),
            ("Ghana", "https://t.co/", at(11, 23)),
            ("Ghana", "https://google.com/", at(12)),
            ("Kenya", "https://t.co/", at(12)),
            ("Kenya", None, at(13, 0)),
            (None, None, at(13)),
        ],
    )
    # Clicks on another url must never leak into url.clicks metrics
    seed_clicks(other, [("France", "https://bing.com/", at(11))] * 3)
    return url


@pytest.mark.django_db
class TestPerCountry:

    def test_counts_clicks_per_country_most_first(self, seeded):
        assert list(seeded.clicks.per_country()) == [
            {"country": "Ghana", "total": 3},
            {"country": "Kenya", "total": 2},
            {"country": None, "total": 1},
        ]

    def test_covers_all_urls_when_not_filtered(self, seeded):
        totals = {row["country"]: row["total"] for row in Click.objects.per_country()}

        assert totals["France"] == 3
        assert sum(totals.values()) == 9

    def test_is_a_single_query(self, seeded, django_assert_num_queries):
        with django_assert_num_queries(1):
            list(seeded.clicks.per_country())


@pytest.mark.django_db
class TestPerDay:

    def test_counts_clicks_per_day_oldest_first(self, seeded):
        assert list(seeded.clicks.per_day()) == [
            {"day": date(2026, 11, 11), "total": 2},
            {"day": date(2026, 11, 12), "total": 2},
            {"day": date(2026, 11, 13), "total": 2},
        ]

    def test_is_a_single_query(self, seeded, django_assert_num_queries):
        with django_assert_num_queries(1):
            list(seeded.clicks.per_day())


@pytest.mark.django_db
class TestTopReferrers:

    def test_ranks_referrers_and_skips_direct_visits(self, seeded):
        assert list(seeded.clicks.top_referrers()) == [
            {"referrer": "https://t.co/", "total": 3},
            {"referrer": "https://google.com/", "total": 1},
        ]

    def test_limit_keeps_only_the_top(self, seeded):
        assert list(seeded.clicks.top_referrers(limit=1)) == [
            {"referrer": "https://t.co/", "total": 3},
        ]

    def test_is_a_single_query(self, seeded, django_assert_num_queries):
        with django_assert_num_queries(1):
            list(seeded.clicks.top_referrers())


@pytest.mark.django_db
def test_metrics_are_empty_without_clicks(url):
    assert list(url.clicks.per_country()) == []
    assert list(url.clicks.per_day()) == []
    assert list(url.clicks.top_referrers()) == []
