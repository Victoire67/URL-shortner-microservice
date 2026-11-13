from django.conf import settings
from django.db import models
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name


class URLQuerySet(models.QuerySet):

    def active_urls(self):
        return self.filter(is_active=True).filter(
            Q(expires_at__isnull=True) | Q(expires_at__gt=timezone.now())
        )

    def expired_urls(self):
        return self.filter(expires_at__lt=timezone.now())

    def popular_urls(self):
        return self.order_by("-click_count")


class Url(models.Model):

    objects = URLQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["short_code"]),
            models.Index(fields=["created_at"]),
        ]

    original_url = models.URLField(max_length=2048)
    short_code = models.CharField(max_length=10, unique=True)
    custom_alias = models.CharField(
        max_length=50, unique=True, null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="urls",
        null=True,
        blank=True,
    )
    tags = models.ManyToManyField(Tag, related_name="urls", blank=True)
    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    favicon = models.URLField(max_length=2048, blank=True)
    click_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.short_code} -> {self.original_url}"


class ClickQuerySet(models.QuerySet):
    """Click analytics. Each method runs as one GROUP BY query in Postgres."""

    def per_country(self):
        """[{"country": "Ghana", "total": 12}, ...], most clicks first."""
        return (
            self.values("country")
            .annotate(total=Count("id"))
            .order_by("-total", "country")
        )

    def per_day(self):
        """[{"day": date(2026, 11, 13), "total": 5}, ...], oldest day first (UTC)."""
        return (
            self.annotate(day=TruncDate("clicked_at"))
            .values("day")
            .annotate(total=Count("id"))
            .order_by("day")
        )

    def top_referrers(self, limit=10):
        """[{"referrer": "https://t.co/", "total": 7}, ...], most clicks first."""
        return (
            self.exclude(referrer__isnull=True)
            .values("referrer")
            .annotate(total=Count("id"))
            .order_by("-total", "referrer")[:limit]
        )


class Click(models.Model):

    objects = ClickQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["url", "clicked_at"]),
        ]

    url = models.ForeignKey(
        Url,
        on_delete=models.CASCADE,
        related_name="clicks"
    )
    clicked_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField()
    city = models.CharField(max_length=100, null=True, blank=True)
    country = models.CharField(max_length=100, null=True, blank=True)
    user_agent = models.TextField()
    referrer = models.URLField(max_length=2048, null=True, blank=True)

    def __str__(self):
        return f"{self.url.short_code} @ {self.clicked_at}"
