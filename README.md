# URL Shortener Microservice

A REST API, built with Django, that turns long urls into short codes and redirects short codes back to the original url.
It uses Redis for storage, dependency injection for its services, Docker for local and production runs, and
interactive Swagger documentation.


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
