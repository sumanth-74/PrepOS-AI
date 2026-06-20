# Production Deployment Readiness — Sprint P1.0

**Generated:** 2026-06-20  
**Scope:** Backend Docker/Compose, Celery, migrations; Frontend Next.js production build and deployment

---

## Executive Summary

Backend is **compose-ready** with Postgres, Redis, API, worker, and beat. Frontend is a **real Next.js app** (`apps/web`) but **docker-compose still serves an nginx placeholder**, not the built app. Production deployment requires wiring Next.js standalone output or a separate frontend service.

**Deployment readiness score:** 62/100

---

## Backend

### Docker

| Item | Status | Notes |
|------|--------|-------|
| `backend/docker/Dockerfile` | ✅ | Python 3.13-slim, multi-stage, non-root `prepos` user |
| Package install | ✅ | hatchling/pip editable install |
| Alembic in image | ✅ | `alembic/` + `alembic.ini` copied |
| Default CMD | ✅ | uvicorn (compose overrides) |

### Docker Compose (`docker-compose.yml`)

| Service | Status | Notes |
|---------|--------|-------|
| `postgres` | ✅ | PG 17, healthcheck, persistent volume |
| `redis` | ✅ | Redis 7, healthcheck |
| `api` | ✅ | Migrates on start, port 8000, hot-reload mount (dev) |
| `worker` | ✅ | Celery worker `-Q default,events` |
| `beat` | ✅ | Outbox publish every 30s |
| `frontend` | ❌ | **nginx placeholder only** — not `apps/web` |

**Gaps:**
- API uses `--reload` in compose (not production-safe)
- Source mounted read-only (dev pattern)
- No healthcheck on API/worker services
- No resource limits / restart policies beyond defaults
- Beat does not depend on postgres (OK for outbox-only)

### Environment variables

**Source:** `.env.example` + `backend/src/prepos/core/config.py`

| Category | Required | Production notes |
|----------|----------|------------------|
| `SECRET_KEY` | ✅ | Must replace placeholder; use secrets manager |
| `DATABASE_URL` | ✅ | asyncpg URL; compose overrides host to `postgres` |
| `REDIS_URL` | ✅ | Required for Celery |
| `CELERY_BROKER_URL` / `CELERY_RESULT_BACKEND` | ✅ | Separate Redis DBs 1/2 |
| `CORS_ORIGINS` | ✅ | Must include production frontend origin |
| `COOKIE_SECURE` | ⚠️ | `false` in example — **must be `true` behind HTTPS** |
| `OTEL_ENABLED` | ⚠️ | `false` in example; enable for prod observability |
| `SENTRY_DSN` | Optional | Recommended for prod |
| `APP_ENV` | ⚠️ | Set `production` to enable OTEL (non-dev skip) |

### PostgreSQL

| Item | Status |
|------|--------|
| Schema migrations | ✅ 25 revisions (001–026) |
| Migration on deploy | ✅ `alembic upgrade head` in compose API command |
| Local repair script | ✅ `backend/scripts/migrate-db.sh` |
| Connection pooling | ✅ pool_size=10, max_overflow=20 |

### Redis

| Item | Status |
|------|--------|
| Celery broker | ✅ |
| Result backend | ✅ |
| App cache URL | ✅ configured; LG cache is NoOp in deps |

### Celery workers

| Item | Status |
|------|--------|
| Worker process | ✅ Defined in compose |
| Beat scheduler | ✅ `publish_outbox_batch` task |
| Event dispatch queue | ✅ `events` queue |
| Eager mode | ⚠️ `CELERY_TASK_ALWAYS_EAGER=false` in prod — **worker mandatory** |
| Worker health | ❌ Not in readiness probe |

**Critical:** Without worker + beat, activities and goals enqueue outbox events that **never project** to twin/study plan/mentor queue.

### Alembic migrations

| Item | Status |
|------|--------|
| Head revision | `026_mentor_effectiveness_learning` |
| Async env | ✅ |
| Idempotent seed | Separate script (`seed_demo_data.py`) |

---

## Frontend

### Production build

| Item | Status | Notes |
|------|--------|-------|
| `apps/web` Next.js 15 | ✅ | Builds successfully |
| `npm run typecheck` | ✅ PASS |
| `npm run lint` | ✅ PASS |
| `npm run build` | ✅ PASS — 15 routes |
| Env | ✅ | `NEXT_PUBLIC_API_BASE_URL` in `.env.local.example` |

### Environment variables

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_BASE_URL` | API base (e.g. `http://127.0.0.1:8000/api/v1`) |

### Nginx / static deployment

| Item | Status |
|------|--------|
| Compose frontend service | ❌ Placeholder HTML at `docker/frontend-placeholder/` |
| Next.js standalone Docker | ❌ Not configured |
| Nginx reverse proxy config | ❌ Not in repo |
| CDN / static asset strategy | ❌ Not documented |

**Recommended production pattern:**
1. Build `apps/web` with `output: 'standalone'` in `next.config.ts`
2. Add `frontend` Dockerfile multi-stage (node build → node runtime or nginx for static export if applicable)
3. Terminate TLS at load balancer; proxy `/api` to backend

---

## Deployment Checklist (pilot)

### Must do before pilot

- [ ] Replace `SECRET_KEY` and DB credentials
- [ ] Set `COOKIE_SECURE=true`, `APP_ENV=production`
- [ ] Run worker + beat alongside API
- [ ] Configure CORS for production frontend URL
- [ ] Deploy real Next.js frontend (not placeholder)
- [ ] Run `seed_demo_data.py` or institute onboarding via API
- [ ] Verify `/health/ready` returns DB ok

### Should do

- [ ] Enable Sentry + OTEL in staging/prod
- [ ] Remove uvicorn `--reload` from production compose override
- [ ] Add API/worker healthchecks to compose/K8s
- [ ] Extend readiness to Redis + worker ping
- [ ] Secrets via vault/K8s secrets, not `.env` in image

### Nice to have

- [ ] Separate staging environment
- [ ] Database backup/restore runbook
- [ ] Horizontal scaling notes for worker queue depth

---

## Production Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Missing Celery worker | Stale twin, empty UI | Monitor outbox pending count; alert if worker down |
| Placeholder frontend in compose | Wrong deploy artifact | Replace with Next.js service |
| Dev reload in API container | Instability, memory | Production compose profile without reload |
| Default SECRET_KEY | Token forgery | Fail deploy if placeholder detected |
| No frontend CDN/TLS docs | Misconfigured prod | Add deployment guide |
