from rest_framework import status
from rest_framework.exceptions import APIException


class ShortCodeNotFound(APIException):
    """Raised when a short code does not exist in storage."""

    status_code = status.HTTP_404_NOT_FOUND
    default_code = "short_code_not_found"
    default_detail = "Short code was not found."


class ShortCodeGenerationError(APIException):
    """Raised when a unique short code could not be generated."""

    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_code = "short_code_generation_failed"
    default_detail = "Could not generate a unique short code."
