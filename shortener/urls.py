from django.urls import path
from rest_framework.routers import SimpleRouter

from shortener.views import ResolveView, URLViewSet

app_name = "shortener"

router = SimpleRouter()
router.register("urls", URLViewSet, basename="url")

urlpatterns = [
    *router.urls,
    path("<str:short_code>", ResolveView.as_view(), name="resolve"),
]
