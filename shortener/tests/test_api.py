import fakeredis
import pytest
from django.urls import reverse

SHORTEN_URL = reverse("shortener:shorten")


def shorten(api_client, url="https://example.com/some/long/path"):
    return api_client.post(SHORTEN_URL, {"url": url}, format="json")


def test_shorten_returns_201_with_short_url(api_client):
    response = shorten(api_client)

    assert response.status_code == 201
    body = response.json()
    assert body["long_url"] == "https://example.com/some/long/path"
    assert body["short_url"] == f"http://testserver/api/{body['short_code']}"


@pytest.mark.parametrize("payload", [{"url": "not-a-url"}, {"url": ""}, {}])
def test_shorten_rejects_invalid_url_with_structured_error(api_client, payload):
    response = api_client.post(SHORTEN_URL, payload, format="json")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["status"] == 400
    assert error["code"] == "invalid"
    assert "url" in error["details"]


def test_shorten_rejects_malformed_json(api_client):
    response = api_client.post(SHORTEN_URL, "{bad json", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "parse_error"


def test_resolve_redirects_to_long_url(api_client):
    code = shorten(api_client).json()["short_code"]

    response = api_client.get(reverse("shortener:resolve", args=[code]))

    assert response.status_code == 302
    assert response["Location"] == "https://example.com/some/long/path"


def test_resolve_unknown_code_returns_404(api_client):
    response = api_client.get(reverse("shortener:resolve", args=["missing"]))

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "short_code_not_found"
    assert "missing" in error["message"]


def test_wrong_method_returns_405(api_client):
    response = api_client.get(SHORTEN_URL)

    assert response.status_code == 405
    assert response.json()["error"]["code"] == "method_not_allowed"


def test_storage_down_returns_503(api_client, container):
    server = fakeredis.FakeServer()
    server.connected = False
    container.reset_singletons()

    with container.redis_client.override(fakeredis.FakeRedis(server=server)):
        response = shorten(api_client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"


def test_unknown_route_returns_json_404(client):
    response = client.get("/does/not/exist/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
