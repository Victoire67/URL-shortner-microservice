from datetime import timedelta

import pytest
from django.db import OperationalError
from django.urls import reverse
from django.utils import timezone

from shortener.models import Click, Url

LIST_URL = reverse("shortener:url-list")


def detail_url(short_code):
    return reverse("shortener:url-detail", args=[short_code])


def create(api_client, **fields):
    body = {"original_url": "https://example.com/some/long/path", **fields}
    return api_client.post(LIST_URL, body, format="json")


# --- POST /api/v1/urls/ -----------------------------------------------------


def test_create_returns_201_with_the_new_url(api_client):
    response = create(api_client)

    assert response.status_code == 201
    body = response.json()
    assert body["original_url"] == "https://example.com/some/long/path"
    assert body["short_url"] == f"http://testserver/api/v1/{body['short_code']}"
    assert body["is_active"] is True
    assert body["click_count"] == 0
    assert Url.objects.filter(short_code=body["short_code"]).exists()


def test_create_stores_optional_fields_and_tags(api_client):
    response = create(
        api_client,
        custom_alias="docs",
        title="Docs",
        description="Project docs",
        tags=["Work", "Social"],
        expires_at="2030-01-01T00:00:00Z",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["custom_alias"] == "docs"
    assert body["title"] == "Docs"
    assert sorted(body["tags"]) == ["Social", "Work"]
    assert body["expires_at"] == "2030-01-01T00:00:00Z"


def test_create_ignores_read_only_fields(api_client):
    response = create(api_client, short_code="mine", click_count=99)

    body = response.json()
    assert body["short_code"] != "mine"
    assert body["click_count"] == 0


@pytest.mark.parametrize(
    "payload", [{"original_url": "not-a-url"}, {"original_url": ""}, {}]
)
def test_create_rejects_invalid_url_with_structured_error(api_client, payload):
    response = api_client.post(LIST_URL, payload, format="json")

    assert response.status_code == 400
    error = response.json()["error"]
    assert error["status"] == 400
    assert error["code"] == "invalid"
    assert "original_url" in error["details"]


def test_create_rejects_unknown_tag(api_client):
    response = create(api_client, tags=["NoSuchTag"])

    assert response.status_code == 400
    assert "tags" in response.json()["error"]["details"]


def test_create_rejects_taken_custom_alias(api_client):
    create(api_client, custom_alias="docs")

    response = create(api_client, custom_alias="docs")

    assert response.status_code == 400
    assert "custom_alias" in response.json()["error"]["details"]


def test_create_rejects_malformed_json(api_client):
    response = api_client.post(LIST_URL, "{bad json", content_type="application/json")

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "parse_error"


# --- GET /api/v1/urls/ ------------------------------------------------------


def test_list_returns_active_urls_newest_first(api_client):
    first = create(api_client).json()["short_code"]
    second = create(api_client).json()["short_code"]
    deleted = create(api_client).json()["short_code"]
    api_client.delete(detail_url(deleted))

    response = api_client.get(LIST_URL)

    assert response.status_code == 200
    assert [url["short_code"] for url in response.json()] == [second, first]


# --- GET /api/v1/urls/{short_code}/ -----------------------------------------


def test_retrieve_returns_the_url(api_client):
    code = create(api_client, title="Docs").json()["short_code"]

    response = api_client.get(detail_url(code))

    assert response.status_code == 200
    assert response.json()["short_code"] == code
    assert response.json()["title"] == "Docs"


def test_retrieve_unknown_code_returns_404(api_client):
    response = api_client.get(detail_url("missing"))

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


# --- PUT /api/v1/urls/{short_code}/ -----------------------------------------


def test_update_replaces_editable_fields(api_client):
    code = create(api_client).json()["short_code"]

    response = api_client.put(
        detail_url(code),
        {"original_url": "https://example.com/new", "title": "New", "tags": ["Work"]},
        format="json",
    )

    assert response.status_code == 200
    body = response.json()
    assert body["short_code"] == code
    assert body["original_url"] == "https://example.com/new"
    assert body["tags"] == ["Work"]
    assert Url.objects.get(short_code=code).title == "New"


def test_update_rejects_invalid_body(api_client):
    code = create(api_client).json()["short_code"]

    response = api_client.put(detail_url(code), {"original_url": "nope"}, format="json")

    assert response.status_code == 400


def test_update_unknown_code_returns_404(api_client):
    response = api_client.put(
        detail_url("missing"), {"original_url": "https://example.com"}, format="json"
    )

    assert response.status_code == 404


def test_patch_is_not_allowed(api_client):
    code = create(api_client).json()["short_code"]

    response = api_client.patch(detail_url(code), {"title": "x"}, format="json")

    assert response.status_code == 405


# --- DELETE /api/v1/urls/{short_code}/ --------------------------------------


def test_delete_deactivates_instead_of_deleting(api_client):
    code = create(api_client).json()["short_code"]

    response = api_client.delete(detail_url(code))

    assert response.status_code == 204
    assert Url.objects.get(short_code=code).is_active is False
    assert api_client.get(detail_url(code)).status_code == 404
    assert api_client.get(reverse("shortener:resolve", args=[code])).status_code == 404


def test_delete_unknown_code_returns_404(api_client):
    response = api_client.delete(detail_url("missing"))

    assert response.status_code == 404


# --- GET /api/v1/{short_code} (redirect) ------------------------------------


def test_resolve_redirects_to_long_url(api_client):
    code = create(api_client).json()["short_code"]

    response = api_client.get(reverse("shortener:resolve", args=[code]))

    assert response.status_code == 302
    assert response["Location"] == "https://example.com/some/long/path"


def test_resolve_saves_a_click_and_counts_it(api_client):
    code = create(api_client).json()["short_code"]
    resolve_url = reverse("shortener:resolve", args=[code])

    api_client.get(resolve_url, HTTP_USER_AGENT="Mozilla/5.0", HTTP_REFERER="https://t.co/x")
    api_client.get(resolve_url)

    url = Url.objects.get(short_code=code)
    assert url.click_count == 2
    first = url.clicks.order_by("clicked_at").first()
    assert first.ip_address == "127.0.0.1"
    assert first.user_agent == "Mozilla/5.0"
    assert first.referrer == "https://t.co/x"
    assert url.clicks.order_by("clicked_at").last().referrer is None


def test_resolve_expired_code_returns_404_without_a_click(api_client):
    code = create(api_client).json()["short_code"]
    Url.objects.filter(short_code=code).update(expires_at=timezone.now() - timedelta(minutes=1))

    response = api_client.get(reverse("shortener:resolve", args=[code]))

    assert response.status_code == 404
    assert Click.objects.count() == 0


def test_resolve_unknown_code_returns_404(api_client):
    response = api_client.get(reverse("shortener:resolve", args=["missing"]))

    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "short_code_not_found"
    assert "missing" in error["message"]


# --- Errors -----------------------------------------------------------------


class UnavailableRepository:
    def save_if_absent(self, short_code, long_url, **options):
        raise OperationalError("database is down")

    def get(self, short_code):
        raise OperationalError("database is down")

    def record_click(self, short_code, visit):
        raise OperationalError("database is down")


def test_storage_down_returns_503(api_client, container):
    container.reset_singletons()

    with container.url_repository.override(UnavailableRepository()):
        response = create(api_client)

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "storage_unavailable"


def test_unknown_route_returns_json_404(client):
    response = client.get("/does/not/exist/")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"
