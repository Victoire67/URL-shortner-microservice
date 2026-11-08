from dependency_injector.wiring import Provide, inject
from django.shortcuts import redirect
from django.urls import reverse
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shortener.containers import Container
from shortener.serializers import ShortenRequestSerializer, ShortenResponseSerializer
from shortener.services import UrlShortenerService


class ShortenView(APIView):
    """Takes a long url and returns its short code."""

    @extend_schema(
        request=ShortenRequestSerializer,
        responses={
            201: ShortenResponseSerializer,
            400: OpenApiResponse(description="Invalid url"),
            503: OpenApiResponse(description="Storage unavailable or no free code"),
        },
    )
    @inject
    def post(
        self,
        request,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        serializer = ShortenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        short_code = service.shorten(serializer.validated_data["url"])
        short_url = request.build_absolute_uri(reverse("shortener:resolve", args=[short_code]))
        return Response(
            {"short_code": short_code, "short_url": short_url},
            status=status.HTTP_201_CREATED,
        )


class ResolveView(APIView):
    """Redirects a short code to its long url."""

    @extend_schema(
        responses={
            302: OpenApiResponse(description="Redirect to the long url"),
            404: OpenApiResponse(description="Short code not found"),
        },
    )
    @inject
    def get(
        self,
        request,
        short_code: str,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        return redirect(service.resolve(short_code))
