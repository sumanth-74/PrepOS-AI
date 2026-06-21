# PrepOS AI

**Decision-intelligence platform for competitive exam preparation** — UPSC, APPSC, TSPSC, and coaching institutes.

PrepOS is not a content library or generic chatbot. It tracks each aspirant’s **Preparation Twin**, plans what to study and revise next, and grounds AI answers in institute knowledge — with full tenant isolation and auditable agent operations.

---

## Table of contents

- [What you get](#what-you-get)
- [Tech stack](#tech-stack)
- [Prerequisites](#prerequisites)
- [Quick start](#quick-start)
- [Demo accounts](#demo-accounts)
- [Portals & navigation](#portals--navigation)
- [Project structure](#project-structure)
- [Tests](#tests)
- [Documentation](#documentation)
- [Troubleshooting](#troubleshooting)

---

## What you get

| Layer | Capabilities |
|-------|----------------|
| **Learning** | Learning graph, preparation twin, study plan, revision queue, goals |
| **AI** | Persona Copilot, Knowledge RAG, PYQ & current affairs, recommendations, planning, forecasting, interventions |
| **Agents** | Multi-agent orchestration, critique/reflection, approvals, trace explorer (P8–P10) |
| **Operations** | Admin dashboards, RAG quality, cohort & institution intelligence, security & platform readiness (P11) |

**Portals:** Student · Mentor · Faculty · Admin

For personas, journeys, and screen-by-screen detail → [`docs/PRODUCT_EXPERIENCE_GUIDE.md`](docs/PRODUCT_EXPERIENCE_GUIDE.md)

---

## Tech stack

| Area | Technologies |
|------|----------------|
| Backend | Python 3.13, FastAPI, SQLAlchemy 2.0, Alembic, Pydantic v2 |
| Data | PostgreSQL 17 (+ pgvector), Redis |
| Async | Celery (worker + beat), domain event outbox |
| Frontend | Next.js 15, React 19, TanStack Query, Tailwind |
| AI | OpenAI (embeddings + LLM), hybrid RAG, multi-agent orchestration |
| Observability | Structured logging, OpenTelemetry, Sentry (optional) |

Architecture: **modular monolith**, Clean Architecture, tenant-safe by design.

---

## Prerequisites

| Tool | Version | Required for |
|------|---------|--------------|
| Docker + Compose | 24+ | Easiest local stack (Postgres, Redis, API, Celery) |
| Node.js | 20+ | Frontend dev server |
| Python | 3.13 | Backend without Docker (optional) |
| OpenAI API key | — | Copilot RAG / knowledge Q&A (optional but recommended) |

---

## Quick start

### 1. Configure environment

```bash
cp .env.example .env
# Edit .env: set SECRET_KEY (32+ chars) and OPENAI_API_KEY if using Copilot RAG

cd apps/web
cp .env.local.example .env.local
# NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

### 2. Start backend

**Docker (recommended)**

```bash
docker compose up -d postgres redis api worker beat
docker compose exec api python scripts/seed_demo_data.py
```

**Verify**

```bash
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
```

- API docs: http://localhost:8000/docs  
- Health UI (admin login): http://localhost:3000/admin/health  

Migrations run automatically when the API container starts.

### 3. Start frontend

```bash
cd apps/web
npm ci
npm run dev
```

Open **http://localhost:3000/login**

### One-liner recap

```bash
docker compose up -d postgres redis api worker beat
docker compose exec api python scripts/seed_demo_data.py
cd apps/web && npm run dev
```

---

## Local development (without Docker)

Requires **PostgreSQL** and **Redis** running locally.

```bash
# Terminal 1 — API
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
bash scripts/migrate-db.sh
python scripts/seed_demo_data.py
uvicorn prepos.api.main:app --reload --host 127.0.0.1 --port 8000

# Terminal 2 — Celery worker (twin updates, recommendations, embeddings)
celery -A prepos.tasks.celery_app worker --loglevel=info -Q default,events,knowledge

# Terminal 3 — Frontend
cd apps/web && npm run dev
```

Optional: `celery -A prepos.tasks.celery_app beat` for scheduled outbox publishing.

See [`backend/README.md`](backend/README.md) and [`docs/PILOT_RUNBOOK.md`](docs/PILOT_RUNBOOK.md) for migration repair, worker recovery, and deployment.

---

## Demo accounts

Seed script: `backend/scripts/seed_demo_data.py` · Tenant: **`prepos-demo`**

| Role | Email | Password | Lands on |
|------|-------|----------|----------|
| Student | `student@prepos-demo.example.com` | `SecurePass123!` | `/student/dashboard` |
| Faculty / Mentor | `faculty@prepos-demo.example.com` | `SecurePass123!` | `/mentor/dashboard` |
| Institute Admin | `admin@prepos-demo.example.com` | `SecurePass123!` | `/mentor/dashboard` + admin URLs |

**New institute:** register at http://localhost:3000/register (creates tenant + institute admin).

**Copilot:** floating launcher (bottom-left). Persona follows the URL — `/student/*`, `/mentor/*`, `/admin/*`.

---

## Portals & navigation

Base URL: **http://localhost:3000**

### Student (`student@…`)

| Page | Path |
|------|------|
| Dashboard | `/student/dashboard` |
| Log activity | `/student/activities` |
| Learning graph | `/student/learning-graph` |
| Recommendations | `/student/recommendations` |
| Revision queue | `/student/revision-queue` |
| Study plan | `/student/study-plan` |
| Adaptive planning | `/student/planning` |
| Goal forecasting | `/student/forecasting` |
| Goals | `/student/goals` |
| Twin forecast | `/student/forecast` |
| Learning timeline | `/student/timeline` |

### Mentor (`faculty@…`)

| Page | Path |
|------|------|
| Dashboard | `/mentor/dashboard` |
| Action queue | `/mentor/queue` |
| Interventions | `/mentor/interventions` |
| Cohort | `/mentor/cohort` |
| Student twin | `/mentor/student/[studentId]` |
| Case workspace | `/mentor/cases/[id]` |

### Faculty workspace

| Page | Path |
|------|------|
| Teaching workspace | `/faculty` *(not in mentor sidebar — bookmark or navigate directly)* |

### Admin (`admin@…`)

Admin uses **hub-and-spoke dashboards** (no single sidebar). Start here:

| Area | Start path |
|------|------------|
| Operations | `/admin/health` → `/admin/copilot` → `/admin/knowledge` |
| Intelligence | `/admin/recommendations` → `/admin/cohort` → `/admin/institution` |
| Agents | `/admin/agents` → `/admin/agent-traces` → `/admin/approvals` |
| Maturity (P11) | `/admin/security` → `/admin/platform-readiness` |

**Suggested tour:** health → copilot → knowledge → agents → security → platform-readiness

Full route catalog → [`docs/PRODUCT_EXPERIENCE_GUIDE.md`](docs/PRODUCT_EXPERIENCE_GUIDE.md) §5–6

---

## Project structure

```
PrepOS/
├── backend/                 # FastAPI modular monolith
│   ├── src/prepos/          # application, domain, infrastructure, api
│   ├── alembic/             # database migrations
│   ├── scripts/             # seed_demo_data.py, benchmarks, validation
│   └── tests/
├── apps/web/                # Next.js frontend (student, mentor, admin, faculty)
├── docs/                    # PRD, specs, runbooks, product guide
├── docker/                  # Postgres init, frontend placeholder
├── docker-compose.yml
└── .env.example
```

---

## Tests

```bash
# Backend unit tests
cd backend && uv run pytest tests/unit -q

# Frontend typecheck & lint
cd apps/web && npm run typecheck && npm run lint

# E2E (requires full stack — see CI)
cd apps/web && npm run test:e2e
```

---

## Documentation

| Document | Audience | Contents |
|----------|----------|----------|
| [**Product Experience Guide**](docs/PRODUCT_EXPERIENCE_GUIDE.md) | PM, sales, QA, institutions | Personas, journeys, navigation, AI capabilities |
| [**Pilot Runbook**](docs/PILOT_RUNBOOK.md) | DevOps, ops | Deploy, rollback, worker recovery, backups |
| [**Master Implementation Plan**](docs/MASTER_IMPLEMENTATION_PLAN.md) | Engineering | Architecture, sprints, dependency graph |
| [**Product Requirements**](docs/01-product-requirements.md) | Founders, PM | Vision, scope, positioning |
| [**Mobile UX Checklist**](docs/MOBILE_UX_CHECKLIST.md) | Design, QA | Responsive audit checklist |
| `backend/README.md` | Backend devs | Local API setup, common errors |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| Login works but data is empty | Run `python scripts/seed_demo_data.py` |
| Twin / recommendations never update | Start Celery worker (`worker` service or local celery) |
| Copilot fails on knowledge questions | Set `OPENAI_API_KEY` in `.env`, restart API |
| 401 after ~15 minutes | Sign in again (access token expiry) |
| Frontend cannot reach API | Check `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1` in `apps/web/.env.local` |
| Port 8000 serves wrong app | Use `http://127.0.0.1:8000` instead of `localhost:8000` |
| `duplicate column` on migrate | Run `bash backend/scripts/migrate-db.sh` |
| Frontend build: duplicate export | Ensure single exports in `apps/web/src/lib/api/index.ts` |

---

## License & contribution

PrepOS project. See repository maintainers for contribution and release process.
