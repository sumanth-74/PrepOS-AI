# PrepOS AI Backend

Production modular monolith backend for PrepOS AI.

## Stack

- Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic
- PostgreSQL 17, Redis, Celery
- OpenTelemetry, Sentry, structured logging

## Local development

```bash
cp ../.env.example ../.env
docker compose up --build
```

API: http://localhost:8000/docs

## Without Docker

PostgreSQL and Redis must be running locally (Homebrew, Postgres.app, etc.).

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
bash scripts/migrate-db.sh
uvicorn prepos.api.main:app --reload --host 127.0.0.1 --port 8000
```

Or use the helper script from the repo root:

```bash
bash backend/scripts/dev-api.sh
```

**Common mistakes**

| Error | Fix |
|-------|-----|
| `No module named 'structlog'` | Activate `.venv` and run `pip install -e ".[dev]"` |
| `No module named 'prepos'` | Use the venv; app path is `prepos.api.main:app` (not `prepos.main:app`) |
| Port 8000 conflict | Bind to `127.0.0.1:8000` — `localhost:8000` may hit DynamoDB Local on IPv6 |
| `column preparation_twins.readiness_score does not exist` | Run `bash scripts/migrate-db.sh` to apply pending migrations |
| `duplicate column` during `alembic upgrade` | Run `bash scripts/migrate-db.sh` (repairs version stamp drift) |

API docs: http://127.0.0.1:8000/docs

## Tests

```bash
cd backend
pytest
```

## Architecture

See `docs/IMPLEMENTATION_GENERATION_MASTER_PROMPT.md`.
