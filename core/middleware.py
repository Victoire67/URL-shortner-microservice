import logging
import time

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware:
    """Logs method, path, status code, duration and client ip of every request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        started = time.perf_counter()
        response = self.get_response(request)
        duration_ms = (time.perf_counter() - started) * 1000

        logger.info(
            "%s %s %s %d %.1fms",
            request.META.get("REMOTE_ADDR", "-"),
            request.method,
            request.get_full_path(),
            response.status_code,
            duration_ms,
        )
        return response
