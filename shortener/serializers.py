from rest_framework import serializers


class ShortenRequestSerializer(serializers.Serializer):
    """Validates the long url sent to the shorten endpoint"""

    url = serializers.URLField(max_length=2048)


class ShortenResponseSerializer(serializers.Serializer):
    """Shape of the shorten endpoint response"""

    short_code = serializers.CharField()
    short_url = serializers.URLField()
