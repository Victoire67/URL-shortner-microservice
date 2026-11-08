from rest_framework import serializers


class ShortenRequestSerializer(serializers.Serializer):
    """Validates the long url sent to the shorten endpoint."""

    url = serializers.URLField(
        max_length=2048,
        help_text="The long url to shorten. Must be a valid http(s) url.",
    )


class ShortenResponseSerializer(serializers.Serializer):
    """Shape of the shorten endpoint response."""

    short_code = serializers.CharField(help_text="Unique 7 character code.")
    short_url = serializers.URLField(help_text="Full url that redirects to the long url.")
    long_url = serializers.URLField(help_text="The original url.")
