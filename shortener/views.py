from dependency_injector.wiring import Provide, inject
from django.shortcuts import redirect
from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from shortener.containers import Container
from shortener.exceptions import ShortCodeGenerationError, ShortCodeNotFound
from shortener.serializers import ShortenRequestSerializer, ShortenResponseSerializer
from shortener.services import UrlShortenerService


class ShortenView(APIView):
    """Takes a long url and returns its short code"""

    @extend_schema(
        request=ShortenRequestSerializer,
        responses={201: ShortenResponseSerializer, 400: OpenApiResponse(description="Invalid url")},
    )
    @inject
    def post(
        self,
        request,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        serializer = ShortenRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            short_code = service.shorten(serializer.validated_data["url"])
        except ShortCodeGenerationError as error:
            return Response({"detail": str(error)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        short_url = request.build_absolute_uri(f"/{short_code}")
        return Response(
            {"short_code": short_code, "short_url": short_url},
            status=status.HTTP_201_CREATED,
        )


class ResolveView(APIView):
    """Redirects a short code to its long url"""

    @extend_schema(
        responses={302: OpenApiResponse(description="Redirect to the long url"),
                   404: OpenApiResponse(description="Short code not found")},
    )
    @inject
    def get(
        self,
        request,
        short_code: str,
        service: UrlShortenerService = Provide[Container.url_shortener_service],
    ):
        try:
            long_url = service.resolve(short_code)
        except ShortCodeNotFound as error:
            return Response({"detail": str(error)}, status=status.HTTP_404_NOT_FOUND)

        return redirect(long_url)
