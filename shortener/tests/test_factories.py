from datetime import datetime, timezone

import pytest

from shortener.models import Click, Tag, Url
from shortener.tests.factories import ClickFactory, TagFactory, UrlFactory, UserFactory


@pytest.mark.django_db
class TestFactories:

    def test_user_factory_saves_a_user_with_a_usable_password(self):
        user = UserFactory()

        assert user.pk is not None
        assert user.email == f"{user.username}@example.com"
        assert user.check_password("password")

    def test_tag_factory_reuses_seeded_tags(self):
        assert TagFactory(name="Work") == Tag.objects.get(name="Work")
        assert Tag.objects.filter(name="Work").count() == 1

    def test_url_factory_gives_unique_codes_and_optional_tags(self):
        first, second = UrlFactory(), UrlFactory(tags=["Work", "Brand new"])

        assert first.short_code != second.short_code
        assert first.owner is None
        assert set(second.tags.values_list("name", flat=True)) == {"Work", "Brand new"}
        assert Url.objects.active_urls().count() == 2

    def test_click_factory_can_set_clicked_at(self):
        when = datetime(2026, 1, 1, tzinfo=timezone.utc)

        click = ClickFactory(clicked_at=when)

        assert Click.objects.get(pk=click.pk).clicked_at == when
        assert click.url.clicks.count() == 1
