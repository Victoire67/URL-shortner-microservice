from django.urls import path

from shortener.views import ResolveView, ShortenView

app_name = "shortener"

urlpatterns = [
    path("shorten/", ShortenView.as_view(), name="shorten"),
    path("<str:short_code>", ResolveView.as_view(), name="resolve"),
]
