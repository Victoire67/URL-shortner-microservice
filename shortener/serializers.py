from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from shortener.models import Tag, Url


class URLSerializer(serializers.ModelSerializer):
    """A shortened url, read and written through /api/v1/urls/."""

    short_url = serializers.SerializerMethodField(
        help_text="Full url that redirects to original_url."
    )
    owner = serializers.SlugRelatedField(
        slug_field="username",
        read_only=True,
        help_text="Username of the owner, or null for anonymous urls.",
    )
    tags = serializers.SlugRelatedField(
        many=True,
        slug_field="name",
        queryset=Tag.objects.all(),
        required=False,
        help_text="Tag names, e.g. ['Work', 'Social']. Each tag must already exist.",
    )

    class Meta:
        model = Url
        fields = [
            "short_code",
            "short_url",
            "owner",
            "original_url",
            "custom_alias",
            "title",
            "description",
            "tags",
            "is_active",
            "expires_at",
            "click_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "short_code",
            "is_active",
            "click_count",
            "created_at",
            "updated_at",
        ]

    @extend_schema_field(OpenApiTypes.URI)
    def get_short_url(self, url: Url) -> str:
        path = reverse("shortener:resolve", args=[url.short_code])
        request = self.context.get("request")
        return request.build_absolute_uri(path) if request else path

    def validate_custom_alias(self, value: str | None) -> str | None:
        # Store "no alias" as NULL: unique allows many NULLs but only one ""
        return value or None
