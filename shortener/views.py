from dependency_injector.wiring import Provide, inject
from django.shortcuts import redirect
from django.urls import reverse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import error_body
from core.serializers import ErrorResponseSerializer
from shortener.containers import Container
from shortener.serializers import ShortenRequestSerializer, ShortenResponseSerializer
from shortener.services import UrlShortenerService

TAG = "Shortener"


class ShortenView(APIView):
    """Takes a long url and returns its short code."""

    @extend_schema(
        tags=[TAG],
        summary="Shorten a url",
        operation_id="shorten_url",
        description="Stores the long url under a new unique short code.",
        request=ShortenRequestSerializer,
        responses={
            201: OpenApiResponse(ShortenResponseSerializer, description="Short url created."),
            400: OpenApiResponse(ErrorResponseSerializer, description="The url is missing or invalid."),
            503: OpenApiResponse(ErrorResponseSerializer, description="Storage unavailable or no free code."),
        },
        examples=[
            OpenApiExample(
                "Long url",
                value={"url": "https://docs.djangoproject.com/en/stable/topics/http/urls/"},
                request_only=True,
            ),
            OpenApiExample(
                "Created",
                value={
                    "short_code": "aZ3kP9q",
                    "short_url": "http://localhost:8000/api/aZ3kP9q",
                    "long_url": "https://docs.djangoproject.com/en/stable/topics/http/urls/",
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "Invalid url",
                value=error_body(400, "invalid", "Request validation failed.", {"url": ["Enter a valid URL."]}),
                response_only=True,
                status_codes=["400"],
            ),
        ],
    )
    @inject
    def post(
        self,
        request,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        serializer = ShortenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        long_url = serializer.validated_data["url"]

        short_code = service.shorten(long_url)
        short_url = request.build_absolute_uri(reverse("shortener:resolve", args=[short_code]))

        response = ShortenResponseSerializer(
            {"short_code": short_code, "short_url": short_url, "long_url": long_url}
        )
        return Response(response.data, status=status.HTTP_201_CREATED)


class ResolveView(APIView):
    """Redirects a short code to its long url."""

    @extend_schema(
        tags=[TAG],
        summary="Resolve a short code",
        operation_id="resolve_short_code",
        description=(
            "Redirects (302) to the long url stored under the short code. "
            "Open the short url in a browser to follow the redirect."
        ),
        parameters=[
            OpenApiParameter(
                "short_code",
                OpenApiTypes.STR,
                OpenApiParameter.PATH,
                description="The code returned by the shorten endpoint.",
                examples=[OpenApiExample("Short code", value="aZ3kP9q")],
            ),
        ],
        responses={
            302: OpenApiResponse(description="Redirect to the long url (see the Location header)."),
            404: OpenApiResponse(ErrorResponseSerializer, description="The short code does not exist."),
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
        return redirect(service.resolve(short_code))
