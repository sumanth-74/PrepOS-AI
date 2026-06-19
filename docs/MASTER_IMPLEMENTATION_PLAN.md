# PrepOS AI — Master Implementation Plan

Version: 1.1
Status: Principal Architect Review & Execution Plan
Author role: Principal Architect
Scope: Consolidates the Founder Master Blueprint (Parts 1, 2, 3, 5, 6, 7, 8) into a single executable plan.

> **v1.1 change:** Adds **Canonical Implementation Specifications** (§1.10) and aligns sprint deliverables with engine specs + `DOMAIN_EVENTS_SPECIFICATION.md`. Scoring formulas, event contracts, and engine boundaries are **no longer ambiguous** — implement from the canonical spec files, not Part 2 prose alone.

> This document does **not** contain code. It is the planning and decision artifact that all future code must conform to. It supersedes scattered guidance in the individual blueprint parts wherever they conflict; conflicts are explicitly called out in Section 6. **Where a canonical `*_SPECIFICATION.md` exists, it wins over blueprint Part 2/6 prose for that bounded context.**

---

## 0. How to read this document

| Section | Purpose | Primary audience |
|---|---|---|
| 1. Architecture Summary | The system in one place: layers, modules, data, AI | Everyone |
| 1.10 Canonical Specifications | Implementation-ready engine specs (source of truth for code) | Every engineer |
| 2. Development Roadmap | Phased delivery from empty repo to production | Eng lead, Founder |
| 3. Dependency Graph | What must be built before what, and why | Eng lead, every engineer |
| 4. Sprint Plan | Two-week sprints with concrete deliverables | Whole team |
| 5. Definition of Done & Quality Gates | What "finished" means | Whole team |
| 6. Contradictions | Places where the source docs disagree | Founder (decisions needed) |
| 7. Missing Requirements | Things the docs never specified | Founder (decisions needed) |
| 8. Unclear Decisions | Things specified vaguely | Founder (decisions needed) |
| 9. Risk Register | What can go wrong and how we mitigate | Founder, Eng lead |
| 10. Open Decisions Log | Single list of everything needing a founder answer | Founder |

**Teaching note (for a developer new to backend/AI):** A plan like this exists so that you never have to hold the whole system in your head. Each sprint tells you the small slice to build; the dependency graph tells you why that slice comes first; the architecture summary tells you where your code belongs. When in doubt, the layering rules in Section 1.3 win.

---

## 1. Architecture Summary

### 1.1 What PrepOS actually is (one paragraph)

PrepOS is an **AI-native, multi-tenant SaaS** that models each student as a continuously-updated **Preparation Twin** built on top of a per-student **Learning Graph** (mastery / retention / confidence / importance per syllabus concept). Deterministic engines compute the scores; AI agents *interpret* those scores to plan, revise, evaluate, and explain. The relational database (PostgreSQL) is the single source of truth; AI is an intelligence layer on top, never the source of truth.

### 1.2 Architectural style and the non-negotiables

The blueprint commits to a **Modular Monolith** following **Clean Architecture**. The decision is correct for V1 (10k students / 50 institutes) and is explicitly reversible later (extract modules → services).

Seven architecture laws are stated across the docs (Part 3 §26 and Part 6 §30). They are the spine of every code review:

1. **No business logic in API routes.** Routes validate, authenticate, authorize, serialize — nothing more.
2. **Repositories never return ORM models to the API.** They return domain objects / DTOs. (This is the boundary that keeps the monolith modular.)
3. **Agents never touch the database directly.** They call tools; tools call services; services call repositories.
4. **Every AI decision must be explainable.** Reasoning is persisted, not just the output.
5. **Learning Graph is the source of truth** for knowledge state.
6. **Preparation Twin is the intelligence layer** derived from the graph + history.
7. **AI assists decisions; AI never becomes the source of truth.**

Plus two operational laws from Part 6 §30:

8. **Everything is tenant-aware.** Every table has `tenant_id`; every query filters by it.
9. **Every feature is observable** (request_id, tenant_id, user_id on every request; cost/latency on every AI call).

### 1.3 The layers (Clean Architecture mapping)

```
            ┌─────────────────────────────────────────────┐
            │                 API Layer                    │  FastAPI routers
            │   validation · authN · authZ · serialization │  (no business logic)
            └───────────────────────┬─────────────────────┘
                                     │ DTOs only
            ┌───────────────────────▼─────────────────────┐
            │             Application Layer                │  use-cases, services,
            │   use_cases · services · dto · validators    │  orchestration, transactions
            └───────────────────────┬─────────────────────┘
                                     │ domain objects
            ┌───────────────────────▼─────────────────────┐
            │               Domain Layer                   │  entities, value objects,
            │   entities · value objects · rules · events  │  pure business rules (no I/O)
            └───────────────────────┬─────────────────────┘
                                     │ interfaces (ports)
            ┌───────────────────────▼─────────────────────┐
            │            Infrastructure Layer              │  SQLAlchemy repos, Redis,
            │  repositories · db · cache · storage · ext   │  S3, pgvector, OpenAI client
            └─────────────────────────────────────────────┘

   AI Layer (sits beside Application, calls services via tools):
   ai/  agents · graphs(LangGraph) · tools · prompts · memory · evaluation

   Async Layer:
   tasks/ (Celery)  +  events/ (Redis pub/sub) — react to domain events
```

**Dependency rule (the heart of Clean Architecture):** dependencies point *inward only*. Domain knows nothing about FastAPI, SQLAlchemy, Redis, or OpenAI. Infrastructure implements interfaces the domain/application defines. This is what makes the modules independently testable and later extractable.

### 1.4 Module map (16 modules)

From Part 3 §6. Each module owns its models, services, repositories, and APIs.

| # | Module | V1? | Depends on (domain) | Notes |
|---|---|---|---|---|
| 1 | `auth` | V1 | — | JWT + RBAC, tenant resolution |
| 2 | `tenant` | V1 | auth | Multi-tenant root (implied, not named in §6 — see Gap G1) |
| 3 | `student` | V1 | auth, tenant, exam | Profile, onboarding, preferences |
| 4 | `exam` | V1 | tenant | Exam definitions + weights |
| 5 | `syllabus` | V1 | exam | Syllabus graph + concept relationships |
| 6 | `learning_graph` | V1 | student, syllabus | **Core.** Mastery/retention/confidence engine |
| 7 | `revision` | V1 | learning_graph | Retention decay + scheduling |
| 8 | `mentor` | V1 | learning_graph, revision, pyq | Daily/weekly/monthly plans |
| 9 | `pyq` | V1 | exam, syllabus | PYQ ingestion + importance |
| 10 | `assessment` | V1 | learning_graph, student | MCQ (V1), Mains (V3) |
| 11 | `analytics` | V1 | learning_graph, assessment | Student/faculty/institute analytics |
| 12 | `faculty` | V1.5 | tenant, student | Coaching staff |
| 13 | `institute` | V1.5 | tenant, faculty, student | Batch management |
| 14 | `knowledge` | V2 | syllabus | RAG + search |
| 15 | `current_affairs` | V2 | syllabus, knowledge | News → concept mapping |
| 16 | `notifications` | V1 (minimal) | — | In-app first; email/push later |
| + | `billing` | V1.5 | tenant | Subscriptions (named in §6 but undesigned — see Gap G2) |
| + | `ai` | cross-cutting | services only | Agents, graphs, tools, prompts |

### 1.5 Data architecture summary

- **PostgreSQL 17** = single source of truth. JSONB for flexible profiles, `pgvector` for embeddings, full-text search for keyword retrieval. No Elasticsearch / Neo4j / MongoDB in V1 (Part 8 §10).
- **Redis** = cache, Celery broker, sessions, rate limiting, pub/sub event bus.
- **S3** = documents, user uploads, reports, answer sheets. Folder convention `tenant_id/project_id/file` (note: "project_id" is undefined — see Gap G3).
- **pgvector** = single vector store, `embedding vector(3072)` (note: dimension hard-codes a specific OpenAI model — see Risk R7).

Core tables (Part 6 §10): `tenants, users, students, exams, syllabus_nodes, concept_relationships, student_concept_progress (the most important table), preparation_twins, mentor_plans, revisions, assessments, assessment_attempts, current_affairs, pyq_questions, pyq_mappings, knowledge_chunks`.

### 1.6 The scoring model (the IP) — consolidated

> **v1.1 resolution:** Precise formulas, weights, and presentation rules are defined in **`SCORING_ENGINE_SPECIFICATION_V1_1.md`** (Readiness R3 Option A, prediction gating, Engine vs Display scores) with Mastery/Retention/Importance/Confidence/Weakness/Priority details in the v1.0 scoring layer referenced therein. **Importance** computation is specified in **`PYQ_INTELLIGENCE_SPECIFICATION.md`**. **Revision Priority** (weighted additive v1.1) is in **`REVISION_ENGINE_SPECIFICATION.md` §5**. Treat the table below as a **summary only**.

These formulas are the product's moat and must be implemented as **deterministic, versioned, unit-tested** functions in the domain layer.

| Score | Range | Formula (summary) | Canonical spec |
|---|---|---|---|
| **Importance (Exam Weight)** | 0–100 | PYQ frequency + trend + exam relevance + faculty weight | `PYQ_INTELLIGENCE_SPECIFICATION.md` §8–§13 |
| **Mastery** | 0–100 | 40% MCQ + 30% Mains + 20% Revision + 10% Study | Scoring v1.0 §2 (via v1.1) |
| **Confidence** | 0–100 | Self-assessment + speed + consistency (internal; overconfidence flag only in UI) | Scoring v1.0 §13; v1.1 R4 |
| **Retention** | 0–100 | Stability-modulated exponential decay | Scoring v1.0 §3; LG §8.2 |
| **Revision Priority** | 0–100 | Weighted additive: importance, retention gap, weakness, proximity, CA | `REVISION_ENGINE_SPECIFICATION.md` §5 |
| **Revision Health** | 0–100 | On-time completion credit over scheduled window | Scoring v1.0 §6 |
| **Readiness Score** | 0–100 | Weighted KnowledgeSub (MasteryNonMCQ) + Retention + MCQ + Writing + CA | `SCORING_ENGINE_SPECIFICATION_V1_1.md` §4 |

> **Architect note (historical):** Part 2 stated formulas as *intent without weights*. That gap is closed by the canonical scoring and engine specs above. Sprint S4–S7 implement from those documents, not from Part 2 prose.

### 1.7 AI architecture summary

- **Hybrid**: deterministic engines (scoring, scheduling, analytics) + AI agents (planning, evaluation, explanation, mentoring). Rule: *never use an LLM where an algorithm suffices* (Part 3 §11).
- **Multi-agent under a Supervisor** (Part 5): Supervisor routes intent → Mentor / Revision / Assessment / Knowledge / Current Affairs / Faculty / Institute agents.
- **Orchestration**: LangGraph with a shared `GraphState` (student_id, tenant_id, intent, messages, learning_graph, preparation_twin, tool_results, agent_outputs).
- **Tools, not DB**: agents call registered tools (`GetLearningGraphTool`, `GetWeakTopicsTool`, etc.) which call services.
- **Memory (3 layers)**: conversation (short-term) → student preferences (long-term) → Preparation Twin (the durable intelligence).
- **Cost tiering**: small model (classify/route/tag) → mid model (plan/explain) → frontier reasoning model (Mains eval, interview, prediction). Target 60–80% cost reduction.
- **Eval framework from day one**: hallucination rate, recommendation quality, plan accuracy, answer-eval quality — stored and tracked over time.
- **Human-in-the-loop**: faculty override AI scores/plans; overrides are captured as training signal.

### 1.8 Frontend architecture summary

- **Next.js 15 / React 19 / TypeScript / Tailwind / shadcn/ui**, feature-based folders.
- **React Query** for server state, **Zustand** for client/UI state, **React Hook Form + Zod** for forms.
- **Recharts** first, **ECharts** later for the interactive Learning Graph visualization.
- UX law: always answer *"What should I do next?"* and *"Why?"*; Preparation Twin visible everywhere; avoid chatbot-first design; mobile-first (RN later).

### 1.9 Deployment topology summary

- **Dev**: Docker Compose (api, worker, beat, frontend, postgres, redis).
- **Staging**: AWS EC2 + Docker, auto-deploy.
- **Production**: CloudFront → WAF → ALB → ECS Fargate → RDS PostgreSQL (Multi-AZ) + ElastiCache Redis + S3. Secrets in AWS Secrets Manager. Observability via CloudWatch + Sentry + OpenTelemetry. Production deploys require manual approval.

### 1.10 Canonical implementation specifications

The following documents are **implementation-ready** and supersede blueprint prose for their bounded contexts. All new backend work MUST conform to them. Cross-engine integration MUST conform to **`DOMAIN_EVENTS_SPECIFICATION.md`**.

| Spec file | Bounded context | Sprint(s) | Status |
|---|---|---|---|
| `EXAM_DOMAIN_SPECIFICATION.md` | Exam → Subject → Topic → Concept taxonomy | S2 | Ready |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Readiness, display scores, prediction gating | S4, S11 | Ready (delta on v1.0 math) |
| `SCORING_ENGINE_REVIEW.md` | R1–R8 rationale (reference only) | — | Reference |
| `LEARNING_GRAPH_SPECIFICATION.md` | `student_concept_progress`, graph events | S4+ | Ready |
| `REVISION_ENGINE_SPECIFICATION.md` | Revision queue, priority v1.1, sessions | S5 | Ready |
| `PREPARATION_TWIN_SPECIFICATION.md` | Twin profiles, projection pipelines | S6 | Ready |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | PYQ ingestion, Importance engine | S7 | Ready |
| `MENTOR_AGENT_SPECIFICATION.md` | Plans, tools, interventions | S8 | Ready |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | MCQ, mocks, recall sessions | S9–S10 | Ready |
| `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` | CA ingestion, linking, CASub inputs | S17 (V2) | Ready |
| `DOMAIN_EVENTS_SPECIFICATION.md` | Outbox, idempotency, event registry | S0–S1 infra + all | Ready |

**Hierarchy of truth:** Canonical spec → this Master Plan → Blueprint Parts 1–8. **`06-api-spec.md`** API list is indicative; engine spec API sections win on conflict.

**Event spine (critical path):**

```
AssessmentCompleted / RevisionCompleted / StudySessionLogged
  → Learning Graph → LearningGraphUpdated → Preparation Twin → Mentor (read tools)
PYQDataChanged → Learning Graph (importance copy)
CurrentAffairsPublished → Revision (CA relevance); Mentor cache (V2)
```

---

## 2. Development Roadmap

### 2.1 Reconciling the two roadmaps in the docs

The blueprint contains **two different phase plans that disagree** (see Contradiction C1):

- **Part 6 §28** (engineering): 6 phases × 4 weeks = 24 weeks. Assessment (incl. Mains) in Phase 3; Knowledge/RAG in Phase 4.
- **Part 8 §35** (CTO verdict): 4 phases × ~4 months. Mains evaluation deferred to *Phase 3 (months 9–12)*; RAG pulled forward to Phase 2 (months 5–8).

**Architect's resolution (recommended):** Follow the **CTO sequencing intent** (Part 8) because it is risk-ordered — it front-loads the defensible moat (Learning Graph, Revision, Mentor, MCQ) and defers the two hardest, least-reliable pieces (Mains AI evaluation, RAG quality) until the core retention loop is proven. But keep the **2-week sprint cadence** from a normal agile process rather than month-blocks, so progress is visible every two weeks. The phases below are the merged result. *This merge needs founder confirmation (Open Decision D1).*

### 2.2 Phase overview (merged, recommended)

| Phase | Theme | Sprints | Calendar (approx) | Exit criteria (must all be true) |
|---|---|---|---|---|
| **P0** | Foundation & Walking Skeleton | S0–S1 | Weeks 1–4 | Repo scaffolded, CI green, one tenant can register/login, one request traced end-to-end |
| **P1** | Knowledge Core | S2–S4 | Weeks 5–10 | Exams + syllabus graph + Learning Graph live; scores computed deterministically with tests |
| **P2** | Retention Loop | S5–S6 | Weeks 11–14 | Revision engine (nightly decay + scheduling) + Preparation Twin populated |
| **P3** | Guidance Loop | S7–S8 | Weeks 15–18 | Mentor agent produces explainable daily/weekly/monthly plans; PYQ importance feeds it |
| **P4** | Assessment (MCQ) | S9–S10 | Weeks 19–22 | MCQ create→attempt→score→update graph→update twin, fully closed loop |
| **P5** | Student App Surface | S11–S12 | Weeks 23–26 | Student dashboard, learning-graph screen, revision & mentor workspaces usable end-to-end |
| **P6** | Institutes & Faculty | S13–S14 | Weeks 27–30 | Faculty + batch + institute analytics; billing/subscription enforcement |
| **P7** | Knowledge & Current Affairs (V2) | S15–S17 | Weeks 31–36 | RAG pipeline + hybrid search + CA→concept mapping with eval gates |
| **P8** | Mains AI Evaluation (V2/V3) | S18–S19 | Weeks 37–40 | Mains submit→AI eval→human override→update twin, with eval-quality thresholds |
| **P9** | Production Hardening | S20–S21 | Weeks 41–44 | Full AWS prod topology, monitoring, security, DR, load-tested to V1 targets |

> **Sequencing rationale:** P0–P4 build and *prove* the retention loop (the moat) with mostly deterministic logic. The riskiest AI (RAG hallucination, Mains scoring reliability) is intentionally last among feature work (P7–P8), after we have real student data and an eval harness. Production hardening (P9) is a dedicated phase, but observability and tenancy are built in from P0, not bolted on.

### 2.3 What is explicitly out of scope for V1

Mobile apps, multi-language, white-label, marketplace, AI faculty assistant, interview coach, voice mentor (PRD V2/V3). The architecture must *not block* these (e.g., API-first so React Native can reuse it) but we build none of them.

---

## 3. Dependency Graph

### 3.1 Reading the graph

An arrow `A → B` means **B depends on A** (A must exist first). This drives sprint ordering in Section 4. The graph is split into *infrastructure*, *domain*, and *AI/experience* tiers because they parallelize differently.

### 3.2 Infrastructure & cross-cutting (built once, used everywhere)

```
Repo scaffold + Clean Architecture skeleton
        │
        ├──► Config & Settings (Pydantic Settings, env injection)
        ├──► DB engine + session + migrations (SQLAlchemy 2.0 + Alembic)
        ├──► Tenancy primitive (tenant_id context + query enforcement)
        ├──► Observability (request_id / tenant_id / user_id middleware, logging schema)
        ├──► Auth (JWT access/refresh, RBAC, password hashing)
        ├──► Event bus (Redis pub/sub) + Celery (worker, beat, queues)
        └──► Error tracking + health checks
```

These are **prerequisites for everything**. Tenancy and observability in particular must precede any feature module or they become impossible to retrofit safely.

### 3.3 Domain dependency chain (the critical path)

```
exam ──► syllabus ──► (concept_relationships)
                          │
student ──────────────────┼──► learning_graph (student_concept_progress)   ◄── THE CORE
   ▲                      │           │
   │                      │           ├──► revision (retention decay, scheduling)
 auth/tenant              │           │            │
                          │           │            ▼
                pyq ──► (importance)   │     Preparation Twin (knowledge/behavior/
                          │           │            assessment/prediction profiles)
                          │           │                    │
                          └───────────┴────────────────────┼──► mentor (daily/weekly/monthly plans)
                                                            │
assessment (MCQ) ───────────────────────────────────────────┘
   │   (closes the loop: attempt → score → update learning_graph → update twin)
   ▼
analytics (student → faculty → institute)
```

**The critical path is:** `auth/tenant → exam → syllabus → learning_graph → revision → twin → mentor → assessment → analytics`. Everything else hangs off this spine. If any one link slips, downstream slips. Protect this path.

### 3.4 Why this order (key justifications)

- **Learning Graph before everything intelligent.** Revision, Twin, Mentor, and Analytics all *read* the graph. Building any of them first would force mocking the graph, violating the "no mock implementations" rule.
- **Syllabus before Learning Graph.** A student's progress is *per syllabus concept node*; without the concept tree there is nothing to attach scores to.
- **PYQ before Mentor (and before final Importance).** Importance score (a Mentor input) depends on PYQ frequency/trend. Mentor can run with a degraded importance (faculty-weight only) earlier, but quality plans need PYQ.
- **Revision + Twin before Mentor.** The Mentor's daily plan is literally `f(learning_graph, twin, pyq, revision)`. Mentor is an *integrator*; it must be last among the intelligence engines.
- **Assessment closes the loop.** It is both a consumer (reads graph to pick questions) and the most important *writer* (its results drive mastery). It needs the graph write-path to exist first.
- **Analytics is aggregation.** It is genuinely last among data features because it summarizes everything above it.

### 3.5 AI & frontend dependency overlay

```
Tool Layer (wraps services)  ──►  Supervisor Agent  ──►  per-agent graphs (LangGraph)
        ▲                                                        │
        │ services must exist first                              ▼
learning_graph/revision/mentor/assessment services      Prompt registry + Eval harness
                                                                 │
Frontend design system (shadcn) ──► auth screens ──► dashboard ──► graph/revision/mentor/assessment screens
```

- **Tools depend on services**, so no agent work is real until the underlying service exists. (You can scaffold the tool *interface* early, but not a working tool.)
- **Eval harness should precede heavy agent reliance** so we never ship an agent we can't measure.
- **Frontend can start its design system and auth screens in parallel with backend P0–P1**, but feature screens must trail their backing APIs by ~1 sprint.

### 3.6 Parallelization guidance

| Can run in parallel | Reason |
|---|---|
| Infra hardening + frontend design system | No shared code |
| `exam` + `syllabus` ingestion tooling + PYQ ingestion tooling | Different tables, only loosely linked |
| Backend feature N + Frontend feature N-1 | API contract is the seam |
| Eval harness + Mentor agent | Harness measures the agent |

| Must be strictly sequential | Reason |
|---|---|
| Tenancy/observability → any feature | Cannot retrofit safely |
| Learning Graph → Revision/Twin/Mentor/Analytics | They all read it |
| Service → Tool → Agent | Architecture law #3 |

---

## 4. Sprint Plan

**Cadence:** 2-week sprints. **Assumption:** small senior team (≈2–3 backend, 1 frontend, shared AI/devops). Velocity and team size are *not specified in the docs* — see Gap G5; adjust sprint count if the real team differs. Each sprint lists **Goal**, **Backend**, **AI/Frontend/Infra**, and **Sprint exit (Definition of Done)**.

> Sprints are scoped to be independently shippable behind feature flags. No sprint depends on a future sprint. Tests ship *with* each feature (rule 15), not after.

### Phase P0 — Foundation & Walking Skeleton

**Sprint S0 — Repo, skeleton, CI**
- Goal: An empty but *correct* monolith that builds, lints, tests, and runs in Docker Compose.
- Backend: Clean Architecture folder skeleton (`api/application/domain/infrastructure/ai/events/tasks/tests`); Pydantic Settings config; SQLAlchemy 2.0 engine/session; Alembic baseline migration; health endpoint; **event outbox skeleton per `DOMAIN_EVENTS_SPECIFICATION.md` §3**.
- Infra: Docker Compose (api, worker, beat, postgres, redis, frontend placeholder); GitHub Actions pipeline (lint → test → build); pre-commit hooks; Sentry + OpenTelemetry wiring stubs.
- Exit: `docker compose up` runs; CI is green on an empty test; one migration applies; structured log line emits `request_id/tenant_id/user_id`; outbox table + publisher stub exists.

**Sprint S1 — Tenancy, Auth, Observability spine**
- Goal: A tenant can register and log in; every request is traced and tenant-scoped.
- Backend: `tenant` + `auth` modules; users table; JWT access (15m) + refresh (7d) in HttpOnly cookies; RBAC roles (student/faculty/institute_admin/super_admin); password hashing; tenant-context middleware + repository-level `tenant_id` enforcement; audit-log skeleton.
- AI/FE: Frontend design system bootstrap (shadcn/Tailwind); login/register screens wired to auth.
- Exit: Register → login → authenticated `GET /students/me` returns 401 without token, 200 with; every query provably filtered by `tenant_id`; rate limiting on auth endpoints.

### Phase P1 — Knowledge Core

**Sprint S2 — Exams & Syllabus graph**
- Goal: Model exams and the syllabus as a graph.
- Backend: `exam` module; **`EXAM_DOMAIN_SPECIFICATION.md`** taxonomy (`concepts`, `subjects`, `topics`, `concept_relationships` — replaces informal `syllabus_nodes` tree from Part 6); admin ingestion + seed-loading (`seeds/upsc_cse_concepts_v1_0.json` target).
- FE: Super-admin syllabus browser (read).
- Exit: UPSC CSE catalog loads per EXAM_DOMAIN; concept IDs stable; `DomainCatalogUpdated` event on publish.

**Sprint S3 — Student profile & onboarding**
- Goal: A student exists with goals and preferences.
- Backend: `student` module (target_exam, target_year, daily_hours, experience_level, onboarding_completed); onboarding use-case that provisions an (empty) Learning Graph and Preparation Twin shell for the student.
- FE: Onboarding flow (exam, year, hours, level).
- Exit: New student completes onboarding; empty `student_concept_progress` rows (or lazy strategy) + `preparation_twins` row created; reproducible via test.

**Sprint S4 — Learning Graph engine (deterministic core)**
- Goal: The single most important table and its update service.
- Backend: **`LEARNING_GRAPH_SPECIFICATION.md`** — `learning_graph` module; `student_concept_progress`; Mastery + Confidence (Scoring v1.0); event handlers for `StudySessionLogged`, `AssessmentCompleted`, `RevisionCompleted`; emits `LearningGraphUpdated`; idempotency + outbox per **`DOMAIN_EVENTS_SPECIFICATION.md`**. Retention/Importance handlers stubbed until S5/S7 then wired to specs.
- FE: Learning-graph read API contract published.
- Exit: Given known inputs, mastery/confidence computed deterministically; event chain tested; row versioning per LG §4.

### Phase P2 — Retention Loop

**Sprint S5 — Retention & Revision engine**
- Goal: Fight forgetting on a schedule.
- Backend: **`REVISION_ENGINE_SPECIFICATION.md` (v1.1)** — `revision` module; Retention decay (Scoring v1.0 §3 + LG §8.2); weighted additive **Revision Priority** §5; nightly plan generation; `RevisionCompleted` + session aggregates; CA relevance §9 consumes `CurrentAffairsPublished` (stub OK pre-S17).
- Infra: Celery `revision` queue per **`DOMAIN_EVENTS_SPECIFICATION.md` §19**.
- Exit: Nightly job produces deterministic revision list; completion emits `RevisionCompleted` → LG update; frozen-clock tests pass.

**Sprint S6 — Preparation Twin**
- Goal: Derive the intelligence layer from graph + history.
- Backend: **`PREPARATION_TWIN_SPECIFICATION.md`** — `preparation_twins` JSONB profiles; Twin-builder subscribing to events per §15 + **`DOMAIN_EVENTS_SPECIFICATION.md` §8**; debounced rebuild; Revision Health/Fatigue/Streak from Revision events; Readiness via **`SCORING_ENGINE_SPECIFICATION_V1_1.md` §4**.
- FE: Preparation Twin screen (strongest/weakest subject, most-forgotten topic).
- Exit: Event-driven rebuild idempotent; `TwinUpdated` emitted; profiles match graph after activity.

### Phase P3 — Guidance Loop

**Sprint S7 — PYQ Intelligence & real Importance**
- Goal: Make Importance real and feed the Mentor.
- Backend: **`PYQ_INTELLIGENCE_SPECIFICATION.md`** — `pyq` module; ingestion; Importance engine; `PYQDataChanged` → LG importance copy; faculty weights.
- FE: Exam Weight badge on syllabus/graph nodes (Scoring v1.1 R5 label).
- Exit: Deterministic Importance recompute; backfill graph `importance_score`; event chain per DOMAIN_EVENTS §8.3.

**Sprint S8 — Mentor engine + Supervisor/Mentor agent**
- Goal: Explainable daily/weekly/monthly plans.
- Backend: **`MENTOR_AGENT_SPECIFICATION.md`** — deterministic plan assembly; `mentor_plans` + `reasoning_json`; tool gateway (Twin, Graph, Revision, PYQ, Assessment gaps, CA priorities stub).
- AI: LangGraph Supervisor → Mentor; eval harness v1; agents via tools only (Rule #3).
- Exit: Every task has `reasoning_json`; `MentorPlanGenerated` event; tool-only DB access enforced by test.

### Phase P4 — Assessment (MCQ)

**Sprint S9 — MCQ create & attempt**
- Goal: Create and take an MCQ assessment.
- Backend: **`ASSESSMENT_ENGINE_SPECIFICATION.md`** §6–§11 — `assessment` module; question selection; attempt lifecycle; guessing/confidence capture; recall session API for Revision.
- FE: MCQ test interface (timer, confidence marking, bookmarks).
- Exit: MCQ attempt stored; **no** graph update yet (isolated de-risk).

**Sprint S10 — MCQ scoring closes the loop**
- Goal: Assessment results flow into graph and twin.
- Backend: **`ASSESSMENT_ENGINE_SPECIFICATION.md`** §13–§20 + **`DOMAIN_EVENTS_SPECIFICATION.md` §8.1** — `AssessmentCompleted` outbox → LG → `LearningGraphUpdated` → Twin debounce.
- FE: Post-test analysis + weak concepts + graph deltas.
- Exit: Full **create→attempt→score→graph→twin** loop demonstrable end-to-end.

### Phase P5 — Student App Surface

**Sprint S11 — Student dashboard & Learning Graph screen**
- Goal: The product's home.
- FE: Dashboard (greeting, target, Readiness Score, Today's Plan, Revision Health, Mastery, streak); interactive Learning Graph visualization (Recharts; color system green/yellow/red; expandable nodes with mastery/retention/importance/confidence).
- Backend: `GET /analytics/dashboard`; **Readiness Score** composite defined and implemented (per D3); dashboard aggregation endpoints.
- Exit: A real student sees a coherent dashboard driven entirely by live data; Readiness Score is explainable.

**Sprint S12 — Revision & Mentor workspaces**
- Goal: Daily usable loops.
- FE: Revision workspace (today/overdue/upcoming cards); Mentor workspace (proactive suggestions + plan + chat area, *not* chatbot-first); "Why?" on every recommendation.
- Backend: WebSocket `/ws` for AI token streaming + `plan_generated`/`assessment_complete` events.
- Exit: A student can run an entire day (see plan → study → revise → MCQ) inside the app; mentor proactively guides.

### Phase P6 — Institutes & Faculty

**Sprint S13 — Faculty, batches, institute analytics**
- Goal: B2B surface (the revenue center).
- Backend: `faculty`, `institute` modules; batch model; institute/faculty analytics (weak/strong topics, batch health, risk students); human-in-the-loop override of AI scores/plans (captured as signal).
- FE: Faculty dashboard + Institute dashboard + batch analytics + risk dashboard.
- Exit: An institute admin sees batch health; a faculty member overrides an AI score and the override is recorded.

**Sprint S14 — Billing & subscription enforcement**
- Goal: Plans actually gate features.
- Backend: `billing` module; plan/tier model (Individual/Premium/Institute); entitlement checks in the application layer; payment-provider integration (**provider unspecified — see Gap G2/D4**).
- FE: Plan selection + upgrade flows.
- Exit: Feature access is enforced per plan; subscription state is auditable. *(If payment provider is undecided, ship entitlement logic with a stubbed provider gated behind a flag — flagged as the one deliberate stub, pending D4.)*

### Phase P7 — Knowledge & Current Affairs (V2)

**Sprint S15 — RAG ingestion pipeline**
- Backend: `knowledge` module; `knowledge_chunks` (`vector(3072)`); ingestion pipeline upload→extract→chunk(500–800 tok, 100 overlap)→embed→store; S3 source storage; Celery `ingestion` queue.
- Exit: A document is ingested end-to-end; chunks are searchable by vector similarity.

**Sprint S16 — Hybrid search + Knowledge agent**
- Backend: hybrid retrieval (pgvector + Postgres full-text); `POST /knowledge/ask`.
- AI: Knowledge agent + tools; **eval gate**: hallucination-rate threshold must pass before exposure.
- Exit: Concept queries return grounded answers with PYQ/mains relevance; hallucination metric below agreed threshold (per D5).

**Sprint S17 — Current Affairs intelligence**
- Goal: CA catalog, linking, and Mentor CA slots (V2).
- Backend: **`CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md`** — `current_affairs` module; ingestion; concept linking; `CurrentAffairsPublished` / `CurrentAffairsEngaged`; CASub inputs (V2); `GET /current-affairs`.
- AI: Current Affairs Agent (explanation only — CA spec §24 boundary).
- Exit: Published CA item mapped to concepts with auditable links; Mentor `GetCurrentAffairsPrioritiesTool` populated; optional V1 seed corpus for demos.

### Phase P8 — Mains AI Evaluation (V2/V3)

**Sprint S18 — Mains submission & AI evaluation**
- Backend: extend `assessment` for Mains/Essay; submission storage (S3 answer sheets).
- AI: Assessment agent for Mains (frontier reasoning model) evaluating structure/content/examples/keywords/flow; eval harness for answer-eval quality.
- Exit: A Mains answer receives an AI evaluation with score + strengths + weaknesses + improved answer; quality metric tracked.

**Sprint S19 — Human override & loop closure**
- Backend: faculty override of Mains scores; override → training-signal store; Mains results update graph (30% of mastery) + twin.
- Exit: Mains create→AI eval→human override→graph/twin update is closed and tested; overrides captured.

### Phase P9 — Production Hardening

**Sprint S20 — AWS production topology & security**
- Infra: ECS Fargate services (api/worker/beat/frontend); RDS Multi-AZ; ElastiCache; S3 buckets (documents/user-content/backups); CloudFront + WAF (managed rules); Secrets Manager; per-env AWS accounts; manual-approval prod deploys.
- Security: TLS everywhere, AES at rest, audit-log completeness, prompt-injection guardrails, tenant-isolation tests.
- Exit: Staging→prod promotion works with manual gate; secrets never in code/images; WAF active.

**Sprint S21 — Observability, DR, load & cost**
- Infra: CloudWatch dashboards + alerts; Sentry; OpenTelemetry traces with request_id/tenant_id; AI cost monitoring per user/institute/feature/agent; DR (Postgres daily backups, S3 versioning, Redis snapshots) validated against RPO<24h / RTO<4h; load test to V1 targets (10k students, thousands of concurrent assessments).
- Exit: Dashboards live; a restore drill passes RPO/RTO; load test meets targets; AI cost is attributable.

### 4.1 Sprint summary table

| Sprint | Phase | Headline deliverable | Closes which dependency |
|---|---|---|---|
| S0 | P0 | Repo + CI + Compose skeleton | Unblocks all |
| S1 | P0 | Tenancy + Auth + Observability | Unblocks all features |
| S2 | P1 | Exams + Syllabus graph | Unblocks Learning Graph |
| S3 | P1 | Student onboarding | Unblocks per-student data |
| S4 | P1 | Learning Graph engine | Unblocks Revision/Twin/Mentor/Assessment |
| S5 | P2 | Retention + Revision | Unblocks Twin/Mentor |
| S6 | P2 | Preparation Twin | Unblocks Mentor quality |
| S7 | P3 | PYQ + real Importance | Unblocks Mentor quality |
| S8 | P3 | Mentor + Supervisor agent | First AI value |
| S9 | P4 | MCQ create/attempt | Unblocks scoring |
| S10 | P4 | MCQ scoring closes loop | Proves the moat loop |
| S11 | P5 | Dashboard + Graph screen | Product is visible |
| S12 | P5 | Revision + Mentor workspaces | Daily-usable product |
| S13 | P6 | Faculty + Institute analytics | B2B value |
| S14 | P6 | Billing enforcement | Revenue |
| S15 | P7 | RAG ingestion | Unblocks Knowledge agent |
| S16 | P7 | Hybrid search + Knowledge agent | V2 knowledge |
| S17 | P7 | Current Affairs | V2 CA |
| S18 | P8 | Mains AI evaluation | Hardest AI |
| S19 | P8 | Human override loop | Trust + signal |
| S20 | P9 | AWS prod + security | Go-live readiness |
| S21 | P9 | Observability + DR + load | Operability |

---

## 5. Definition of Done & Quality Gates

Applies to **every** sprint (operationalizes the user rules + Part 6 §27).

1. **Layering respected** — no business logic in routes; repos return DTOs/domain objects, not ORM models; agents reach data only via tools→services.
2. **Tenant-aware** — every new query filtered by `tenant_id`; a negative test proves cross-tenant access fails.
3. **Typed** — full Python type hints; Pydantic v2 models for all I/O; SQLAlchemy 2.0 typed models.
4. **Tested** — unit tests for all domain logic (scoring functions: 100%), integration tests for repositories/services, contract tests for APIs; target ≥80% coverage (Part 6 §27). AI features add eval tests.
5. **Observable** — emits structured logs with request_id/tenant_id/user_id; AI calls record model/prompt-version/tokens/cost/latency.
6. **Explainable (AI)** — any recommendation/score from AI persists its reasoning.
7. **Migrations** — schema changes ship as Alembic migrations, reversible.
8. **No placeholders / no unrequested mocks** — the single allowed exception is the payment provider stub in S14, explicitly flagged and feature-gated, pending D4.
9. **Docs** — each feature documents purpose, flow, alternatives considered, and tradeoffs (per user rules 11 & 13).

---

## 6. Contradictions (found in the source docs)

| ID | Contradiction | Where | Impact | Recommended resolution |
|---|---|---|---|---|
| **C1** | Two different roadmaps. Part 6 §28 = 6×4-week phases with Assessment(incl. Mains) in Phase 3 and Knowledge/RAG in Phase 4. Part 8 §35 = 4 phases over a year with Mains deferred to months 9–12 and RAG in months 5–8. | Part 6 §28 vs Part 8 §35 | Different teams could build to different orders. | Adopt the merged roadmap in §2 (CTO risk-ordering + 2-week cadence). **Needs sign-off (D1).** |
| **C2** | Document part numbering is inconsistent. File `03-system-architecture.md` is titled "Part 3" but ends "END OF PART 2"; file `06` is "Part 6" but ends "End of Part 6" while `03` is the 3rd file. Parts are also non-contiguous (1,2,3,5,6,7,8) — **Part 4 is missing** from the repo. | File headers/footers vs filenames | Reader confusion; a whole part (likely DB schema deep-dive or AI part) may be absent. | Treat Part 4 as **missing requirement (G7)**; renumber/normalize the docs. |
| **C3** | AI model naming. Part 8 §23 says "GPT + Anthropic (Claude) for long-context evaluation." Part 5 §23 specifies an all-OpenAI tier ladder (GPT-4.1 Mini / GPT-4.1 / GPT-5-class) and only parenthetically says "use strongest available." Part 3 §4 lists only "OpenAI SDK." | Part 3 §4 vs Part 5 §23 vs Part 8 §23 | Ambiguity on whether Anthropic is in V1 and which SDK(s) to integrate. | Pick a provider strategy + abstraction (see D6). Recommend a provider-agnostic LLM gateway interface so either works. |
| **C4** | Pricing inconsistency. PRD Individual plan = ₹499–999/mo; Part 8 §32 Individual = ₹299–999/mo. Institute: PRD says "annual license"; Part 8 §32 says ₹25,000–2,00,000/**month**. | PRD §Revenue vs Part 8 §32 | Billing module (S14) can't encode tiers reliably. | Founder to fix canonical pricing (D4). |
| **C5** | Vector dimension vs model tier. Part 6 §11 hard-codes `embedding vector(3072)` (an OpenAI `text-embedding-3-large` dimension), but Part 5 §23 leaves models open and Part 8 allows Anthropic. Anthropic has no first-party embedding model at that dimension. | Part 6 §11 vs Part 5/§8 | A hard-coded dimension locks the embedding model and breaks if provider changes. | Make embedding model/dimension a config decision (D7); store model+dim alongside each chunk. |
| **C6** | "Mains in V1" vs "Mains later." PRD V1 Must-Have lists "Assessment Engine" broadly and Part 6 §28 puts Mains in Phase 3 of V1; but Part 8 §35 (CTO) explicitly defers Mains evaluation to months 9–12 and Part 5 lists Essay/Interview as V2. | PRD vs Part 6 §28 vs Part 8 §35 vs Part 5 | Scope of "V1 assessment." | Resolve via §2 plan: **MCQ in V1 (P4), Mains in V2/V3 (P8)**. Confirm (D1). |
| **C7** | "frequently_asked_with" relationship exists in domain (Part 2 §8) but the Importance formula references "PYQ Frequency/Trend" without using concept co-occurrence; unclear if the relationship is used by any engine. | Part 2 §8 vs §10 | Possible dead data model or missing engine logic. | Clarify intended use (D8) — likely a future PYQ-clustering input. |

---

## 7. Missing Requirements (never specified)

| ID | Missing item | Why it matters | Suggested default (pending founder) |
|---|---|---|---|
| **G1** | A named `tenant`/tenant-provisioning module. §6 lists 16 modules but omits the tenant module even though every table is tenant-scoped. | Tenancy is the backbone; it can't be implicit. | Treat `tenant` as a first-class V1 module (done in §1.4 / S1). |
| **G2** | Billing/payments design. `billing` is named (Part 6 §6) but no provider, data model, invoicing, taxes (GST), refunds, or proration is specified. | Revenue + India tax compliance. | Pick provider (Razorpay/Stripe) + design in S14 (D4). |
| **G3** | `project_id` in the S3 path convention `tenant_id/project_id/file` is never defined anywhere in the domain. | Storage layout undefined; could break uploads. | Replace with a defined scope (e.g., `tenant_id/student_id/...` or `tenant_id/resource_type/...`) (D9). |
| **G4** | ~~**Readiness Score** definition.~~ | **Resolved in v1.1:** `SCORING_ENGINE_SPECIFICATION_V1_1.md` §4 (R3 Option A). | Implemented in S6 Twin + S11 dashboard. |
| **G5** | Team size, roles, and velocity. No staffing is stated, yet the roadmap implies effort. | Sprint counts and dates are guesses without it. | Provide team composition (D10). |
| **G6** | Prediction Engine model. "Predicted Prelims 84±6" is shown, but no method, training data, or accuracy target is defined. | It's a stated moat (Level 6) but unbuildable as specified. | Defer to post-V1; start as heuristic + confidence interval; revisit with data (D11). |
| **G7** | **Part 4 of the blueprint is absent** from the repo (parts jump 3→5). Likely contains DB schema depth or another AI/infra spec. | We may be missing canonical requirements. | Locate/author Part 4 or confirm it's intentionally dropped. |
| **G8** | Data sourcing & licensing for PYQs, NCERT, Laxmikanth, Spectrum, PIB/PRS, Economic Survey. RAG/PYQ engines assume this content exists. | Legal/IP risk; the moat depends on data we must lawfully obtain. | Define content acquisition + licensing plan (D12). |
| **G9** | Privacy/compliance specifics for Indian users (DPDP Act 2023), data retention, consent, deletion, minors. Only "Basic Security Year 1" is stated. | Legal exposure handling student PII + behavior. | Add a DPDP-compliance baseline to P9 (D13). |
| **G10** | Notification delivery providers (email/push/WhatsApp) and templates. Channels are named; providers and triggers-to-template mapping are not. | Notifications are in V1 (minimal). | Pick providers (e.g., SES + FCM) (D14). |
| **G11** | Internationalization/timezone handling. "Nightly" retention jobs + study times imply a timezone, never specified (India-only? per-user TZ?). | Wrong TZ corrupts retention/revision timing. | Default to per-user timezone, store UTC (D15). |
| **G12** | Onboarding score bootstrapping ("cold start"). A new student has no history; how are initial mastery/retention seeded (diagnostic test? zeroes?). | The whole graph starts empty; first plans need *some* signal. | Add an optional diagnostic assessment at onboarding (D16). |
| **G13** | Concurrency/locking strategy for `student_concept_progress`. | **Resolved in v1.1:** `LEARNING_GRAPH_SPECIFICATION.md` §4 (row_version) + `DOMAIN_EVENTS_SPECIFICATION.md` §4–§5 (idempotency, partition ordering). | Implement in S4. |
| **G14** | Acceptance thresholds for AI eval (max hallucination rate, min plan accuracy, min answer-eval agreement with humans). Eval is mandated; targets aren't. | Without thresholds, "eval" is decorative. | Set initial thresholds (D5). |

---

## 8. Unclear Decisions (specified, but ambiguously)

| ID | Unclear point | Source | Question to resolve |
|---|---|---|---|
| **U1** | ~~Scoring formula weights/normalization.~~ | **Resolved:** canonical scoring + engine specs (§1.6, §1.10). | Close D2 as implemented in specs. |
| **U2** | "Runs nightly" / "runs daily/weekly/monthly" for Retention & Mentor engines — at what time, in what timezone, and is it per-tenant or global? | Part 6 §18/§19 | Define schedule + TZ (links G11). |
| **U3** | Mentor is described both as a deterministic "engine" (Part 6 §19) and as an LLM "agent" (Part 5 §5). Which part is deterministic vs LLM-driven? | Part 6 §19 vs Part 5 §5 | Confirm split: deterministic plan assembly + LLM phrasing/explanation (recommended). |
| **U3b** | Same dual framing for Revision ("engine" in Part 6 §18, "agent" in Part 5 §6). | Part 6 §18 vs Part 5 §6 | Confirm Revision is fully deterministic; the "agent" only narrates. |
| **U4** | "Human override becomes training signal" — stored for later fine-tuning? For prompt-improvement? For a future model? No mechanism specified. | Part 5 §19 | Define what "training signal" operationally means in V1 (probably: stored + analyzed, no fine-tuning yet). |
| **U5** | WebSocket auth, scaling, and fallback (does it run on Fargate with sticky sessions? what if WS drops?). | Part 6 §23 | Define WS infra + auth (token over query/cookie) + reconnect. |
| **U6** | "Shared schema now, isolated DB for enterprise later" — what's the trigger and migration path to per-tenant DB? | Part 3 §5 | Define the threshold + extraction plan (architecture, low founder input). |
| **U7** | MCP integration (Part 5 §27) — is exposing Knowledge/PYQ/CA/Institute as MCP servers in scope for V1 at all, or strictly future? | Part 5 §27 | Confirm V1 exclusion (recommended: future-only). |
| **U8** | "Importance" lives at concept level *and* is duplicated into `student_concept_progress.importance_score`. Is per-student importance ever different from global, or is this denormalization? | Part 2 §11 vs §10 | Clarify: global importance vs per-student weighting (affects schema). |

---

## 9. Risk Register

Scored as Likelihood (L) × Impact (I), each High/Med/Low. Ordered by severity.

| ID | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| **R1** | **Scoring formulas are underspecified** (U1/G4). Wrong formulas silently produce bad plans/recommendations — the core product value. | High | High | Convert every formula to a precise, weighted, bounded, **versioned** function with founder sign-off (D2/D3); 100% unit tests; backtest against sample data before exposing. | Architect + Founder |
| **R2** | **AI evaluation reliability** for Mains/RAG. LLM scoring of UPSC answers may be inconsistent or hallucinate; students lose trust fast. | High | High | Eval harness *before* exposure (S8/S16/S18); hard thresholds (D5); human-in-the-loop override; defer Mains to P8 after data exists. | AI lead |
| **R3** | **AI cost blow-up.** AI spend at 10k users projected $5k–15k/mo; uncontrolled prompts/agents could exceed revenue. | Med | High | Model tiering (Part 5 §23/Part 8 §24); per-user/feature/agent cost tracking from S8; caching of plans/analytics in Redis; budget alerts. | AI lead + DevOps |
| **R4** | **Tenant data leakage.** Shared-schema multi-tenancy: one missing `tenant_id` filter exposes another institute's students. | Med | High | Repository-level enforced tenant scoping (S1); mandatory negative cross-tenant tests in DoD; periodic query audits; consider Postgres RLS as defense-in-depth. | Backend lead |
| **R5** | **Critical-path concentration.** Learning Graph is a single point that everything depends on (§3.3). Delay or defect cascades. | Med | High | Build it early (S4) with the highest test bar; freeze its interface; protect the path in planning. | Eng lead |
| **R6** | **Content/data licensing** (G8/G12). PYQ and standard-book content may be copyrighted; the moat depends on lawful data. | Med | High | Legal review of every source; prefer owned/licensed content; design ingestion to track source + license per chunk. | Founder/Legal |
| **R7** | **Embedding model lock-in** (C5). Hard-coded `vector(3072)` ties us to one model; re-embedding 100k docs later is costly. | Med | Med | Make dim/model config (D7); store model+dim per chunk; plan a re-embedding job pattern. | AI lead |
| **R8** | **Concurrency on `student_concept_progress`** (G13). Simultaneous MCQ/revision/study events race and corrupt scores. | Med | High | Idempotent event-driven updates; row versioning/optimistic locking; serialize per-(student,concept). | Backend lead |
| **R9** | **Compliance (DPDP Act 2023)** (G9). Handling student PII/behavior without consent/retention/deletion controls is a legal risk in India. | Med | High | DPDP baseline in P9 (consent, deletion, retention, audit) (D13); privacy-by-design in schema now. | Founder/Legal |
| **R10** | **Cold-start quality** (G12). New students get poor first plans (no data), hurting activation/retention. | High | Med | Optional diagnostic assessment at onboarding (D16); conservative default plans; communicate "warming up." | Product + AI |
| **R11** | **Roadmap/scope ambiguity** (C1/C6) causes mis-sequenced work and rework. | Med | Med | Lock the merged roadmap (D1); feature-flag everything; no sprint depends on a future sprint. | Eng lead |
| **R12** | **Frontend/backend contract drift.** Parallel work (Recharts graph, dashboard) outpaces/contradicts evolving APIs. | Med | Med | API contracts published one sprint ahead; contract tests; FE trails BE by ≤1 sprint. | FE + BE leads |
| **R13** | **WebSocket scaling on Fargate** (U5). Stateful WS conflicts with horizontally-scaled stateless tasks. | Low | Med | Define WS strategy (sticky sessions or Redis-backed pub/sub for fan-out) in S12; graceful HTTP fallback. | Backend + DevOps |
| **R14** | **Single-region availability** (V1 is single-region). Region outage = full downtime. | Low | Med | Accept for V1 (Multi-AZ only); DR drills (S21); multi-region is an explicit Phase-3 scaling item. | DevOps |
| **R15** | **Prompt injection / jailbreaks** via student-supplied answer text or chat. | Med | Med | System-prompt hardening, guardrails, output validation, tenant boundaries (Part 8 §29); injection tests in DoD for AI features. | AI lead |
| **R16** | **Team/velocity unknown** (G5). Sprint dates are estimates; over-commitment risk. | Med | Med | Calibrate after S0–S1 actuals; reforecast; the plan is sprint-ordered, not date-locked. | Eng lead |

---

## 10. Open Decisions Log (single list for the Founder)

These are the items blocking *unambiguous* execution. Recommended defaults are in §§6–9; nothing here stops S0–S1 from starting.

| ID | Decision needed | Blocks | Recommended default |
|---|---|---|---|
| **D1** | Confirm the merged roadmap & V1 assessment scope (MCQ in V1, Mains in V2/V3). | Phase ordering (esp. P4/P8) | Accept §2 merged plan. |
| **D2** | Sign off precise, weighted, bounded formulas for Importance, Retention, Confidence, Revision Priority. | S4, S5, S7 | Architect drafts; founder approves before S4 ships scores. |
| **D3** | Define Readiness Score composite + subscore weights. | S11 dashboard | Weighted avg of knowledge/revision/MCQ/writing/CA. |
| **D4** | Canonical pricing + payment provider (Razorpay vs Stripe) + GST handling. | S14 billing | Razorpay (India-first) + fix pricing per one source. |
| **D5** | AI eval acceptance thresholds (max hallucination, min plan accuracy, min human-agreement for Mains). | S8/S16/S18 gates | Set conservative initial bars; tighten over time. |
| **D6** | LLM provider strategy: OpenAI-only vs OpenAI+Anthropic; commit to a provider-agnostic gateway. | S8 onward | Provider-agnostic gateway; start OpenAI; Claude for long-context Mains. |
| **D7** | Embedding model + vector dimension as config (not hard-coded). | S15 | `text-embedding-3-large`(3072) default, stored per chunk. |
| **D8** | Intended use of `frequently_asked_with` concept relationship. | PYQ engine (S7) | Future PYQ co-occurrence input; keep schema, defer logic. |
| **D9** | Define the S3 path scope replacing undefined `project_id`. | Any upload (S15/S18) | `tenant_id/<resource_type>/<owner_id>/file`. |
| **D10** | Team composition & velocity. | Sprint dates | Provide actual staffing; recalibrate after S1. |
| **D11** | Prediction Engine approach & whether it's V1. | (post-V1) | Defer; heuristic + CI later. |
| **D12** | Content acquisition & licensing plan (PYQs, books, gov sources). | RAG/PYQ data | Legal review; prefer owned/licensed. |
| **D13** | DPDP Act 2023 compliance baseline (consent/retention/deletion). | P9 | Add baseline in P9; privacy-by-design now. |
| **D14** | Notification providers (email/push) + template mapping. | Notifications (S12+) | SES + FCM. |
| **D15** | Timezone policy for nightly jobs & study times. | S5 retention job | Per-user TZ, store UTC. |
| **D16** | Onboarding diagnostic to solve cold start. | S3/S10 quality | Optional diagnostic MCQ at onboarding. |

---

## Appendix A — Source document inventory

| File | Titled | Footer says | Notes |
|---|---|---|---|
| `docs/01-product-requirements.md` | Part 1 — PRD | END OF PART 1 | Vision, personas, 8 engines, V1/V2/V3, revenue. |
| `docs/02-domain-model.md` | Part 2 — Domain/DB/Learning Graph/Twin | (none) | IP: scoring formulas, twin, moats. |
| `docs/03-system-architecture.md` | Part 3 — Technical Architecture | **END OF PART 2** (mismatch) | Stack, modules, layers, rulebook. |
| `docs/05-agent-architecture.md` | Part 5 — AI & Agent System | (none) | Supervisor + agents, memory, eval, RAG, MCP. |
| `docs/06-api-spec.md` | Part 6 — Backend/Services/APIs/Events | End of Part 6 | Services, tables, events, API list, roadmap §28. |
| `docs/07-ui-ux.md` | Part 7 — Frontend/UX | (none) | Screens, design system, FE rulebook. |
| `docs/08-future-devops.md` | Part 8 — AWS/DevOps/Security/Scale | (none) | Infra evolution, cost, CTO roadmap §35. |
| `docs/04-*` | **MISSING** | — | Part 4 not present in repo (Gap G7). |

### Canonical implementation specifications (v1.1)

| File | Bounded context |
|---|---|
| `EXAM_DOMAIN_SPECIFICATION.md` | UPSC taxonomy, PYQ/CA mapping models |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Readiness, display scores, gating |
| `LEARNING_GRAPH_SPECIFICATION.md` | Student graph state |
| `REVISION_ENGINE_SPECIFICATION.md` | Revision queue (v1.1) |
| `PREPARATION_TWIN_SPECIFICATION.md` | Twin projection |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | PYQ + Importance |
| `MENTOR_AGENT_SPECIFICATION.md` | Mentor orchestration |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | MCQ / mocks / recall |
| `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` | CA catalog + linking |
| `DOMAIN_EVENTS_SPECIFICATION.md` | Cross-engine events + outbox |

## Appendix B — Glossary (for newcomers)

- **Preparation Twin** — a per-student data model (profiles for knowledge, behavior, assessment, prediction) derived from the Learning Graph + history. The "intelligence layer."
- **Learning Graph** — per-student scores (mastery/retention/confidence/importance) attached to each syllabus concept. The "source of truth" for knowledge state.
- **Importance** — how exam-relevant a concept is (driven by PYQ data).
- **Retention** — how much a student still remembers, decaying over time (Ebbinghaus).
- **Clean Architecture** — dependencies point inward; domain logic has no I/O dependencies; infrastructure is swappable.
- **Modular Monolith** — one deployable app split into independent modules that *could* later become services.
- **Repository pattern** — data-access objects that hide the database and return domain objects, not ORM rows.
- **Service layer** — where business logic lives (not in routes, not in repositories).
- **RAG** — Retrieval-Augmented Generation: fetch relevant chunks, then have the LLM answer grounded in them.
- **Supervisor agent** — routes a user request to the right specialist agent; doesn't answer itself.

---

*End of Master Implementation Plan v1.0. No code is included by design. Update this document whenever an Open Decision (§10) is resolved; treat §§6–10 as the living backlog of clarifications.*
