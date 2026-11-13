import logging


def test_swagger_ui_is_served(client):
    assert client.get("/api/docs/").status_code == 200


def test_openapi_schema_documents_every_endpoint(client):
    response = client.get("/api/schema/", HTTP_ACCEPT="application/json")

    assert response.status_code == 200
    paths = response.json()["paths"]
    assert set(paths["/api/v1/urls/"]) == {"get", "post"}
    assert set(paths["/api/v1/urls/{short_code}/"]) == {"get", "put", "delete"}
    assert set(paths["/api/v1/{short_code}"]) == {"get"}


def test_root_redirects_to_swagger(client):
    response = client.get("/")

    assert response.status_code == 302
    assert response["Location"] == "/api/docs/"


def test_requests_are_logged(api_client, caplog):
    with caplog.at_level(logging.INFO, logger="config.middleware"):
        api_client.get("/api/v1/missing")

    assert any("GET /api/v1/missing 404" in message for message in caplog.messages)
