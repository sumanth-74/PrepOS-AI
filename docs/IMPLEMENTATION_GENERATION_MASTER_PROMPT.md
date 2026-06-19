# PrepOS AI — Implementation Generation Master Prompt

Version: 1.0  
Status: **Constitution for all code generation**  
Role: Principal Architect · Lead Engineer  
Audience: AI code generators, backend engineers, reviewers  

> **Purpose.** This document is the **non-negotiable implementation contract** for PrepOS AI. Every module, migration, test, and agent tool generated in this repository MUST conform to it. When a generator is unsure, it MUST read the bounded-context specification first, then this document, then implement.
>
> **Do not generate code that violates this contract.** If a spec is ambiguous, stop and flag the gap — do not invent behavior.

---

## 0. How to use this document

### 0.1 Relationship to specifications

| Layer | Documents | Role |
|---|---|---|
| **Constitution** | This file | Architecture, layering, patterns, quality gates |
| **Bounded-context specs** | `*_SPECIFICATION.md` | Business rules, formulas, events, ownership |
| **Blueprint parts** | `01`–`08` (except missing Part 4) | Vision, UX, indicative APIs — **subordinate to specs** |
| **Execution plan** | `MASTER_IMPLEMENTATION_PLAN.md` | Sprint sequencing — **subordinate to specs on conflicts** |

### 0.2 Specification priority order (conflict resolution)

When documents disagree, apply this order **top wins**:

| Priority | Document | Wins for |
|:---:|---|---|
| 1 | `LEARNING_GRAPH_SPECIFICATION.md` | Graph storage, single-writer, concurrency, rollups, cache keys |
| 2 | `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Readiness (R3), display scores, prediction gating, Engine vs Display |
| 3 | `SCORING_ENGINE_SPECIFICATION.md` | Core deterministic score math (Mastery, Retention, Weakness, Health, Predictions) |
| 4 | `REVISION_ENGINE_SPECIFICATION.md` | Revision queue, **Revision Priority additive formula**, sessions, CA relevance |
| 5 | `PREPARATION_TWIN_SPECIFICATION.md` | Twin profiles, projection pipelines, debounced rebuild |
| 6 | `PYQ_INTELLIGENCE_SPECIFICATION.md` | PYQ catalog, **Importance computation ownership**, `PYQDataChanged` |
| 7 | `ASSESSMENT_ENGINE_SPECIFICATION.md` | MCQ/mocks/recall, attempt lifecycle, confidence inputs |
| 8 | `MENTOR_AGENT_SPECIFICATION.md` | Plans, tools, deterministic assembly, LLM boundaries |
| 9 | `DOMAIN_EVENTS_SPECIFICATION.md` | Envelope, outbox, idempotency, ordering, Celery routing |
| 10 | `EXAM_DOMAIN_SPECIFICATION.md` | Taxonomy, concept IDs, relationships, catalog versioning |
| 11 | `MASTER_IMPLEMENTATION_PLAN.md` | Sprint order, team process |

### 0.3 Codified cross-spec resolutions

These conflicts are **already decided** by the priority stack above. Generators MUST NOT re-litigate them:

| Topic | Implement from | Not from |
|---|---|---|
| **Readiness formula** | Scoring v1.1 §4 (`MasteryNonMCQ`-based `KnowledgeSub`) | Scoring v1.0 §7 |
| **Revision Priority (scheduling)** | Revision spec §5.1 (`revision_priority_v1_1`, weighted additive) | Scoring v1.0 §10.4 multiplicative form |
| **Importance global write** | PYQ Intelligence (`ImportanceEngine` → `concepts.importance`) | Direct Learning Graph writes to global importance |
| **Importance student copy** | Learning Graph (`RefreshImportanceForExam` on `PYQDataChanged`) | PYQ writing `student_concept_progress` |
| **Weakness persistence** | Compute on demand; optional stale analytics cache only (v1.1 R1) | Authoritative `weakness_score` column |
| **Confidence formula inputs** | Assessment §16 + Learning Graph §8.4 (until Scoring v1.0 adds dedicated section) | Invented weights |
| **S3 object paths** | `tenant_id/{resource_type}/{owner_id}/...` | Undefined `project_id` (Master Plan D9) |
| **Time math** | UTC storage; `Asia/Kolkata` default display; nightly jobs 18:30 UTC (Scoring v1.0 §1.2) | Per-worker local timezone in formulas |

### 0.4 Architecture laws (immutable)

From blueprint Part 3 §26 and Master Plan §1.3 — **every PR must satisfy all**:

1. **No business logic in API routes.**
2. **Repositories never return ORM models to the API layer.**
3. **Agents never touch the database directly** — tools → services → repositories only.
4. **Every AI/scoring decision must be explainable** — persist reasoning, not just outputs.
5. **Learning Graph is the source of truth** for student knowledge state.
6. **Preparation Twin is the intelligence layer** derived from graph + history.
7. **AI assists decisions; AI never becomes the source of truth.**
8. **Everything is tenant-aware** — every table and query scoped by `tenant_id`.
9. **Every feature is observable** — `request_id`, `tenant_id`, `user_id` on every request; cost/latency on every AI call.

---

## 1. System architecture

### 1.1 Style

| Decision | Choice | Rationale |
|---|---|---|
| Application shape | **Modular monolith** | V1 scale (≈10k students); faster iteration; extractable modules later |
| Architecture pattern | **Clean Architecture** | Testable domain; swappable infrastructure |
| Integration style | **Event-driven** between bounded contexts | Loose coupling; replay; idempotency |
| AI placement | **Sidecar layer** (`ai/`) calling application services via tools | Rule #3; never source of truth |

### 1.2 Technology stack (mandatory)

| Concern | Technology | Version / notes |
|---|---|---|
| Language | Python | **3.13+** |
| HTTP API | **FastAPI** | Async-capable; OpenAPI-first |
| Validation / settings | **Pydantic v2** | All I/O models |
| ORM | **SQLAlchemy 2.0** | Typed models; `Mapped[]` annotations |
| Migrations | **Alembic** | Reversible; one migration per logical change |
| Primary database | **PostgreSQL 17** | Single source of truth |
| Vector search | **pgvector** | `vector(dim)` — dim from config, default 3072 |
| Cache / broker | **Redis** | Cache, Celery broker, rate limits, optional pub/sub |
| Background jobs | **Celery** + Celery Beat | Queue routing per `DOMAIN_EVENTS_SPECIFICATION.md` §19 |
| Object storage | **AWS S3** | Documents, uploads, answer sheets |
| AI orchestration | **LangGraph** | Agent graphs; shared state |
| LLM provider (V1 default) | **OpenAI SDK** | Behind provider-agnostic gateway interface |
| Observability | **OpenTelemetry**, **Sentry**, structured logging | From day one (S0) |
| CI | **GitHub Actions** | lint → test → build |
| Local dev | **Docker Compose** | api, worker, beat, postgres, redis, frontend placeholder |

### 1.3 Runtime topology (V1)

```
                    ┌──────────────┐
                    │   Next.js    │  (frontend — separate repo/path)
                    └──────┬───────┘
                           │ HTTPS
                    ┌──────▼───────┐
                    │   FastAPI    │  api/ — authN, authZ, serialize
                    └──────┬───────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────▼──────┐   ┌──────▼──────┐   ┌──────▼──────┐
  │ Application │   │  ai/ agents │   │   events/   │
  │  use-cases  │   │   + tools   │   │  handlers   │
  └──────┬──────┘   └──────┬──────┘   └──────┬──────┘
         │                 │                 │
         └─────────────────┼─────────────────┘
                           │
                    ┌──────▼───────┐
                    │    domain/   │  pure rules, scoring fns, entities
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │infrastructure│  repos, DB, Redis, S3, OpenAI client
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
         PostgreSQL      Redis          S3
```

**Celery workers** run the same codebase; they invoke application services and event handlers — never bypass layers.

### 1.4 Bounded contexts (modules)

Each module owns models (in infrastructure), domain rules, services, repositories, APIs, and events:

| Module | V1 | Primary spec |
|---|---|---|
| `auth` | ✓ | Master Plan S1; Part 3 |
| `tenant` | ✓ | Master Plan S1 |
| `student` | ✓ | Master Plan S3 |
| `exam` | ✓ | `EXAM_DOMAIN_SPECIFICATION.md` |
| `syllabus` | ✓ | `EXAM_DOMAIN_SPECIFICATION.md` (catalog) |
| `learning_graph` | ✓ | `LEARNING_GRAPH_SPECIFICATION.md` |
| `revision` | ✓ | `REVISION_ENGINE_SPECIFICATION.md` |
| `preparation_twin` | ✓ | `PREPARATION_TWIN_SPECIFICATION.md` |
| `pyq` | ✓ | `PYQ_INTELLIGENCE_SPECIFICATION.md` |
| `assessment` | ✓ | `ASSESSMENT_ENGINE_SPECIFICATION.md` |
| `mentor` | ✓ | `MENTOR_AGENT_SPECIFICATION.md` |
| `analytics` | ✓ | Aggregation over graph + assessment |
| `current_affairs` | V2 | `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` |
| `knowledge` | V2 | Master Plan S15–S16 |
| `notifications` | minimal | Master Plan |
| `billing` | V1.5 | Master Plan S14 |
| `ai` | cross-cutting | `MENTOR_AGENT_SPECIFICATION.md`, Part 5 |

Shared **`domain/scoring/`** holds pure scoring functions consumed by Learning Graph, Revision, Twin, and PYQ — not a separate deployable service.

---

## 2. Folder structure rules

### 2.1 Repository layout

```
PrepOS/
├── backend/
│   ├── alembic/                    # migrations (Alembic)
│   │   └── versions/
│   ├── src/
│   │   ├── api/                    # FastAPI routers, deps, middleware
│   │   │   └── v1/
│   │   │       ├── auth/
│   │   │       ├── students/
│   │   │       ├── learning_graph/
│   │   │       ├── revision/
│   │   │       ├── assessment/
│   │   │       ├── mentor/
│   │   │       ├── pyq/
│   │   │       ├── analytics/
│   │   │       └── health.py
│   │   ├── application/            # use cases, orchestration, DTOs
│   │   │   └── {module}/
│   │   │       ├── use_cases/
│   │   │       ├── services/
│   │   │       ├── dto/
│   │   │       └── ports/          # abstract repository interfaces (optional)
│   │   ├── domain/                 # entities, value objects, pure logic
│   │   │   ├── scoring/            # SHARED pure functions (all score fns)
│   │   │   └── {module}/
│   │   │       ├── entities/
│   │   │       ├── value_objects/
│   │   │       ├── events/
│   │   │       ├── policies/
│   │   │       └── exceptions/
│   │   ├── infrastructure/         # I/O implementations
│   │   │   ├── db/
│   │   │   │   ├── models/         # SQLAlchemy ORM — NEVER exported upward
│   │   │   │   ├── repositories/
│   │   │   │   └── session.py
│   │   │   ├── cache/
│   │   │   ├── messaging/          # outbox publisher, Redis
│   │   │   ├── storage/            # S3
│   │   │   └── llm/                # OpenAI gateway
│   │   ├── ai/
│   │   │   ├── agents/
│   │   │   ├── tools/
│   │   │   ├── graphs/             # LangGraph
│   │   │   ├── prompts/
│   │   │   └── evaluation/
│   │   ├── events/
│   │   │   ├── envelope.py
│   │   │   ├── outbox/
│   │   │   └── handlers/           # per-consumer idempotent handlers
│   │   ├── tasks/                  # Celery app + task modules
│   │   └── core/
│   │       ├── config.py           # Pydantic Settings
│   │       ├── tenancy.py          # TenantContext
│   │       ├── logging.py
│   │       ├── errors.py
│   │       └── observability.py
│   └── tests/
│       ├── unit/
│       ├── integration/
│       ├── e2e/
│       └── contract/
├── seeds/                          # JSON catalog seeds (EXAM_DOMAIN, PYQ, CA)
├── docs/                           # specifications (source of truth)
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

### 2.2 Naming conventions

| Artifact | Convention | Example |
|---|---|---|
| Python packages / modules | `snake_case` | `learning_graph_service.py` |
| Classes | `PascalCase` | `LearningGraphService` |
| Domain entities | `PascalCase` noun | `ConceptProgressNode` |
| Use cases | verb phrase class | `ApplyGraphEventUseCase` |
| Repositories | `{Entity}Repository` | `ConceptProgressRepository` |
| ORM models | suffix `Model` or table name | `StudentConceptProgressModel` |
| API routes | plural REST nouns | `/api/v1/students/{id}/graph` |
| Event types | `PascalCase` past tense | `AssessmentCompleted` |
| Config keys | `SCREAMING_SNAKE` | `MASTERY_W_MCQ` |
| Redis keys | colon-separated lowercase | `lg:node:{tenant}:{student}:{concept}` |
| Scoring versions | `{score}_v{n}` | `mastery_v1`, `readiness_v1_1` |

### 2.3 File placement rules

| Code type | Location | Forbidden elsewhere |
|---|---|---|
| FastAPI route | `api/v1/{module}/` | Business logic in route |
| Use case / orchestration | `application/{module}/use_cases/` | Direct SQL in use case |
| Pure business rule | `domain/{module}/` or `domain/scoring/` | FastAPI, SQLAlchemy imports |
| SQLAlchemy model | `infrastructure/db/models/` | `api/`, `domain/` |
| Repository impl | `infrastructure/db/repositories/` | Returning ORM to `api/` |
| Celery task | `tasks/` | Business logic without calling application service |
| Event handler | `events/handlers/` | Direct cross-module table writes |
| LangGraph / agent | `ai/` | Direct DB access |
| Tool definition | `ai/tools/` | Must call application service only |

### 2.4 One module, one ownership

- Each bounded context has **one application service** as the public entry point for synchronous operations.
- Cross-context calls use **domain/integration events** or **read ports** — never import another module's repository.

---

## 3. Layering rules

### 3.1 Layer responsibilities

```
┌─────────────────────────────────────────────────────────────┐
│  API (api/)                                                  │
│  • HTTP routing, OpenAPI                                     │
│  • AuthN / AuthZ dependency injection                        │
│  • Request/response Pydantic models                          │
│  • Map exceptions → HTTP status                              │
│  • NO business rules, NO SQL, NO scoring formulas            │
└───────────────────────────────┬─────────────────────────────┘
                                │ DTOs in / out
┌───────────────────────────────▼─────────────────────────────┐
│  APPLICATION (application/)                                  │
│  • Use cases (one per user/system action)                    │
│  • Transaction boundaries                                    │
│  • Orchestration across repositories + domain services       │
│  • Emit outbox events in same transaction as state change    │
│  • NO FastAPI imports, NO raw SQL                            │
└───────────────────────────────┬─────────────────────────────┘
                                │ domain objects, value types
┌───────────────────────────────▼─────────────────────────────┐
│  DOMAIN (domain/)                                            │
│  • Entities, value objects, domain events (types)            │
│  • Pure scoring functions (domain/scoring/)                  │
│  • Invariants and policies                                   │
│  • NO I/O: no DB, Redis, HTTP, OpenAI, Celery               │
└───────────────────────────────┬─────────────────────────────┘
                                │ interfaces (ports)
┌───────────────────────────────▼─────────────────────────────┐
│  INFRASTRUCTURE (infrastructure/)                            │
│  • SQLAlchemy models + repository implementations            │
│  • Redis, S3, OpenAI client                                    │
│  • Maps ORM ↔ domain entities                                 │
└─────────────────────────────────────────────────────────────┘

        AI (ai/) sits beside APPLICATION:
        tools → application services ONLY
```

### 3.2 Request flow (canonical)

```
HTTP Request
  → api/router (validate auth, parse DTO)
  → application/use_case.execute(dto)
  → domain policies + pure functions
  → infrastructure/repository (tenant-scoped)
  → PostgreSQL (+ outbox insert in same transaction)
  → (async) Celery dispatches event to consumers
  → api/router (serialize response DTO)
```

### 3.3 Scoring code placement

| Concern | Location |
|---|---|
| Formula implementation | `domain/scoring/{score}.py` — **pure functions** |
| Config constants | `domain/scoring/config.py` → `ScoringConfig` versioned |
| Invocation / persistence | `LearningGraphService` (or PYQ for global Importance) |
| Display projection | Application read models + API mappers (v1.1 rules) |

Scoring functions MUST accept explicit inputs + `now: datetime` — no hidden wall-clock reads inside the function body.

---

## 4. Dependency rules

### 4.1 Allowed imports (summary matrix)

| From ↓ / To → | api | application | domain | infrastructure | ai | events | tasks |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **api** | ✓ | ✓ | ✗* | ✗ | ✗ | ✗ | ✗ |
| **application** | ✗ | ✓ | ✓ | ✓** | ✗ | ✓ | ✗ |
| **domain** | ✗ | ✗ | ✓ | ✗ | ✗ | ✗ | ✗ |
| **infrastructure** | ✗ | ✗ | ✓ | ✓ | ✗ | ✗ | ✗ |
| **ai** | ✗ | ✓ | ✓*** | ✗ | ✓ | ✗ | ✗ |
| **events/handlers** | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✗ |
| **tasks** | ✗ | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ |

\* API may import domain **exception types only** for mapping to HTTP errors — not entities for logic.  
\** Application imports infrastructure via **constructor injection** / FastAPI `Depends` wiring in `api/deps.py` — not global singletons.  
\*** AI may import domain **types** for tool schemas — not services that touch I/O.

### 4.2 Forbidden imports (hard fail in review)

```python
# FORBIDDEN — domain layer
from sqlalchemy import ...
from fastapi import ...
import openai
import redis

# FORBIDDEN — api layer
from infrastructure.db.repositories import ...
from infrastructure.db.models import ...

# FORBIDDEN — ai layer
from infrastructure.db.session import get_session
from infrastructure.db.repositories import ConceptProgressRepository

# FORBIDDEN — cross-context coupling
from application.revision.services import RevisionEngineService  # inside learning_graph module
# Use events or shared read port interface instead

# FORBIDDEN — ORM leakage
def get_student(...) -> StudentModel:  # returning ORM to api/application
```

### 4.3 Cross-module communication

| Need | Allowed mechanism |
|---|---|
| Assessment → update mastery | Emit `AssessmentCompleted` → Learning Graph handler |
| PYQ → update importance copy | Emit `PYQDataChanged` → LG `RefreshImportanceForExam` |
| Graph → Twin | Emit `LearningGraphUpdated` → Twin debounced rebuild |
| Revision → retention | Emit `RevisionCompleted` → LG handler |
| Mentor → read scores | Tool → `GetLearningGraphTool` → application service |
| Sync read within request | Application **read port** interface — read-only, no writes |

**Never:** Module A's repository writing Module B's authoritative table.

---

## 5. Repository pattern rules

### 5.1 Contract

1. **Repository interface** lives in `application/{module}/ports/` or `domain/{module}/repositories/` (abstract base).
2. **Implementation** lives in `infrastructure/db/repositories/`.
3. Methods accept **`tenant_id` explicitly** or via injected `TenantContext` — never optional tenant.
4. Return type is **`domain` entity**, **`dataclass`**, or **application DTO** — never SQLAlchemy `Model`.
5. Repository performs **persistence only** — no business rules, no scoring formulas.

### 5.2 Mapping

```python
# infrastructure layer ONLY
def _to_domain(row: StudentConceptProgressModel) -> ConceptProgressNode:
    ...

def _to_model(entity: ConceptProgressNode) -> StudentConceptProgressModel:
    ...
```

### 5.3 Tenant enforcement in every query

```python
# REQUIRED pattern
stmt = select(StudentConceptProgressModel).where(
    StudentConceptProgressModel.tenant_id == tenant_id,
    StudentConceptProgressModel.student_id == student_id,
)
```

Base repository class MUST provide `scoped_query(model, tenant_id)` — subclasses cannot bypass.

### 5.4 Optimistic locking (Learning Graph mandatory)

For `student_concept_progress`:

```python
UPDATE ... SET ..., row_version = row_version + 1
WHERE tenant_id = ? AND student_id = ? AND concept_id = ?
  AND row_version = :expected_version
```

On zero rows updated → raise `OptimisticLockError` → retry policy (LG spec §19.1: max 3 with jitter).

### 5.5 Repository anti-patterns (reject in PR)

- Generic `get_all()` without tenant filter
- `session.query()` legacy SQLAlchemy 1.x style
- Business logic in repository (`if mastery > 70: tier = "expert"`)
- Repository calling another module's repository directly
- Exposing `Session` to application layer

---

## 6. Event-driven architecture rules

### 6.1 Mandatory patterns (DOMAIN_EVENTS spec)

| Rule | Requirement |
|---|---|
| Cross-context writes | **Outbox table** in same DB transaction as state change |
| Delivery | Celery worker reads outbox → dispatches to handlers |
| Idempotency | Every handler checks `processed_events` by `(consumer, event_id)` |
| Envelope | Global fields per §2.1: `event_id`, `event_version`, `event_type`, `occurred_at`, `recorded_at`, `tenant_id`, `correlation_id`, `causation_id`, `producer`, `payload` |
| Naming | `PascalCase` past tense — `AssessmentCompleted`, not `assessment.completed` |
| At-least-once | Handlers MUST be idempotent — duplicates ack silently |

### 6.2 Producer obligation

```python
# REQUIRED transaction pattern in application use case
async with unit_of_work() as uow:
    uow.revisions.complete(revision)
    uow.outbox.publish(
        event_type="RevisionCompleted",
        payload=...,
        tenant_id=tenant_id,
        correlation_id=request_id,
    )
    await uow.commit()
# Celery picks up outbox AFTER commit
```

**Forbidden:** `redis.publish()` or Celery `delay()` as sole durability mechanism for cross-context facts.

### 6.3 Ordering guarantees

| Partition key | Strict serial required |
|---|---|
| `{tenant_id}:{student_id}:{concept_id}` | Learning Graph mutations |
| `{tenant_id}:{student_id}:{revision_id}` | Revision completion |
| `{tenant_id}:{student_id}:{attempt_id}` | Assessment scoring |

Handlers for the same partition MUST NOT run concurrently without row-level coordination.

### 6.4 Consumer registry (implement handlers, do not invent events)

Critical V1 events — full catalog in `DOMAIN_EVENTS_SPECIFICATION.md` Appendix A:

| Event | Producer | Consumers |
|---|---|---|
| `AssessmentCompleted` | Assessment | Learning Graph, Twin, Mentor cache, Analytics |
| `RevisionCompleted` | Revision | Learning Graph, Twin |
| `LearningGraphUpdated` | Learning Graph | Twin, Mentor cache, Dashboard |
| `PYQDataChanged` | PYQ | Learning Graph, Twin, Mentor, Assessment pools |
| `TwinUpdated` | Twin | Mentor cache, WebSocket bridge |
| `MentorPlanGenerated` | Mentor | Analytics, notifications |
| `StudySessionLogged` | Student/Study | Learning Graph |
| `DomainCatalogUpdated` | Exam/Syllabus | Learning Graph backfill, cache invalidation |

### 6.5 Celery queue routing

Per `DOMAIN_EVENTS_SPECIFICATION.md` §19 — route by domain:

| Queue | Workloads |
|---|---|
| `default` | General |
| `learning_graph` | Graph updates, retention materialize |
| `revision` | Nightly revision plans |
| `twin` | Twin rebuild projections |
| `pyq` | Importance batch recompute |
| `ingestion` | V2 content pipelines |

### 6.6 Failure handling

| Failure | Action |
|---|---|
| Transient DB | Celery retry exponential backoff |
| Domain/scoring error | Dead-letter queue; **no partial score write** |
| Duplicate `event_id` | Ack silently |
| Corrupt payload | Quarantine; alert; no mutation |
| Optimistic lock conflict | Reload + idempotent retry (max 3) |

---

## 7. Learning Graph single-writer rule

### 7.1 The rule

> **Only `LearningGraphService` (Learning Graph bounded context) may INSERT/UPDATE score columns on `student_concept_progress`.**

No other module — including Assessment, Revision, PYQ, Twin, Mentor, or API routes — may write:

- `mastery_score`, `mastery_nonmcq_score`
- `retention_score`, `retention_stability_s`, retention state columns
- `confidence_score`, `importance_score` (student copy)
- `overconfidence_flag`, evidence counters (`n_mcq`, etc.)

### 7.2 How other modules influence the graph

| Module | Mechanism |
|---|---|
| Assessment | Emit `AssessmentCompleted` with evidence payload |
| Revision | Emit `RevisionCompleted` with recall grade |
| Study | Emit `StudySessionLogged` |
| PYQ | Emit `PYQDataChanged` → LG runs `RefreshImportanceForExam` |
| Nightly jobs | Emit `RetentionMaterializeRequested` → LG materializes decay |

### 7.3 Event application pipeline (mandatory)

Per `LEARNING_GRAPH_SPECIFICATION.md` §7.2:

1. Validate envelope + tenant + idempotency
2. Append `learning_graph_events`
3. Load node with `row_version`
4. Call `domain/scoring/` pure functions
5. Persist node + `score_audit_log` in **one transaction**
6. Publish `LearningGraphUpdated`

### 7.4 Scoring invocation

```python
# CORRECT — inside LearningGraphService
new_mastery, version, audit = compute_mastery(inputs, now, config)

# WRONG — inside AssessmentService
node.mastery_score = calculate_mastery(...)
repository.save(node)
```

### 7.5 Read access

All modules may **read** graph data via:
- Repository read methods (same bounded context)
- Application **read port** services exposed to tools/APIs
- Materialized rollups / Redis cache (stale-while-revalidate)

---

## 8. Multi-tenant enforcement rules

### 8.1 Data model

- Every tenant-scoped table includes **`tenant_id UUID NOT NULL`** (except platform-global catalog rows with explicit `tenant_id IS NULL` + `scope=platform` flag).
- FK chains must not allow cross-tenant references.
- Platform-global: `concepts`, `pyq_questions` (when `tenant_id IS NULL`), domain catalog — consumers MUST NOT apply to wrong tenant.

### 8.2 TenantContext

```python
# core/tenancy.py — set by middleware after JWT validation
class TenantContext:
    tenant_id: UUID
    user_id: UUID
    roles: frozenset[Role]
```

Middleware MUST reject requests where JWT `tenant_id` ≠ resource `tenant_id`.

### 8.3 RBAC roles (V1)

`student`, `faculty`, `institute_admin`, `super_admin`

Authorization checks live in **application layer** or dedicated `domain/auth/policies/` — not scattered in repositories.

### 8.4 Required tests (every module)

```python
async def test_cross_tenant_access_denied():
    """Tenant A token cannot read Tenant B student graph."""
```

Negative cross-tenant test is **Definition of Done** — non-optional.

### 8.5 Defense in depth (recommended P9)

- PostgreSQL Row Level Security policies on `student_*` tables
- Periodic audit script grepping repositories for queries missing `tenant_id`

---

## 9. Caching rules

### 9.1 Principles

| Rule | Detail |
|---|---|
| **PostgreSQL is authoritative** | Redis is always rebuildable |
| **Cache-aside** | Read through Redis; populate on miss |
| **Event invalidation** | Domain events trigger DEL of affected keys — no unbounded TTL-only consistency |
| **Never cache writes** | Write-through only for idempotent read models with explicit invalidation |
| **Stampede protection** | Redis lock + stale-while-revalidate for hot keys |

### 9.2 Key namespaces (mandatory prefixes)

| Prefix | Owner spec | Example |
|---|---|---|
| `lg:*` | Learning Graph §13 | `lg:node:{tenant}:{student}:{concept}` |
| `rev:*` | Revision §17 | `rev:today:{tenant}:{student}` |
| `pyq:*` | PYQ §31 | `pyq:insights:{tenant}:{student}` |
| `ca:*` | CA §30 | `ca:priorities:{tenant}:{student}` |
| `twin:*` | Twin spec | `twin:profile:{tenant}:{student}` |

**Do not invent new prefixes** without documenting in the owning spec.

### 9.3 TTL defaults

| Key type | TTL |
|---|---|
| Hot concept node | 60s |
| Dashboard summary | 120s |
| Subject rollups | 300s |
| Catalog adjacency | 24h (invalidate on `DomainCatalogUpdated`) |
| Tool DTO caches (PYQ, CA) | 120s |

### 9.4 Invalidation matrix (minimum)

| Event | Invalidate |
|---|---|
| `LearningGraphUpdated` | `lg:node:*`, `lg:summary:*`, `lg:rollup:*` for affected student |
| `PYQDataChanged` | `pyq:importance:*`, `pyq:insights:*`, `pyq:pool:*` |
| `RevisionPlanGenerated` | `rev:today:{tenant}:{student}` |
| `TwinUpdated` | `twin:profile:{tenant}:{student}`; Mentor session tool cache hash |

---

## 10. API design standards

### 10.1 REST conventions

| Rule | Standard |
|---|---|
| Base path | `/api/v1/` |
| Resources | plural nouns: `/students`, `/assessments`, `/revisions` |
| IDs | UUID in path: `/students/{student_id}` |
| Nested resources | max 2 levels: `/students/{id}/graph/nodes/{concept_id}` |
| Actions | POST verb + action sub-resource: `/assessments/{id}/submit` |
| Pagination | `?cursor=` or `?offset=&limit=`; default `limit=50`, max `200` |
| Filtering | query params; tenant NEVER in query — from auth context |
| Versioning | URL prefix `/v1/`; breaking change → `/v2/` |

### 10.2 Request / response

- All bodies validated with **Pydantic v2** models in `application/{module}/dto/`.
- API layer maps DTO → HTTP response model (may be same type).
- Timestamps in responses: **ISO 8601 UTC** with `Z` suffix.
- Score fields: stored precision 2 decimals; API may expose integer display fields separately (`readiness_display: 72`).
- Use **engine scores** internally; apply **display score rules** (Scoring v1.1) at API read-model boundary for student-facing endpoints.

### 10.3 Authentication

- JWT access token (15 min) + refresh token (7 days) in **HttpOnly Secure cookies** (preferred) or `Authorization: Bearer`.
- Every authenticated route receives `TenantContext` via dependency injection.
- Public routes: `/health`, `/api/v1/auth/register`, `/api/v1/auth/login` only.

### 10.4 OpenAPI

- FastAPI auto-generates OpenAPI; keep `summary`, `description`, and `response_model` on every route.
- Document error responses: 400, 401, 403, 404, 409, 422, 500.

### 10.5 WebSocket (S12+)

- Auth via same JWT (query param or cookie) — spec Master Plan U5.
- Bridge events from Redis pub/sub fed by outbox — **never source of truth**.

### 10.6 Indicative vs canonical APIs

`06-api-spec.md` is **indicative**. On conflict, the **engine specification API section** wins (Assessment, Mentor, PYQ, etc.).

---

## 11. Error handling standards

### 11.1 Domain exceptions

Define in `domain/{module}/exceptions.py`:

```python
class DomainError(Exception):
    code: str
    message: str

class NotFoundError(DomainError): ...
class ConflictError(DomainError): ...
class OptimisticLockError(DomainError): ...
class TenantAccessDeniedError(DomainError): ...
class ValidationError(DomainError): ...
```

### 11.2 HTTP mapping (api layer only)

| Domain exception | HTTP | Body |
|---|---|---|
| `ValidationError` | 422 | `{ "code", "message", "details" }` |
| `NotFoundError` | 404 | `{ "code", "message" }` |
| `TenantAccessDeniedError` | 403 | `{ "code", "message" }` |
| `ConflictError` / `OptimisticLockError` | 409 | `{ "code", "message" }` |
| Unhandled | 500 | Generic message; no stack trace in production |

### 11.3 Error response envelope

```json
{
  "error": {
    "code": "CONCEPT_NOT_FOUND",
    "message": "Concept not found in student graph.",
    "correlation_id": "uuid",
    "details": {}
  }
}
```

### 11.4 Rules

- **Never** catch bare `Exception` in domain/application without re-raising or wrapping.
- **Never** return stack traces to clients in production.
- Log full exception server-side with `request_id`, `tenant_id`, `user_id`.
- Idempotent handlers: duplicate events are **not errors** — return success without mutation.
- Scoring failures: **fail closed** — do not persist partial score updates.

---

## 12. Testing standards

### 12.1 Pyramid

| Layer | Scope | Location | Required |
|---|---|---|---|
| **Unit** | Pure domain, scoring fns, policies | `tests/unit/` | Every domain function |
| **Integration** | Repositories, services, DB, Redis | `tests/integration/` | Every repository + use case |
| **Contract** | API request/response vs OpenAPI | `tests/contract/` | Every public route |
| **E2E** | Critical paths cross-module | `tests/e2e/` | Critical paths below |

### 12.2 Coverage targets

| Area | Target |
|---|---|
| `domain/scoring/` | **100%** line coverage |
| Other domain policies | ≥ 90% |
| Application use cases | ≥ 80% |
| Overall backend | ≥ **80%** (Master Plan §5) |

### 12.3 Mandatory test categories

**Scoring (golden tests):**
- Every worked example in Scoring v1.0 §§2–9 and v1.1 §4 as golden tests
- Boundary: empty data, zero coverage, weight redistribution
- Monotonicity: more correct MCQs → mastery non-decreasing
- Anti-gaming: study-only cap, question dedupe, revision health recall gate
- Retention calibration against reference curve (Scoring v1.0 §3.5)

**Learning Graph:**
- Optimistic lock retry
- Idempotent `event_id` replay
- `unrated → rated` transition on first evidence
- Cross-tenant denial

**Events:**
- Outbox committed iff state committed
- Duplicate delivery does not double-apply
- Partition ordering preserved

**Multi-tenant:**
- Every repository test uses two tenants; asserts isolation

### 12.4 E2E critical paths (V1)

1. Register → login → onboarding → empty graph provisioned
2. MCQ attempt → `AssessmentCompleted` → mastery updated → `TwinUpdated`
3. Revision complete → `RevisionCompleted` → retention updated
4. PYQ ingest → `PYQDataChanged` → importance copied to graph nodes
5. Mentor daily plan generated with `reasoning_json` on every task

### 12.5 AI / agent tests

| Type | Requirement |
|---|---|
| Tool unit tests | Mock application service; assert no DB imports in tool module |
| Eval tests | Plan quality, hallucination rate — gates before production exposure (D5) |
| Deterministic planner | Golden tests on plan assembly without LLM |

### 12.6 Test infrastructure

- **pytest** + **pytest-asyncio**
- Integration tests: real PostgreSQL + Redis via Docker / testcontainers
- Freeze time with `freezegun` or `time-machine` for retention/decay tests
- No production credentials in tests; use `.env.test`

---

## 13. Database standards

### 13.1 General

| Rule | Standard |
|---|---|
| Primary keys | UUID v4 for entities; surrogate `id` + natural unique constraints where needed |
| Timestamps | `timestamptz` stored UTC; `created_at`, `updated_at` on all mutable tables |
| Money | `NUMERIC` — never float |
| Scores | `DECIMAL(5,2)` — range 0–100 |
| JSON profiles | JSONB with Pydantic-validated shapes (Twin profiles) |
| Soft delete | Prefer `status` enum over hard delete for audit-sensitive data |
| Naming | `snake_case` tables and columns |

### 13.2 Required indexes (Learning Graph minimum)

From `LEARNING_GRAPH_SPECIFICATION.md` §16.4:

```sql
-- student_concept_progress
UNIQUE (tenant_id, student_id, concept_id)
INDEX (tenant_id, student_id, node_state, importance_score DESC)
INDEX (tenant_id, student_id, subject_id, node_state)
PARTIAL INDEX WHERE node_state = 'rated'  -- retention batch jobs

-- learning_graph_events
INDEX (tenant_id, student_id, occurred_at)

-- processed_events (per consumer)
UNIQUE (consumer_name, event_id)
```

Each new module spec may add indexes — follow the owning spec.

### 13.3 Optimistic locking

- `student_concept_progress.row_version INT NOT NULL DEFAULT 1`
- Any concurrent update pattern on high-contention rows uses version check
- Revision completion + graph update use **outbox** — not distributed 2PC

### 13.4 Migrations (Alembic)

| Rule | Detail |
|---|---|
| One concern per migration | `add_student_concept_progress`, not `misc_changes` |
| Reversible | Every migration has `downgrade()` |
| No data loss in downgrade | Document if downgrade is destructive |
| Seed data | Separate `seeds/` JSON + loader scripts — not hidden in migrations |
| Formula version bumps | Migration adds version column value + backfill job — not inline mass UPDATE without audit |

### 13.5 Transaction boundaries

- One use case = one transaction unless explicitly saga/outbox
- Graph event application: **event log + node update + audit** = single transaction
- Never hold transactions open across HTTP calls or LLM calls

### 13.6 Event log retention

- `learning_graph_events`: 7 years (LG spec §15.3)
- `processed_events`: 90 days idempotency window

---

## 14. Security standards

### 14.1 Authentication & authorization

- Passwords: **bcrypt** or **argon2** — never plaintext, never reversible encryption
- JWT signed with strong secret from AWS Secrets Manager / env
- Refresh token rotation on use
- RBAC enforced in application layer before any data access
- Rate limit auth endpoints (Redis sliding window)

### 14.2 Data protection

- TLS everywhere in production
- AES at rest (RDS, S3)
- PII fields minimized; no secrets in logs
- S3 paths: `s3://{bucket}/{tenant_id}/{resource_type}/{owner_id}/{filename}`
- Presigned URLs for uploads/downloads — time-limited

### 14.3 Tenant isolation

- Mandatory `tenant_id` filter (§8)
- Optional PostgreSQL RLS (P9)
- Automated test proving cross-tenant access fails

### 14.4 AI security

- Prompt injection guardrails on student-supplied text (Part 8 §29)
- System prompts never expose raw tenant data from other tenants
- Tool calls scoped to authenticated `tenant_id` + `student_id`
- Log prompt version + model — not full prompt in production logs if PII-heavy

### 14.5 Audit

- Audit log for: auth events, faculty overrides, score overrides, admin catalog publishes
- Scoring audit: `{score_name, version, inputs_hash, old_value, new_value, reason, computed_at}` (Scoring v1.0 §1.5)

### 14.6 Compliance (P9 baseline)

- DPDP Act 2023: consent, deletion workflow, retention policy (Master Plan G9/D13)
- Design delete/export hooks in schema now even if UI comes later

---

## 15. AI agent standards

### 15.1 Non-negotiable rules

1. **Agents NEVER import repositories or DB sessions.**
2. **Agents call registered tools only.**
3. **Tools call application services only** — one service method per tool action.
4. **Agents NEVER compute scores** — they read engine scores via tools and explain them.
5. **Agents NEVER override deterministic engine outputs** — faculty override goes through dedicated API.
6. **Every LLM output that affects user-visible plans MUST persist `reasoning_json`.**

### 15.2 Tool structure

```python
# ai/tools/get_learning_graph_tool.py
class GetLearningGraphTool:
    def __init__(self, service: LearningGraphReadService) -> None:
        self._service = service

    async def run(self, ctx: ToolContext, input: GetLearningGraphInput) -> GetLearningGraphOutput:
        # ToolContext carries tenant_id, student_id, correlation_id
        return await self._service.get_graph(ctx.tenant_id, input.student_id, ...)
```

### 15.3 Deterministic vs LLM responsibilities

| Concern | Owner |
|---|---|
| Daily plan task selection | Deterministic Mentor engine (MENTOR spec) |
| Task ordering / time budget | Deterministic |
| `reasoning_json` facts | Engine scores from tools |
| Natural language phrasing | LLM (optional template fallback V1) |
| Mains evaluation | Assessment agent + frontier model (P8) — gated by eval harness |

### 15.4 Model tiering

| Tier | Use | Model class |
|---|---|---|
| Small | classify, route, tag | mini / fast |
| Mid | plan explanation, chat | standard |
| Frontier | Mains eval, complex reasoning | strongest available |

All calls through **`LLMGateway`** interface — OpenAI default; swappable per D6.

### 15.5 Cost & observability

Every LLM call logs:

```
request_id, tenant_id, user_id, agent_name, tool_name,
model, prompt_version, input_tokens, output_tokens,
latency_ms, estimated_cost_usd
```

### 15.6 LangGraph

- Shared state includes: `tenant_id`, `student_id`, `intent`, `messages`, `tool_results` — **not** raw DB rows
- Checkpoint session memory per MENTOR spec §4 (`mentor_session_memory`, 24h TTL)
- Supervisor routes intent — Mentor does not implement Supervisor in V1

### 15.7 Eval gates (before production AI features)

- Hallucination rate threshold (D5)
- Plan accuracy vs deterministic baseline
- Mains eval human-agreement rate
- Features behind flags until eval passes

---

## 16. Coding standards

### 16.1 Typing

- **Full type hints** on all functions, methods, and class attributes
- Use `from __future__ import annotations` in new modules
- Prefer `TypedDict`, `Protocol`, `NewType` where appropriate
- MyPy strict mode in CI — no untyped defs
- Pydantic v2 models for all external I/O

### 16.2 Naming

| Element | Convention |
|---|---|
| Modules | `snake_case` |
| Classes | `PascalCase` |
| Functions / methods | `snake_case` |
| Constants | `SCREAMING_SNAKE_CASE` |
| Private | leading `_` |
| Event types | `PascalCase` matching spec exactly |

### 16.3 Logging (structured)

Every log line includes:

```python
logger.info(
    "graph_node_updated",
    extra={
        "request_id": request_id,
        "tenant_id": str(tenant_id),
        "user_id": str(user_id),
        "student_id": str(student_id),
        "concept_id": concept_id,
        "event_id": str(event_id),
    },
)
```

- **INFO**: business milestones (event applied, plan generated)
- **WARNING**: retry, stale cache served, eval threshold near miss
- **ERROR**: handler failure, dead-letter, optimistic lock exhausted
- **Never log**: passwords, tokens, full LLM prompts with PII

### 16.4 Observability

- OpenTelemetry traces: span per use case, child spans for DB/Redis/LLM
- Propagate `correlation_id` from HTTP → use case → outbox → Celery → handler
- Metrics: event processing latency, cache hit rate, graph update p95, LLM cost counters
- Health endpoint: `/health` checks DB + Redis connectivity

### 16.5 Code quality gates (CI)

- `ruff` lint + format
- `mypy` strict
- `pytest` all tests
- Import linter (optional): enforce layer boundaries
- Pre-commit hooks mirror CI

### 16.6 Documentation in code

- Module docstring: purpose, spec reference, ownership
- Non-obvious business rules: comment with spec section reference
- **Do not** restate entire formulas in comments — link to spec

### 16.7 Prohibited patterns

- Placeholder / mock implementations (except payment provider stub S14 — feature-flagged)
- `# type: ignore` without justification comment
- Global mutable state for tenant context
- Synchronous LLM calls in hot graph update path
- `SELECT *` in production repositories

---

## 17. Production readiness checklist

Before any environment beyond dev, verify:

### 17.1 Infrastructure

- [ ] Docker Compose runs api + worker + beat + postgres + redis
- [ ] Alembic migrations apply cleanly on empty DB
- [ ] Secrets from env / Secrets Manager — not in code or images
- [ ] S3 bucket policies enforce tenant prefix isolation
- [ ] Redis persistence configured for broker durability needs
- [ ] Celery queues routed per DOMAIN_EVENTS §19

### 17.2 Security

- [ ] TLS terminated at load balancer
- [ ] JWT secrets rotated procedure documented
- [ ] Cross-tenant negative tests pass in CI
- [ ] Rate limiting on auth endpoints
- [ ] WAF rules (staging/prod — Part 8)

### 17.3 Observability

- [ ] Structured logs with request/tenant/user IDs
- [ ] Sentry error tracking wired
- [ ] OpenTelemetry traces exported
- [ ] Dashboards: API latency, Celery queue depth, graph update p95, LLM cost
- [ ] Alerts: dead-letter queue depth, outbox lag, error rate spike

### 17.4 Data integrity

- [ ] Outbox pattern on all cross-context producers
- [ ] Idempotent consumers with `processed_events`
- [ ] Learning Graph single-writer enforced in code review
- [ ] Optimistic locking on `student_concept_progress`
- [ ] Scoring functions 100% unit tested
- [ ] Event replay procedure documented

### 17.5 Operational

- [ ] Postgres daily backups (RPO < 24h)
- [ ] Restore drill performed
- [ ] Nightly jobs scheduled 18:30 UTC (configurable)
- [ ] Feature flags for AI surfaces until eval gates pass
- [ ] Runbook for dead-letter replay

---

## 18. Definition of Done — generated modules

A module is **done** only when ALL criteria pass:

### 18.1 Architecture

- [ ] Code lives in correct layer folders (§2)
- [ ] No forbidden imports (§4.2)
- [ ] Repository returns domain objects — not ORM models (§5)
- [ ] Cross-context effects use outbox events (§6)
- [ ] Learning Graph writes only in `learning_graph` module (§7) — if applicable
- [ ] Every query scoped by `tenant_id` (§8)

### 18.2 Specification conformance

- [ ] Implements bounded-context spec for the module
- [ ] Formulas match `domain/scoring/` + relevant spec sections
- [ ] Events match `DOMAIN_EVENTS_SPECIFICATION.md` envelope and registry
- [ ] Cache keys match owning spec prefix/TTL (§9)
- [ ] Display scores follow Scoring v1.1 for student-facing APIs

### 18.3 API

- [ ] OpenAPI documented routes with request/response models
- [ ] Error mapping follows §11
- [ ] Pagination on list endpoints
- [ ] Contract tests pass

### 18.4 Testing

- [ ] Unit tests for all domain logic
- [ ] Integration tests for repositories + use cases
- [ ] Cross-tenant denial test
- [ ] Coverage meets §12.2 targets for touched code
- [ ] Golden tests for any scoring touched

### 18.5 Data

- [ ] Alembic migration with downgrade
- [ ] Indexes per spec (§13)
- [ ] `row_version` on concurrent-update tables

### 18.6 Observability & security

- [ ] Structured logging with correlation IDs
- [ ] AI calls logged with cost metadata — if applicable
- [ ] No secrets committed
- [ ] Audit events for sensitive mutations

### 18.7 Documentation

- [ ] Module README or docstring: purpose, flow, spec links, alternatives considered
- [ ] No placeholder TODOs left in production paths

### 18.8 Review sign-off

- [ ] PR checklist confirms architecture laws (§0.4)
- [ ] Architect review for any graph, scoring, or event schema change

---

## Appendix A — Quick reference: authoritative writers

| Data | Sole writer module |
|---|---|
| `student_concept_progress` scores | `learning_graph` |
| `learning_graph_events` | `learning_graph` |
| `concepts.importance` (global) | `pyq` |
| `revisions.*` | `revision` |
| `preparation_twins.*` profiles | `preparation_twin` |
| `pyq_questions`, `pyq_mappings` | `pyq` |
| `assessment_attempts` | `assessment` |
| `mentor_plans` | `mentor` |
| `current_affairs.*` | `current_affairs` |
| Weakness | **nobody** (computed inline) |

---

## Appendix B — Specification index

| Spec file | Primary focus |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | Graph storage, events, caching, concurrency |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Readiness R3, display, gating |
| `SCORING_ENGINE_SPECIFICATION.md` | Score formulas v1.0 |
| `REVISION_ENGINE_SPECIFICATION.md` | Revision queue, priority v1.1 |
| `PREPARATION_TWIN_SPECIFICATION.md` | Twin projection |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | PYQ + Importance |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | MCQ, mocks, recall |
| `MENTOR_AGENT_SPECIFICATION.md` | Plans, tools, agent |
| `DOMAIN_EVENTS_SPECIFICATION.md` | Events, outbox, Celery |
| `EXAM_DOMAIN_SPECIFICATION.md` | Taxonomy, catalog |
| `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` | CA V2 |
| `MASTER_IMPLEMENTATION_PLAN.md` | Sprint plan |
| `IMPLEMENTATION_GENERATION_MASTER_PROMPT.md` | **This constitution** |

---

## Appendix C — Generator preamble (paste at start of every codegen session)

```
You are implementing PrepOS AI backend code.

MANDATORY READ ORDER:
1. docs/IMPLEMENTATION_GENERATION_MASTER_PROMPT.md (constitution)
2. The relevant docs/*_SPECIFICATION.md for this module
3. docs/DOMAIN_EVENTS_SPECIFICATION.md (if touching events)

RULES:
- Modular monolith, Clean Architecture, Python 3.13+, FastAPI, SQLAlchemy 2.0, Pydantic v2
- NO business logic in API routes
- NO ORM models returned to API
- NO agent/repository direct DB access from agents
- Learning Graph single-writer for student_concept_progress scores
- All cross-context writes via outbox events with event_id idempotency
- Full type hints; pytest tests with module; no placeholders
- Match spec formulas exactly; use domain/scoring/ pure functions

On conflict: LEARNING_GRAPH spec > SCORING v1.1 > SCORING v1.0 > REVISION > ... > MASTER_PLAN

Do not invent behavior not in specs. Flag gaps instead.
```

---

*End of Implementation Generation Master Prompt v1.0. This document governs all PrepOS AI code generation. Update when architecture laws or spec priority resolutions change.*
