from dependency_injector.wiring import Provide, inject
from django.shortcuts import redirect
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import viewsets
from rest_framework.views import APIView

from config.exceptions import error_body
from config.serializers import ErrorResponseSerializer
from shortener.containers import Container
from shortener.domain import Visit
from shortener.models import Click, Url
from shortener.serializers import URLSerializer
from shortener.services import UrlShortenerService

URLS_TAG = "URLs"
REDIRECT_TAG = "Redirect"

SHORT_CODE_PARAMETER = OpenApiParameter(
    "short_code",
    OpenApiTypes.STR,
    OpenApiParameter.PATH,
    description="The code returned when the url was created.",
    examples=[OpenApiExample("Short code", value="aZ3kP9q")],
)

URL_REQUEST_EXAMPLE = OpenApiExample(
    "New url",
    value={
        "original_url": "https://docs.djangoproject.com/en/stable/topics/http/urls/",
        "custom_alias": "django-urls",
        "title": "Django URL dispatcher",
        "description": "Docs for routing in Django",
        "tags": ["Work"],
        "expires_at": "2027-01-01T00:00:00Z",
    },
    request_only=True,
)

URL_RESPONSE_EXAMPLE = OpenApiExample(
    "Url",
    value={
        "short_code": "aZ3kP9q",
        "short_url": "http://localhost:8000/api/v1/aZ3kP9q",
        "owner": None,
        "original_url": "https://docs.djangoproject.com/en/stable/topics/http/urls/",
        "custom_alias": "django-urls",
        "title": "Django URL dispatcher",
        "description": "Docs for routing in Django",
        "tags": ["Work"],
        "is_active": True,
        "expires_at": "2027-01-01T00:00:00Z",
        "click_count": 0,
        "created_at": "2026-11-13T10:00:00Z",
        "updated_at": "2026-11-13T10:00:00Z",
    },
    response_only=True,
)

INVALID_EXAMPLE = OpenApiExample(
    "Invalid url",
    value=error_body(400, "invalid", "Request validation failed.", {"original_url": ["Enter a valid URL."]}),
    response_only=True,
    status_codes=["400"],
)

NOT_FOUND_EXAMPLE = OpenApiExample(
    "Not found",
    value=error_body(404, "not_found", "No Url matches the given query."),
    response_only=True,
    status_codes=["404"],
)

INVALID_RESPONSE = OpenApiResponse(ErrorResponseSerializer, description="The body is invalid.")
NOT_FOUND_RESPONSE = OpenApiResponse(
    ErrorResponseSerializer, description="No active url has this short code."
)


@extend_schema_view(
    list=extend_schema(
        tags=[URLS_TAG],
        summary="List urls",
        description="Returns every active url, newest first.",
        examples=[URL_RESPONSE_EXAMPLE],
    ),
    create=extend_schema(
        tags=[URLS_TAG],
        summary="Create a short url",
        description="Stores original_url under a new unique short code.",
        responses={
            201: URLSerializer,
            400: INVALID_RESPONSE,
            503: OpenApiResponse(ErrorResponseSerializer, description="Storage unavailable or no free code."),
        },
        examples=[URL_REQUEST_EXAMPLE, URL_RESPONSE_EXAMPLE, INVALID_EXAMPLE],
    ),
    retrieve=extend_schema(
        tags=[URLS_TAG],
        summary="Get a url",
        parameters=[SHORT_CODE_PARAMETER],
        responses={200: URLSerializer, 404: NOT_FOUND_RESPONSE},
        examples=[URL_RESPONSE_EXAMPLE, NOT_FOUND_EXAMPLE],
    ),
    update=extend_schema(
        tags=[URLS_TAG],
        summary="Update a url",
        description="Replaces the editable fields. short_code and click_count never change.",
        parameters=[SHORT_CODE_PARAMETER],
        responses={200: URLSerializer, 400: INVALID_RESPONSE, 404: NOT_FOUND_RESPONSE},
        examples=[URL_REQUEST_EXAMPLE, URL_RESPONSE_EXAMPLE, INVALID_EXAMPLE, NOT_FOUND_EXAMPLE],
    ),
    destroy=extend_schema(
        tags=[URLS_TAG],
        summary="Deactivate a url",
        description="Soft delete: sets is_active to false so the short url stops redirecting.",
        parameters=[SHORT_CODE_PARAMETER],
        responses={204: None, 404: NOT_FOUND_RESPONSE},
        examples=[NOT_FOUND_EXAMPLE],
    ),
)
class URLViewSet(viewsets.ModelViewSet):
    """Create, list, read, update and deactivate short urls."""

    # owner is joined in the same query and tags are fetched in one extra query,
    # so listing 1 or 1000 urls always costs 2 queries
    queryset = (
        Url.objects.filter(is_active=True)
        .select_related("owner")
        .prefetch_related("tags")
    )
    serializer_class = URLSerializer
    lookup_field = "short_code"
    http_method_names = ["get", "post", "put", "delete", "head", "options"]

    @inject
    def perform_create(
        self,
        serializer,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        data = serializer.validated_data
        short_code = service.shorten(
            data["original_url"],
            custom_alias=data.get("custom_alias"),
            expires_at=data.get("expires_at"),
            tags=[tag.name for tag in data.get("tags", [])],
            title=data.get("title", ""),
            description=data.get("description", ""),
        )
        serializer.instance = Url.objects.get(short_code=short_code)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])


REFERRER_MAX_LENGTH = Click._meta.get_field("referrer").max_length


def visit_from_request(request) -> Visit:
    """Reads who is visiting from the HTTP request."""
    referrer = request.META.get("HTTP_REFERER", "")[:REFERRER_MAX_LENGTH] or None
    return Visit(
        ip_address=request.META["REMOTE_ADDR"],
        user_agent=request.META.get("HTTP_USER_AGENT", ""),
        referrer=referrer,
    )


class ResolveView(APIView):
    """Redirects a short code to its long url and logs the click."""

    @extend_schema(
        tags=[REDIRECT_TAG],
        summary="Resolve a short code",
        operation_id="resolve_short_code",
        description=(
            "Redirects (302) to the long url stored under the short code and saves "
            "the visit (IP, user agent, referrer) as a click. Missing, expired and "
            "deactivated codes return 404. Open the short url in a browser to follow "
            "the redirect."
        ),
        parameters=[SHORT_CODE_PARAMETER],
        responses={
            302: OpenApiResponse(description="Redirect to the long url (see the Location header)."),
            404: OpenApiResponse(
                ErrorResponseSerializer, description="The short code is missing, expired or deactivated."
            ),
        },
        examples=[
            OpenApiExample(
                "Not found",
                value=error_body(404, "short_code_not_found", "Short code 'aZ3kP9q' was not found."),
                response_only=True,
                status_codes=["404"],
            ),
        ],
    )
    @inject
    def get(
        self,
        request,
        short_code: str,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        return redirect(service.resolve(short_code, visit_from_request(request)))
