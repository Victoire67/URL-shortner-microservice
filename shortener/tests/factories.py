"""Test data builders. Each factory saves a valid row with sensible defaults;
pass only the fields a test cares about, e.g. UrlFactory(is_active=False)."""

import factory
from django.conf import settings

from shortener.models import Click, Tag, Url


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = settings.AUTH_USER_MODEL
        django_get_or_create = ("username",)

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda user: f"{user.username}@example.com")
    password = factory.django.Password("password")


class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag
        # The seed migration already creates Marketing, Social, Personal and Work
        django_get_or_create = ("name",)

    name = factory.Sequence(lambda n: f"tag{n}")


class UrlFactory(factory.django.DjangoModelFactory):
    """An anonymous, active url that never expires. Use owner=..., tags=[...] to add more."""

    class Meta:
        model = Url
        skip_postgeneration_save = True  # the tags hook saves through tags.set()

    original_url = factory.Sequence(lambda n: f"https://example.com/page/{n}")
    short_code = factory.Sequence(lambda n: f"code{n}")

    @factory.post_generation
    def tags(self, create, names, **kwargs):
        """UrlFactory(tags=["Work", "Social"]) attaches tags by name."""
        if create and names:
            self.tags.set(TagFactory(name=name) for name in names)


class ClickFactory(factory.django.DjangoModelFactory):
    """A click on a new url. ClickFactory(clicked_at=...) also sets the time."""

    class Meta:
        model = Click

    url = factory.SubFactory(UrlFactory)
    ip_address = "203.0.113.5"
    user_agent = "Mozilla/5.0"
    country = None
    referrer = None

    @classmethod
    def _create(cls, model_class, *args, clicked_at=None, **kwargs):
        click = super()._create(model_class, *args, **kwargs)
        if clicked_at is not None:
            # auto_now_add ignores values passed to create(), so set it afterwards
            model_class.objects.filter(pk=click.pk).update(clicked_at=clicked_at)
            click.clicked_at = clicked_at
        return click
