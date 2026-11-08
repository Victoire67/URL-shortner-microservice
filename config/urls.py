from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("", include("shortener.urls")),
]

# JSON error responses for errors raised outside the API views
handler400 = "core.exceptions.bad_request_handler"
handler404 = "core.exceptions.not_found_handler"
handler500 = "core.exceptions.server_error_handler"
