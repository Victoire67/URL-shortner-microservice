import fakeredis
import pytest
from django.apps import apps
from rest_framework.test import APIClient


@pytest.fixture(autouse=True)
def fast_password_hashing(settings):
    """Real hashers are slow on purpose; tests only need passwords to round-trip."""
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def redis_client():
    """In-memory Redis so tests never need a real server."""
    return fakeredis.FakeRedis(decode_responses=True)


@pytest.fixture
def container(redis_client):
    """The app's DI container with Redis swapped for the fake one."""
    container = apps.get_app_config("shortener").container
    container.reset_singletons()
    with container.redis_client.override(redis_client):
        yield container
    container.reset_singletons()


@pytest.fixture
def api_client(container, db):
    """API client with the fake Redis and access to the test database."""
    return APIClient()
