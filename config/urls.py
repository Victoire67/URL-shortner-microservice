from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="swagger-ui"), name="home"),
    path("admin/", admin.site.urls),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/v1/", include("shortener.urls")),
]

if getattr(settings, "DEBUG_TOOLBAR", False):
    from debug_toolbar.toolbar import debug_toolbar_urls

    urlpatterns += debug_toolbar_urls()

# JSON error responses for errors raised outside the API views
handler400 = "config.exceptions.bad_request_handler"
handler404 = "config.exceptions.not_found_handler"
handler500 = "config.exceptions.server_error_handler"
