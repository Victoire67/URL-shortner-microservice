from django.conf import settings
from django.db import models


class Url(models.Model):

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
