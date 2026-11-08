"""Schemas used to document the structured error responses in OpenAPI."""

from rest_framework import serializers


class ErrorDetailSerializer(serializers.Serializer):
    status = serializers.IntegerField(help_text="HTTP status code.")
    code = serializers.CharField(help_text="Machine readable error code.")
    message = serializers.CharField(help_text="Human readable error message.")
    details = serializers.JSONField(
        allow_null=True, help_text="Field errors for validation failures, otherwise null."
    )


class ErrorResponseSerializer(serializers.Serializer):
    error = ErrorDetailSerializer()
