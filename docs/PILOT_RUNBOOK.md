# PrepOS Pilot Runbook

Operational guide for deploying and running PrepOS in a pilot environment.

---

## Prerequisites

| Component | Version | Notes |
|-----------|---------|-------|
| Docker + Compose | 24+ | Recommended deployment path |
| PostgreSQL | 17 | Provided via compose or managed service |
| Redis | 7 | Celery broker + cache |
| Node.js | 20 | Local frontend dev only |
| Python | 3.13 | Local backend dev only |

---

## 1. Deployment Steps

### Option A — Docker Compose (pilot)

```bash
# 1. Copy environment
cp .env.example .env
# Edit SECRET_KEY, DATABASE_URL, CORS_ORIGINS for your domain

# 2. Start core stack
docker compose up -d postgres redis api worker beat

# 3. Run migrations (first deploy)
docker compose exec api alembic upgrade head

# 4. Seed demo / pilot data
docker compose exec api python scripts/seed_demo_data.py

# 5. Build and start production frontend
export NEXT_PUBLIC_API_BASE_URL=https://your-api.example.com/api/v1
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d web

# Optional nginx reverse proxy on :8080
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d frontend-proxy
```

### Option B — Local development

```bash
# Backend
cd backend && pip install -e ".[dev]"
alembic upgrade head
uvicorn prepos.api.main:app --reload --port 8000

# Worker (separate terminal)
celery -A prepos.tasks.celery_app worker -Q default,events
celery -A prepos.tasks.celery_app beat

# Frontend
cd apps/web && cp .env.local.example .env.local
npm ci && npm run dev
```

### Post-deploy verification

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
curl http://localhost:8000/health/ops
```

Open admin health UI: `/admin/health` (institute admin login required).

---

## 2. Rollback Steps

### Application rollback

```bash
# Re-deploy previous image tag
docker compose pull api web   # if using registry tags
docker compose up -d api web

# Or rebuild from previous git tag
git checkout <previous-tag>
docker compose build api web
docker compose up -d api worker beat api web
```

### Database rollback

```bash
# Downgrade one migration (use with caution)
docker compose exec api alembic downgrade -1

# Prefer restore from backup for production rollback (see section 4)
```

### Frontend-only rollback

```bash
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d web --force-recreate
```

---

## 3. Worker Recovery

### Symptoms

- Activities return 202 but dashboard/twin never updates
- `/health/worker` shows `unavailable` or `worker_count: 0`
- `/health/outbox` shows growing `pending` count

### Recovery

```bash
# Check worker container
docker compose ps worker beat
docker compose logs worker --tail 100

# Restart worker + beat
docker compose restart worker beat

# Verify heartbeat
curl http://localhost:8000/health/worker
curl http://localhost:8000/health/outbox
```

### Manual outbox drain (development only)

```bash
cd backend
python -c "
import asyncio
from demo_seed_support import configure_demo_env, create_app_client, drain_outbox
async def main():
    settings = configure_demo_env()
    _, _, session_factory = await create_app_client(settings)
    async with session_factory() as session:
        n = await drain_outbox(session)
        print(f'Drained {n} events')
asyncio.run(main())
"
```

---

## 4. Database Backup

### Manual backup

```bash
docker compose exec postgres pg_dump -U prepos -d prepos -Fc > prepos_$(date +%Y%m%d_%H%M).dump
```

### Restore

```bash
docker compose exec -T postgres pg_restore -U prepos -d prepos --clean --if-exists < prepos_backup.dump
```

### Pilot recommendation

- Daily automated backups via managed Postgres or cron + object storage
- Test restore monthly

---

## 5. Seed Data

### Demo tenant (pilot workshops)

```bash
cd backend
python scripts/seed_demo_data.py
```

| Role | Email | Password |
|------|-------|----------|
| Tenant | `prepos-demo` | — |
| Admin | `admin@prepos-demo.example.com` | `SecurePass123!` |
| Faculty | `faculty@prepos-demo.example.com` | `SecurePass123!` |
| Student | `student@prepos-demo.example.com` | `SecurePass123!` |

Seed is **idempotent** — safe to re-run.

---

## 6. Troubleshooting Guide

| Symptom | Likely cause | Action |
|---------|--------------|--------|
| 401 on all API calls | Expired/missing token | Re-login; check refresh token flow |
| Dashboard empty after activity | Worker not running | Restart worker; check `/health/outbox` |
| CORS errors in browser | Wrong `CORS_ORIGINS` | Add frontend URL to `.env` |
| Login works but onboarding loop | Profile incomplete | Complete `/student/onboarding` |
| Mentor queue empty | No open cases | Run seed or trigger mentor projection |
| Case resolve fails | Invalid resolution reason | Use enum values from dropdown |
| Frontend build fails | Missing env | Set `NEXT_PUBLIC_API_BASE_URL` at build time |
| High outbox pending | Worker backlog | Scale workers; check Redis connectivity |
| `/health/ready` degraded | DB or Redis down | Check postgres/redis containers |

### Logs

```bash
docker compose logs api -f
docker compose logs worker -f
docker compose logs web -f
```

### Health endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Liveness |
| `GET /health/ready` | DB + Redis readiness |
| `GET /health/worker` | Celery worker heartbeat |
| `GET /health/outbox` | Outbox pending/failed counts |
| `GET /health/ops` | Combined ops dashboard JSON |

---

## 7. CI/CD Reference

GitHub Actions workflow: `.github/workflows/ci.yml`

| Job | Checks |
|-----|--------|
| `backend` | ruff, mypy, pytest |
| `frontend` | typecheck, lint, build |
| `e2e` | seed + Playwright smoke (14 tests) |
| `docker-frontend` | `docker build` for `apps/web` |

Local E2E:

```bash
# Terminal 1: backend + worker + seed
cd backend && alembic upgrade head && python scripts/seed_demo_data.py
uvicorn prepos.api.main:app --port 8000
celery -A prepos.tasks.celery_app worker -Q default,events

# Terminal 2: frontend
cd apps/web && npm run dev

# Terminal 3: tests
cd apps/web && npx playwright install chromium && npm run test:e2e
```

---

## 8. Pilot Go-Live Checklist

- [ ] `SECRET_KEY` rotated from default
- [ ] `COOKIE_SECURE=true` in production
- [ ] CORS limited to pilot domain
- [ ] Worker + beat running
- [ ] `/health/ops` status `ok`
- [ ] Demo seed or production tenant provisioned
- [ ] Playwright smoke tests pass
- [ ] Database backup scheduled
- [ ] On-call contact identified for worker/outbox alerts

---

*Last updated: Sprint P1.1C*
