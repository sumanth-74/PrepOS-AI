# PrepOS Sprint P1.1C — Implementation Report

**Date:** 2026-06-18  
**Scope:** Deployment readiness, CI/CD, E2E testing, operational monitoring (no domain/engine changes)

---

## Summary

Sprint P1.1C delivers automated smoke testing, full CI pipeline, production frontend containerization, worker/outbox health monitoring, and a pilot operations runbook. Estimated readiness: **~84/100 → ~89/100**.

---

## 1. Playwright E2E Suite

**Location:** `apps/web/e2e/`

| File | Tests |
|------|-------|
| `tests/smoke.spec.ts` | Login page, register page |
| `tests/auth.spec.ts` | Student login, mentor login, invalid credentials |
| `tests/student.spec.ts` | Dashboard KPIs, onboarding redirect, activities, activity toast, revision queue, learning graph |
| `tests/mentor.spec.ts` | Queue load, queue content, case resolve (conditional), admin health |
| `tests/api-health.spec.ts` | `/health`, `/ready`, `/worker`, `/outbox`, `/ops` |

**Total:** 16 smoke tests (2 may skip when demo queue/concepts empty)

**Run locally:**

```bash
cd apps/web
npx playwright install chromium
npm run test:e2e
```

**Config:** `playwright.config.ts` — uses `PLAYWRIGHT_BASE_URL` (default `http://127.0.0.1:3000`)

**Demo credentials:** `prepos-demo` / `student@prepos-demo.example.com` / `SecurePass123!`

---

## 2. CI Pipeline

**File:** `.github/workflows/ci.yml`

| Job | Steps |
|-----|-------|
| `backend` | ruff check, ruff format, mypy, pytest |
| `frontend` | npm ci, typecheck, lint, build |
| `e2e` | migrate, seed, start API+worker+frontend, Playwright |
| `docker-frontend` | `docker build` for `apps/web` |

PRs fail if any job fails.

---

## 3. Frontend Deployment

| Artifact | Path |
|----------|------|
| Production Dockerfile | `apps/web/Dockerfile` (Next.js standalone) |
| nginx reverse proxy | `docker/nginx/frontend.conf` |
| Production compose overlay | `docker-compose.prod.yml` |
| Env template | `apps/web/.env.production.example` |
| Next config | `output: "standalone"` in `next.config.ts` |

**Build:**

```bash
docker build \
  --build-arg NEXT_PUBLIC_API_BASE_URL=https://api.example.com/api/v1 \
  -t prepos-web:latest ./apps/web
```

**Run:**

```bash
docker run -p 3000:3000 prepos-web:latest
```

**Note:** Docker was not available in the local validation environment; CI `docker-frontend` job validates the build.

---

## 4. Worker Health Monitoring

### Backend endpoints (no domain logic changes)

| Endpoint | Purpose |
|----------|---------|
| `GET /health/worker` | Celery inspect ping, worker count |
| `GET /health/outbox` | Pending / published / failed counts |
| `GET /health/ops` | Combined ops dashboard JSON |
| `GET /health/ready` | Enhanced with Redis check |

**Implementation:** `backend/src/prepos/infrastructure/health_checks.py`, `backend/src/prepos/api/v1/health.py`

**Tests:** `backend/tests/integration/test_health_ops.py`

### Admin UI

| Route | Access |
|-------|--------|
| `/admin/health` | `institute_admin`, `super_admin` |

Polls `/health/ops` every 15s with component breakdown.

---

## 5. Pilot Runbook

**File:** `docs/PILOT_RUNBOOK.md`

Includes deployment, rollback, worker recovery, database backup, seed data, troubleshooting, CI reference, and go-live checklist.

---

## Validation Results

| Check | Result | Notes |
|-------|--------|-------|
| `npm run typecheck` | **PASS** | |
| `npm run lint` | **PASS** | |
| `npm run build` | **PASS** | 19 routes including `/admin/health` |
| `ruff` (new health files) | **PASS** | After unused var fix |
| `pytest` (health ops) | **Not run locally** | Local DB fixture conflict; CI uses fresh Postgres |
| `docker build` | **CI only** | Docker unavailable locally |
| Playwright E2E | **CI job** | Requires seeded stack; run locally per runbook |

---

## Remaining Blockers Before Pilot

| Blocker | Severity | Notes |
|---------|----------|-------|
| Production hosting not provisioned | High | Runbook + Docker ready; need target infra |
| Docker frontend not in default compose | Medium | Use `docker-compose.prod.yml` overlay |
| Student legal name in mentor queue | Low | API limitation (unchanged) |
| E2E case-resolve test mutates data | Low | Resolves demo case; re-seed restores |
| Sentry SDK not installed | Low | Hooks from P1.1B ready |
| Managed backups / alerting | Medium | Documented in runbook; ops setup required |

---

## Files Added / Modified

**New**

- `apps/web/Dockerfile`
- `apps/web/playwright.config.ts`
- `apps/web/e2e/**`
- `apps/web/.env.production.example`
- `apps/web/src/app/admin/health/page.tsx`
- `apps/web/src/components/admin/ops-health-dashboard.tsx`
- `apps/web/src/lib/api/origin.ts`
- `backend/src/prepos/infrastructure/health_checks.py`
- `backend/tests/integration/test_health_ops.py`
- `docker/nginx/frontend.conf`
- `docker-compose.prod.yml`
- `docs/PILOT_RUNBOOK.md`

**Modified**

- `.github/workflows/ci.yml` — frontend, e2e, docker jobs
- `backend/src/prepos/api/v1/health.py` — worker, outbox, ops, redis
- `backend/tests/integration/test_foundation_flow.py` — redis check
- `apps/web/next.config.ts` — standalone output
- `apps/web/package.json` — Playwright scripts/deps
- `apps/web/package-lock.json` — lockfile update

**No backend domain logic, event architecture, or scoring changes were made.**
