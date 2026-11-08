# URL Shortener Microservice

A REST API, built with Django, that turns long urls into short codes and redirects short codes back to the original url.
It uses Redis for storage, dependency injection for its services, Docker for local and production runs, and
interactive Swagger documentation.

## Tech stack

The lab brief is written for Flask. The reviewers approved building it with Django, using these equivalents:

| Lab requirement (Flask)        | This project (Django)                                             |
| ------------------------------ | ----------------------------------------------------------------- |
| Application factory + profiles | Split settings: `config/settings/base.py`, `dev.py`, `prod.py`    |
| Blueprints                     | Django app: `shortener/` with its own `urls.py`                   |
| Flask-RESTX                    | Django REST Framework                                             |
| Pydantic / Marshmallow         | DRF serializers                                                   |
| Flask-Injector                 | `dependency-injector`                                             |
| RESTX Swagger / OpenAPI        | `drf-spectacular` (OpenAPI 3 + Swagger UI)                        |
| App / request context          | Django `AppConfig.ready()` (startup) and the `request` object     |
| python-decouple, Gunicorn      | Same                                                              |

Python 3.13, Django 6.1, Redis 7.

## Architecture

```
config/                  Project configuration
  settings/base.py       Shared settings (DRF, OpenAPI, logging)
  settings/dev.py        Development profile: DEBUG on
  settings/prod.py       Production profile: DEBUG off, secret key required
  urls.py                Root routes and JSON error handlers
core/                    Cross-cutting concerns
  exceptions.py          Global exception handler -> structured JSON errors
  middleware.py          Request logging middleware
  serializers.py         Error response schema for the docs
shortener/               The shortener app
  views.py               API endpoints (HTTP only, no business logic)
  serializers.py         Request validation and response shapes
  services.py            UrlShortenerService: code generation and lookup
  repositories.py        RedisUrlRepository: storage access
  containers.py          DI container that wires Redis -> repository -> service
  exceptions.py          Domain errors (not found, generation failed)
  tests/                 Unit and API tests
Dockerfile               Multi-stage production image (Gunicorn)
docker-compose.yml       App (dev and prod profiles) + Redis
gunicorn.conf.py         Gunicorn worker settings
```

A request flows through the layers like this:

```
HTTP -> RequestLoggingMiddleware -> View -> UrlShortenerService -> RedisUrlRepository -> Redis
                                     |
                       errors -> global exception handler -> JSON error
```

- **Dependency injection.** `shortener/containers.py` declares how to build the Redis client, the repository and the
  service. `ShortenerConfig.ready()` builds the container once at startup and wires it into the views, which receive
  the service through `Provide[...]`. The views never create their own dependencies, so tests can swap Redis for an
  in-memory fake.
- **Short codes** are 7 random characters (`a-z A-Z 0-9`). Codes are saved with `SET NX`, so an existing code is
  never overwritten. On a collision the service retries up to 5 times.

## API

| Method | Path                | Description                         | Success | Errors   |
| ------ | ------------------- | ----------------------------------- | ------- | -------- |
| POST   | `/api/shorten/`     | Create a short code for a long url  | 201     | 400, 503 |
| GET    | `/api/<short_code>` | Redirect to the long url            | 302     | 404      |
| GET    | `/api/docs/`        | Swagger UI                          | 200     |          |
| GET    | `/api/schema/`      | OpenAPI 3 schema                    | 200     |          |

```bash
curl -X POST http://localhost:8000/api/shorten/ \
     -H "Content-Type: application/json" \
     -d '{"url": "https://docs.djangoproject.com/en/stable/"}'
# 201 {"short_code": "aZ3kP9q", "short_url": "http://localhost:8000/api/aZ3kP9q", "long_url": "..."}

curl -i http://localhost:8000/api/aZ3kP9q
# 302 Location: https://docs.djangoproject.com/en/stable/
```

Every error has the same JSON shape:

```json
{
  "error": {
    "status": 400,
    "code": "invalid",
    "message": "Request validation failed.",
    "details": { "url": ["Enter a valid URL."] }
  }
}
```

> **Testing the redirect in Swagger:** browsers follow the 302 automatically, so Swagger UI shows the response of the
> target site. Many sites block that cross-origin request, so Swagger may say "Failed to fetch". To see the
> redirect, open the `short_url` in a browser tab or use `curl -i`.

## Getting started

### Run with Docker (recommended)

Requirements: Docker with Docker Compose.

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:8000/api/docs/ for Swagger UI.

This starts the **development profile**: the Django dev server with `DEBUG=True`, and your source code mounted as a
volume so changes reload automatically.

To run the **production profile** (Gunicorn with multiple workers, `DEBUG=False`) on port 8001, set a real
`SECRET_KEY` in `.env` first, then run:

```bash
docker compose --profile prod up --build web-prod
```

### Run locally without Docker

Requirements: Python 3.13+, and a Redis server (`docker compose up -d redis` starts one).

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt  # or: poetry install
cp .env.example .env
python manage.py runserver
```

## Configuration

Settings are read from environment variables or the `.env` file (see `.env.example`).

| Variable                 | Default                    | Description                                         |
| ------------------------ | -------------------------- | --------------------------------------------------- |
| `DJANGO_SETTINGS_MODULE` | `config.settings.dev`      | `config.settings.dev` or `config.settings.prod`     |
| `SECRET_KEY`             | dev only: insecure default | Django secret key. **Required in production.**      |
| `ALLOWED_HOSTS`          | `localhost,127.0.0.1`      | Comma separated hostnames the app may serve         |
| `REDIS_URL`              | `redis://localhost:6379/0` | Redis connection (Compose points it at `redis`)     |
| `LOG_LEVEL`              | `INFO`                     | Log level for the app and Gunicorn                  |
| `GUNICORN_WORKERS`       | `2 x CPU cores + 1`        | Production worker count                             |

## Tests

The tests use an in-memory fake Redis, so no server is needed.

```bash
poetry install
poetry run pytest
```

Without Poetry: `pip install -r requirements.txt pytest pytest-django fakeredis`, then run `pytest`.
