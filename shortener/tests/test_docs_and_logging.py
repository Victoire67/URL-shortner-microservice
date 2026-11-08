import logging


def test_swagger_ui_is_served(client):
    assert client.get("/api/docs/").status_code == 200


def test_openapi_schema_lists_both_endpoints(client):
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert "/api/shorten/" in paths
    assert "/api/{short_code}" in paths


def test_root_redirects_to_swagger(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == "/api/docs/"


def test_requests_are_logged(api_client, caplog):
    with caplog.at_level(logging.INFO, logger="core.middleware"):
        api_client.get("/api/missing")

    assert any("GET /api/missing 404" in message for message in caplog.messages)
