"""
Global error handling.

Every error leaves the service as JSON with the same shape:

    {"error": {"status": 404, "code": "...", "message": "...", "details": null}}

`api_exception_handler` covers errors raised inside DRF views and the
`*_handler` views cover errors Django raises outside them (unknown routes,
bad hosts, crashes).
"""

import logging

from django.db import DatabaseError
from django.http import JsonResponse
from redis.exceptions import RedisError
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import exception_handler

logger = logging.getLogger(__name__)


def error_body(status_code: int, code: str, message: str, details=None) -> dict:
    return {
        "error": {
            "status": status_code,
            "code": code,
            "message": message,
            "details": details,
        }
    }


def api_exception_handler(exc, context):
    """DRF EXCEPTION_HANDLER that turns any exception into a structured JSON error."""
    response = exception_handler(exc, context)

    if response is not None:
        if isinstance(exc, ValidationError):
            body = error_body(
                response.status_code, "invalid", "Request validation failed.", response.data
            )
        else:
            detail = response.data.get("detail", "")
            code = getattr(detail, "code", "error")
            body = error_body(response.status_code, code, str(detail))
        response.data = body
        return response

    if isinstance(exc, (DatabaseError, RedisError)):
        logger.error("Storage backend unavailable: %s", exc)
        return Response(
            error_body(503, "storage_unavailable", "The storage backend is unavailable."),
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    logger.exception("Unhandled error", exc_info=exc)
    return Response(
        error_body(500, "server_error", "An unexpected error occurred."),
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )


def bad_request_handler(request, exception=None):
    return JsonResponse(error_body(400, "bad_request", "Bad request."), status=400)


def not_found_handler(request, exception=None):
    return JsonResponse(
        error_body(404, "not_found", "The requested resource was not found."), status=404
    )


def server_error_handler(request):
    return JsonResponse(
        error_body(500, "server_error", "An unexpected error occurred."), status=500
    )
