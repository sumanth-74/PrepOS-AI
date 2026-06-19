# PrepOS AI — Learning Graph Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for student Learning Graph architecture
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`
Authoring lens: Principal Distributed Systems Architect · Learning Science Expert · Knowledge Graph Architect · Staff Backend Engineer · EdTech Platform Architect

> **Scope.** This document defines the **student Learning Graph**: how per-student knowledge state is stored, updated, queried, cached, recovered, and migrated. It is the implementation contract for `student_concept_progress`, graph lifecycle, event-driven updates, rollups, Mentor traversal inputs, and dashboard read models.
>
> **Non-goals:** UI, marketing, sprint tasks, SQL DDL, LLM prompts. Scoring **formulas** live in `SCORING_ENGINE_SPECIFICATION_V1_1.md`; domain **taxonomy** lives in `EXAM_DOMAIN_SPECIFICATION.md`. This spec defines **graph architecture, storage, algorithms, and boundaries** only.
>
> **Core invariant:** the Learning Graph is the **source of truth for student knowledge state** (blueprint Rule 5). The Preparation Twin, Revision Engine, Mentor Agent, and Readiness are **derived consumers** — they read the graph; only the Learning Graph Service writes concept-level scores.

---

## 0. Canonical requirements map

This document is the authoritative answer to the 18 required areas:

| # | Requirement | Primary section |
|---|---|---|
| 1 | `student_concept_progress` | §4 |
| 2 | Graph node lifecycle | §5 |
| 3 | Graph relationship lifecycle | §6 |
| 4 | Event-driven graph updates | §7 |
| 5 | Mastery storage | §8.1 |
| 6 | Retention storage | §8.2 |
| 7 | Importance storage | §8.3 |
| 8 | Readiness dependencies | §9 |
| 9 | Mentor graph traversal | §10 |
| 10 | Topic rollups | §11.1 |
| 11 | Subject rollups | §11.2 |
| 12 | Dashboard read models | §12 |
| 13 | Catalog version migrations | §14.1 |
| 14 | New concept backfills | §14.2 |
| 15 | Graph caching strategy | §13 |
| 16 | Performance requirements | §16 |
| 17 | Event sourcing requirements | §15 |
| 18 | Data ownership boundaries | §17 |

---

## 1. Purpose

### 1.1 What the Learning Graph is

The Learning Graph is a **tenant-scoped, per-student overlay** on the static domain catalog (`EXAM_DOMAIN_SPECIFICATION.md`). For each active concept in the student's target exam, the platform maintains a **Concept Progress Node** — one row in `student_concept_progress` — holding deterministic scores and evidence metadata.

```
Static domain (shared)                    Per-student overlay (this spec)
─────────────────────                    ───────────────────────────────
exams, subjects, topics, concepts   +    student_concept_progress
concept_relationships (catalog)          (mastery, retention, confidence, importance copy)
                                         learning_graph_events (append-only)
```

Subjects and topics are **not graph nodes with stored scores**. They are **computed rollups** over concept nodes (§11).

### 1.2 Why it exists

UPSC preparation requires tracking **hundreds of concepts per student** with:
- evidence-weighted mastery (not self-report);
- time-decaying retention (Ebbinghaus / stability model);
- exam-weighted importance (PYQ-driven);
- prerequisite-aware planning;
- full auditability and replay.

A generic "progress percentage" cannot support Revision Priority, Readiness (v1.1 R3), or Mentor explainability. The Learning Graph is the structured state those engines require.

### 1.3 Systems that read or write

| System | Read | Write | Notes |
|---|---|---|---|
| **Learning Graph Service** | events, catalog, evidence | **`student_concept_progress`** | sole writer of concept scores |
| **Scoring Engine** | — | via Learning Graph Service only | pure functions; no direct DB writes |
| **Revision Engine** | mastery, retention, importance | `revisions` table only; retention via events | consumes graph; writes revision outcomes as events |
| **Preparation Twin** | graph + rollups | `preparation_twins` profiles | event-rebuilt projection |
| **Mentor Agent** | graph via tools | none | never computes scores |
| **Assessment Engine** | graph for question selection | emits `AssessmentCompleted` events | no direct graph writes |
| **Dashboard Read Model Builder** | graph + rollups | materialized read tables / cache | read-side only |
| **PYQ / Domain services** | — | `concepts.importance` (global) | triggers Importance refresh on graph |

---

## 2. Design Principles

| # | Principle | Rule |
|---|---|---|
| LG1 | **Concept nodes only** | Scores attach to `concept_id`. Subject/topic values are rollups, never stored as authoritative scores. |
| LG2 | **Single writer** | Only Learning Graph Service mutates `student_concept_progress` score columns. |
| LG3 | **Deterministic replay** | Given `learning_graph_events` + catalog snapshot + scoring version config, graph state is reproducible. |
| LG4 | **Event-first updates** | All score changes originate from domain events; no ad-hoc score patches. |
| LG5 | **Version everything** | Every score column has a paired `*_version` field matching `ScoringConfig` formula versions. |
| LG6 | **Tenant isolation** | Every row and query includes `tenant_id`. Cross-tenant reads/writes are forbidden. |
| LG7 | **Optimistic concurrency** | `row_version` on `student_concept_progress`; writers fail fast on conflict and retry with fresh read. |
| LG8 | **Lazy retention, eager mastery** | Mastery updates synchronously on evidence events; Retention materialized on read + nightly batch. |
| LG9 | **Weakness is derived** | Per Scoring v1.1 R1: Weakness is **not** a persisted authoritative column; compute on demand from mastery/retention/confidence/error_rate. |
| LG10 | **Catalog immutability of IDs** | `concept_id` never changes; deprecated concepts remain in graph with `node_state=deprecated`. |
| LG11 | **Idempotent consumers** | Event handlers use `event_id` deduplication; duplicate delivery must not double-apply evidence. |
| LG12 | **Separation of global vs student importance** | Global Importance computed on `concepts.importance`; student copy denormalized to `importance_score` for query performance. |

---

## 3. Graph Architecture

### 3.1 Logical model

```
                    ┌─────────────────────────────────────┐
                    │     Domain Catalog (static)         │
                    │  subjects → topics → concepts       │
                    │  concept_relationships (typed)      │
                    └──────────────┬──────────────────────┘
                                   │ concept_id FK
                    ┌──────────────▼──────────────────────┐
                    │   Student Learning Graph (dynamic)   │
                    │   student_concept_progress (nodes)   │
                    │   learning_graph_events (log)        │
                    │   student_retention_state (optional)   │
                    └──────────────┬──────────────────────┘
           reads   │              │ writes (events)
    ┌──────────────┼──────────────┼──────────────────────┐
    │              │              │                      │
    ▼              ▼              ▼                      ▼
 Revision      Mentor         Twin Builder          Dashboard
 Engine        (tools)        (profiles)            Read Models
                                   │
                                   ▼
                            Readiness (Scoring)
                            (student-level, not stored on graph rows)
```

### 3.2 Node types

| Type | Storage | Has student scores? |
|---|---|:---:|
| **Concept Progress Node** | `student_concept_progress` | Yes |
| **Topic aggregate** | computed / `student_topic_rollups` (read model) | Rollup only |
| **Subject aggregate** | computed / `student_subject_rollups` (read model) | Rollup only |
| **Catalog concept** | `concepts` | Global `importance` only |

### 3.3 Edge types (catalog relationships)

Consumed from `concept_relationships` (`EXAM_DOMAIN_SPECIFICATION.md` §10.2):

| Type | Mentor | Revision | Scoring |
|---|---|---|---|
| `PREREQUISITE` | planning constraint | tie-break only | — |
| `BUILDS_ON` | study sequencing hint | — | — |
| `RELATED_TO` | cross-topic suggestions | — | — |
| `CURRENT_AFFAIRS_OF` | CA-aware planning | priority ×1.15 if recent | — |
| `PYQ_OF` | PYQ drill suggestions | — | Importance input |

Student graph does **not** duplicate catalog edges. Traversal joins `student_concept_progress` to `concept_relationships` at query time (cached adjacency lists per exam catalog version).

### 3.4 Service boundaries (modular monolith)

```
domain/learning_graph/
  entities/          # ConceptProgressNode, GraphEvent
  services/          # LearningGraphService (sole writer)
  repositories/      # ConceptProgressRepository, GraphEventRepository
  policies/          # NodeLifecyclePolicy, ConcurrencyPolicy
  projections/       # RollupCalculator, DashboardReadModelBuilder

application/learning_graph/
  use_cases/         # ApplyGraphEvent, MaterializeRetention, BackfillStudentGraph
  dto/

infrastructure/learning_graph/
  cache/             # Redis key patterns
  read_models/       # rollup tables
```

Scoring pure functions live in `domain/scoring/` and are **called by** `LearningGraphService`, not embedded in repositories.

---

## 4. Node Schema — `student_concept_progress`

The most important table in the platform (`MASTER_IMPLEMENTATION_PLAN.md` §1.5).

### 4.1 Primary key and scope

```
UNIQUE (tenant_id, student_id, concept_id)
```

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | no | Surrogate PK |
| `tenant_id` | UUID | no | Tenant scope |
| `student_id` | UUID | no | FK students |
| `concept_id` | string | no | FK concepts; **Learning Graph node identity** |
| `exam_id` | string | no | Denormalized from student target exam |
| `subject_id` | string | no | Denormalized from concept |
| `topic_id` | string | no | Denormalized from concept |

### 4.2 Score columns (authoritative)

| Column | Type | Writer | Scoring ref |
|---|---|---|---|
| `mastery_score` | decimal(5,2) | Learning Graph Service | Scoring v1.0 §2 |
| `mastery_version` | string | Learning Graph Service | e.g. `mastery_v1` |
| `mastery_nonmcq_score` | decimal(5,2) | Learning Graph Service | Scoring v1.1 §4.2 (optional cache) |
| `mastery_nonmcq_version` | string | Learning Graph Service | e.g. `masterynonmcq_v1` |
| `retention_score` | decimal(5,2) | Learning Graph Service | Scoring v1.0 §3 (materialized) |
| `retention_version` | string | Learning Graph Service | e.g. `retention_v1` |
| `confidence_score` | decimal(5,2) | Learning Graph Service | Scoring v1.0 §13 inputs |
| `confidence_version` | string | Learning Graph Service | e.g. `confidence_v1` |
| `importance_score` | decimal(5,2) | Learning Graph Service | copy of global + personalization |
| `importance_version` | string | Learning Graph Service | e.g. `importance_v1` |

**Not stored (v1.1 R1):** `weakness_score` as authoritative. Optional nullable `weakness_score_cache` for analytics only; MUST be labeled non-authoritative and MAY be stale.

### 4.3 Retention state columns (required for deterministic recompute)

Retention is a function of stability + time (`Scoring v1.0 §3.5`). Persist inputs, not just output.

| Column | Type | Description |
|---|---|---|
| `retention_stability_s` | decimal(8,2) | Current stability `S` (days) |
| `retention_last_event_at` | timestamptz | Start of current decay interval |
| `retention_successful_revisions` | int | Count contributing to stability growth |
| `retention_last_recall_grade` | enum | `forgot` \| `hard` \| `good` \| `easy` \| null |

Optional normalized table `student_retention_events` (append-only) for full replay; if omitted, store compact state above plus `learning_graph_events`.

### 4.4 Evidence and lifecycle columns

| Column | Type | Description |
|---|---|---|
| `node_state` | enum | `unrated` \| `rated` \| `deprecated` (see §5) |
| `n_mcq` | int | Evidence count for mastery shrinkage |
| `n_mains` | int | Evidence count |
| `n_revision` | int | Evidence count |
| `n_study` | int | Evidence count |
| `last_study_at` | timestamptz | nullable |
| `last_revision_at` | timestamptz | nullable |
| `last_assessment_at` | timestamptz | nullable |
| `overconfidence_flag` | bool | Derived: `(confidence − mastery) ≥ 25 AND mastery < 70` |
| `catalog_version_bound` | string | Domain catalog version when node created |
| `row_version` | int | Optimistic lock counter |
| `created_at` | timestamptz | |
| `updated_at` | timestamptz | |

### 4.5 Initial row values (on node creation)

| Field | Initial value |
|---|---|
| `mastery_score` | `0.00` |
| `retention_score` | `null` (displayed as unrated, not "forgotten") |
| `confidence_score` | `null` |
| `importance_score` | copied from `concepts.importance` or computed on first PYQ refresh |
| `node_state` | `unrated` |
| `retention_stability_s` | `null` |
| `n_*` | `0` |

### 4.6 Constraints

1. Row exists only when `concepts.status = active` at creation time (deprecated later → `node_state=deprecated`, row retained).
2. `subject_id` / `topic_id` MUST match concept catalog (application validation).
3. All scores ∈ [0, 100] after rounding rules in Scoring spec §1.3.
4. `tenant_id` MUST match student's tenant (enforced in repository).

---

## 5. Graph Node Lifecycle

### 5.1 State machine

```
                    ┌─────────────┐
         create     │   unrated   │  no evidence; retention=null
        ──────────► │             │  excluded from retention denominators
                    └──────┬──────┘
                           │ first evidence event
                           ▼
                    ┌─────────────┐
                    │    rated    │  ≥1 evidence channel; retention computable
                    │             │  participates in all engines
                    └──────┬──────┘
                           │ concept deprecated in catalog
                           ▼
                    ┌─────────────┐
                    │ deprecated  │  frozen scores; no new evidence accepted
                    │             │  excluded from plans and coverage denom
                    └─────────────┘
```

### 5.2 Transitions

| From | To | Trigger | Side effects |
|---|---|---|---|
| — | `unrated` | Student onboarding; new concept backfill | Insert row; emit `GraphNodeCreated` |
| `unrated` | `rated` | First `StudySessionLogged`, `AssessmentCompleted`, or `RevisionCompleted` on concept | Set `node_state=rated`; compute initial mastery/retention |
| `rated` | `rated` | Subsequent evidence events | Update scores per §7–§8 |
| `*` | `deprecated` | `DomainCatalogUpdated` deprecates concept | Freeze row; emit `GraphNodeDeprecated` |
| `deprecated` | — | no reverse | historical data retained |

### 5.3 Provisioning triggers

| Event | Action |
|---|---|
| `StudentRegistered` + onboarding complete | Bulk insert nodes for all `active` concepts in student's `exam_id` |
| `DomainCatalogUpdated` (new concepts) | Backfill new nodes for affected students (§14.2) |
| Student changes target exam | **Not V1** — requires separate migration workflow |

### 5.4 Node count invariant

```
|{nodes for student S}| = |{concepts WHERE exam_id = S.exam_id AND status = active}| + |{deprecated nodes previously rated}|
```

Active planning uses only `node_state != deprecated`.

---

## 6. Graph Relationship Lifecycle

### 6.1 Ownership

| Data | Owner | Mutability |
|---|---|---|
| `concept_relationships` (catalog) | Domain / Content service | Versioned catalog publishes |
| Student traversal views | Learning Graph (read) | Rebuilt when catalog version changes |

Students do **not** have personal relationship edges in V1.

### 6.2 Catalog relationship lifecycle

```
draft → active → deprecated
```

| Transition | Graph impact |
|---|---|
| New `PREREQUISITE` edge published | Rebuild adjacency cache; Mentor re-evaluates plans |
| Edge deprecated | Remove from traversal cache; historical plans unchanged |
| Cycle detected in `PREREQUISITE` | **Block catalog publish** (EXAM_DOMAIN §10.3) |

### 6.3 Runtime derived edges (not stored on student graph)

| Edge | Source | TTL |
|---|---|---|
| `CURRENT_AFFAIRS_OF` | `current_affairs_mappings` + `concept_relationships` | CA archival policy |
| `PYQ_OF` | `pyq_mappings` | permanent |

### 6.4 Adjacency cache (per catalog version)

```
Redis key: lg:adj:{exam_id}:{catalog_version}:{relationship_type}
Value: serialized adjacency list (concept_id → [concept_id])
Invalidate: on DomainCatalogUpdated
```

Used by Mentor traversal (§10) and prerequisite checks.

---

## 7. Event-Driven Graph Updates

### 7.1 Domain events affecting the graph

| Event | Sync/async | Score impact |
|---|---|---|
| `StudentRegistered` | sync | bulk node create |
| `StudySessionLogged` | sync | mastery (study channel); retention `last_event_at`; may flip `unrated→rated` |
| `AssessmentCompleted` | sync (MCQ) / async (Mains eval) | mastery (MCQ/Mains); confidence; `last_assessment_at` |
| `RevisionCompleted` | sync | mastery (revision channel); retention stability update; `last_revision_at` |
| `PYQDataChanged` | async | global importance refresh → copy to `importance_score` |
| `FacultyWeightUpdated` | async | importance refresh |
| `RetentionMaterializeRequested` | async (nightly) | recompute `retention_score` for active nodes |
| `ScoringFormulaVersionChanged` | async (batch) | full replay backfill (§14) |
| `DomainCatalogUpdated` | async | new nodes / deprecations (§14) |

### 7.2 Processing pipeline

```
Domain Event
     │
     ▼
┌─────────────────┐
│ Event Ingestion │  validate schema, tenant, idempotency (event_id)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Append to       │  learning_graph_events (§15)
│ event log       │
└────────┬────────┘
         ▼
┌─────────────────┐
│ LearningGraph   │  load node (row_version)
│ Service         │  load evidence window from event + stores
└────────┬────────┘
         ▼
┌─────────────────┐
│ Scoring Engine  │  pure functions (mastery, retention, confidence, importance copy)
│ (pure fn call)  │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Persist node    │  optimistic lock row_version
│ + audit record  │  score_audit_log
└────────┬────────┘
         ▼
┌─────────────────┐
│ Publish         │  LearningGraphUpdated (downstream)
│ downstream      │  → Twin, Dashboard projection, analytics
└─────────────────┘
```

### 7.3 Idempotency contract

Every handler MUST:

1. Insert `event_id` into `processed_events` (or use unique constraint on `learning_graph_events.event_id`).
2. If duplicate `event_id`, return success without mutation.
3. Include `causation_id` chain for debugging.

### 7.4 Ordering guarantees

| Scope | Guarantee |
|---|---|
| Per `(tenant_id, student_id, concept_id)` | **Strict serial order** — events processed in `occurred_at` order; use partition key in worker queue |
| Per student (cross-concept) | No ordering required |
| Global Importance refresh | Eventually consistent |

**Implementation:** Celery queue partition key = `{tenant_id}:{student_id}:{concept_id}` for graph mutations.

### 7.5 Downstream event: `LearningGraphUpdated`

Payload:

```json
{
  "event_id": "uuid",
  "tenant_id": "uuid",
  "student_id": "uuid",
  "concept_id": "string",
  "changed_scores": ["mastery", "retention"],
  "mastery_score": 62.5,
  "retention_score": 54.0,
  "node_state": "rated",
  "scoring_versions": { "mastery": "mastery_v1", "retention": "retention_v1" },
  "occurred_at": "ISO8601"
}
```

Consumers: Preparation Twin builder, Dashboard read model invalidation, analytics workers. **Must not** write back to `student_concept_progress`.

---

## 8. Graph Update Algorithms

Scoring formulas are defined in `SCORING_ENGINE_SPECIFICATION_V1_1.md`. This section defines **when and how** the Learning Graph Service invokes them and **what it persists**.

### 8.1 Mastery storage

**Formula:** Scoring v1.0 §2 (40% MCQ / 30% Mains / 20% Revision / 10% Study; weight redistribution; shrinkage).

**Algorithm `ApplyMasteryUpdate`:**

```
INPUT:  node, evidence_event, now
1.  Load evidence aggregates for concept from assessment/revision/study stores
2.  Compute components: mcq_component, mains_component, revision_component, study_component
3.  raw_mastery = redistribute_and_blend(components, weights from ScoringConfig)
4.  mastery = shrink(raw_mastery, n_total, MASTERY_K_CONF, MASTERY_PRIOR)
5.  mastery_nonmcq = MasteryNonMCQ( non-MCQ components only )   // v1.1 §4.2
6.  IF node.node_state == unrated AND n_total > 0: node.node_state = rated
7.  Persist mastery_score, mastery_version, mastery_nonmcq_score, n_*, row_version++
8.  Recompute overconfidence_flag from confidence (if present)
9.  Emit LearningGraphUpdated
```

**Update frequency:**
- **Synchronous** on `AssessmentCompleted`, `RevisionCompleted`, `StudySessionLogged`.
- **Nightly recency pass:** recompute mastery for nodes with evidence in last 90 days (recency weights change daily per §2.3.1).

**Storage location:** `student_concept_progress.mastery_score`, `mastery_nonmcq_score`.

### 8.2 Retention storage

**Formula:** Scoring v1.0 §3 (stability-modulated exponential; default model `stability_exp`).

**Algorithm `ApplyRetentionStateUpdate` (on revision/study):**

```
INPUT:  node, recall_grade | study_event, now
1.  Update retention_last_event_at = now
2.  IF revision:
      apply recall_grade to retention_stability_s per §3.5 (EF multipliers / reset on forgot)
      increment retention_successful_revisions if good/easy
3.  retention_score = 100 * exp(-t/S) with t=0 after event → 100 at event time
4.  Persist retention_* columns
```

**Algorithm `MaterializeRetention` (on-read or nightly):**

```
INPUT:  node, now
1.  t = days(now - retention_last_event_at)
2.  retention_score = 100 * exp(-t / retention_stability_s)
3.  IF node.node_state == unrated: retention_score = null
4.  Persist retention_score, retention_version
```

**Update frequency:**
- State mutation: synchronous on revision/study events.
- Decay materialization: **lazy on read** + **nightly batch** for all `rated` nodes touched in last 90 days.

**Storage location:** `retention_score`, `retention_stability_s`, `retention_last_event_at`, supporting counters.

### 8.3 Importance storage

**Formula:** Scoring v1.0 §4 (PYQ frequency + trend + exam relevance + faculty weight).

**Two-layer model:**

| Layer | Table | Scope |
|---|---|---|
| **Global Importance** | `concepts.importance` | exam + concept |
| **Student copy** | `student_concept_progress.importance_score` | tenant + student + concept |

**Algorithm `RefreshImportanceForExam`:**

```
INPUT:  exam_id, concept_id
1.  global_I = ImportanceEngine(concept, pyq_mappings, faculty_weights)
2.  Persist concepts.importance, concepts.importance_version
3.  FOR each student node with concept_id:
      personalized_I = personalize(global_I, student.optional_subject_id, ...)  // EXAM_DOMAIN §4.10
      node.importance_score = personalized_I
4.  Bulk update with batch size 1000
```

**Update frequency:**
- On `PYQDataChanged`, `FacultyWeightUpdated`, annual recency roll.
- Student copy refreshed whenever global changes (async worker).

**Readiness / Revision consume:** `importance_score` from student node (not live join to PYQ tables).

### 8.4 Confidence storage

**Inputs:** Scoring v1.0 §13 (self-assessment, response speed, consistency).

Updated on assessment events with confidence marking enabled. Stored in `confidence_score`. Drives `overconfidence_flag` only (Scoring v1.1 R4 — not a display gauge).

---

## 9. Readiness Dependencies

Readiness is a **student-level** score (Scoring v1.1 §4), not stored on `student_concept_progress`. The Learning Graph supplies **inputs**.

### 9.1 Input mapping

| Readiness sub-score | Learning Graph inputs |
|---|---|
| `KnowledgeSub` | importance-weighted mean of `mastery_nonmcq_score` over `rated` nodes with non-MCQ evidence |
| `RetentionSub` | importance-weighted mean of `retention_score` over `rated` nodes (unrated retention treated as 0 in sum) |
| `MCQSub` | **Not on graph row** — from assessment service (exam-wide MCQ accuracy) |
| `WritingSub` | **Not on graph row** — from assessment service (Mains) |
| `CASub` | concepts with CA mappings (domain) + activity evidence |
| `coverage` | `|{rated nodes ∩ high_importance concepts}| / |{high_importance concepts}|` |

`high_importance` = `importance_score ≥ HIGH_IMPORTANCE_THRESHOLD (70)` OR config override.

### 9.2 Graph query for Readiness computation

```
rated_nodes = SELECT * FROM student_concept_progress
              WHERE tenant_id=? AND student_id=? AND node_state='rated'

KnowledgeSub = Σ(importance_score * mastery_nonmcq_score) / Σ(importance_score)
                 over rated_nodes WHERE mastery_nonmcq_score IS NOT NULL

RetentionSub   = Σ(importance_score * retention_score) / Σ(importance_score)
                 over rated_nodes WHERE retention_score IS NOT NULL

coverage_num   = COUNT(rated_nodes WHERE importance_score >= 70)
coverage_den   = COUNT(all active non-deprecated nodes WHERE importance_score >= 70)
```

Computed by **Scoring Service** reading graph via repository; result stored on `preparation_twins.prediction_profile.readiness`, not on graph nodes.

### 9.3 Top-2 drivers (Scoring v1.1 R8)

Computed from sub-score shortfalls × weights; requires subject/topic denormalization on graph rows:

```
driver_score(subject) = weighted shortfall contribution to Readiness
return top 2 subjects by driver_score descending
```

Learning Graph provides `subject_id`, `topic_id`, score columns; Scoring/Twin builder computes drivers.

---

## 10. Mentor Graph Traversal

Mentor reads via tools (`GetLearningGraphTool`, etc.) — **never direct DB from agent**. Traversal algorithms below are implemented in `LearningGraphService` query methods.

### 10.1 Traversal modes

| Mode | Purpose | Algorithm |
|---|---|---|
| **Weak frontier** | find study targets | nodes where `importance ≥ 70 AND mastery < 40` ordered by `importance × (100-mastery)` |
| **Revision frontier** | consumed from Revision Engine queue | not recomputed by Mentor |
| **Prerequisite gate** | block premature study | for candidate concept C, all `PREREQUISITE` parents P must have `mastery ≥ PREREQ_MASTERY_FLOOR (40)` |
| **Related expansion** | suggest adjacent topics | BFS depth=1 over `RELATED_TO` from weak frontier nodes |
| **CA boost** | prioritize recent CA-linked concepts | filter nodes with `CURRENT_AFFAIRS_OF` edge from CA published ≤30 days |

### 10.2 Algorithm `GetPlanEligibleConcepts(student, limit)`**

```
1.  Load rated, non-deprecated nodes for student
2.  weak_study = top K by (importance * (100-mastery)) WHERE mastery < 70
3.  Filter weak_study through PrerequisiteGate (§10.1)
4.  related = BFS RELATED_TO depth 1 from weak_study (max M nodes)
5.  Merge revision queue IDs from RevisionService (pre-computed priorities)
6.  Return structured payload: { revisions[], study[], related[] } with score snapshots
```

### 10.3 Prerequisite gate detail

```
PrerequisiteGate(C):
  parents = adjacency[PREREQUISITE][C]   // edges point child → parent (see EXAM_DOMAIN §10.4)
  FOR each P in parents:
    IF node(P).mastery_score < 40 AND node(P).node_state == rated:
       RETURN blocked, reason=P
  RETURN allowed
```

Student explicit override flag on plan item bypasses gate (logged to audit).

### 10.4 Tool response shape (internal)

```json
{
  "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
  "mastery_score": 42.0,
  "retention_score": 55.0,
  "importance_score": 95.0,
  "overconfidence_flag": true,
  "node_state": "rated",
  "prerequisite_blocked": false,
  "subject_id": "upsc.cse.polity",
  "topic_id": "upsc.cse.polity.fundamental_rights"
}
```

Weakness computed inline in Revision Engine / optional field in tool response — **not read from stored weakness column**.

---

## 11. Rollup Algorithms

Rollups are **deterministic projections** for navigation, Twin, and dashboards. They are **not** sources of truth for Scoring formulas.

### 11.1 Topic rollups

Source: `EXAM_DOMAIN_SPECIFICATION.md` §10.5.

```
topic_mastery(student, topic_id) =
  Σ_{c ∈ topic, node_state=rated} (I_c · m_c) / Σ_{c ∈ topic, node_state=rated} (I_c)

topic_retention(student, topic_id) =
  Σ_{c ∈ topic, node_state=rated} (I_c · R_c) / Σ_{c ∈ topic, node_state=rated} (I_c)

topic_coverage(student, topic_id) =
  |{rated concepts in topic}| / |{active concepts in topic}|

topic_rated_count, topic_unrated_count — metadata for Mentor
```

If denominator Σ(I_c) = 0 (no rated nodes), rollup = `null`.

**Parent concept tree rollup (optional):** when parent concept has children, parent display mastery MAY be computed as importance-weighted child rollup for navigation; **assessment still targets leaf concepts** by default.

### 11.2 Subject rollups

```
subject_mastery(student, subject_id) =
  Σ_{c ∈ subject, rated} (I_c · m_c) / Σ_{c ∈ subject, rated} (I_c)

subject_retention(student, subject_id) = same pattern with R_c

subject_importance_mass(student, subject_id) = Σ I_c over active concepts
```

**Strongest/weakest subject** (Twin Knowledge Profile):

```
strongest = argmax_subject(subject_mastery)
weakest   = argmin_subject(subject_mastery) WHERE topic_coverage > 0.2
```

### 11.3 Rollup materialization

| Store | Refresh trigger | TTL |
|---|---|---|
| `student_topic_rollups` | `LearningGraphUpdated`, nightly | invalidate on event |
| `student_subject_rollups` | same | same |
| Redis `lg:rollup:{student}:{subject\|topic}` | same | 300s + event invalidation |

Rollup builder is **idempotent**: recomputing from current graph rows yields same result.

---

## 12. Dashboard Read Models

Read models are **query-optimized projections** for API handlers. They do not define UI.

### 12.1 Read model tables (logical)

#### `student_graph_summary` (1 row per student)

| Column | Source |
|---|---|
| `readiness` | Twin `prediction_profile` |
| `readiness_drivers` | JSON top-2 (Scoring v1.1 R8) |
| `revision_health` | Twin `behavior_profile` |
| `coverage` | graph aggregate |
| `rated_concept_count` | graph count |
| `active_concept_count` | catalog count |
| `last_graph_update_at` | max(node.updated_at) |

#### `student_subject_rollups` / `student_topic_rollups`

As §11. Columns: `student_id`, `subject_id`|`topic_id`, `mastery_avg`, `retention_avg`, `coverage`, `importance_mass`, `computed_at`.

#### `student_concept_snapshots` (optional, for concept drill-down API)

Denormalized slice of `student_concept_progress` joined with `concepts.concept_name` — refreshed on `LearningGraphUpdated` for touched concepts only.

### 12.2 Invalidation flow

```
LearningGraphUpdated(student, concept_id)
  → invalidate Redis keys: lg:student:{id}:summary, lg:rollup:{id}:*
  → enqueue RollupRebuildJob(student, subject_id, topic_id)
  → enqueue DashboardSummaryJob(student)
```

### 12.3 Read path SLA (see §16)

| Query | Target | Path |
|---|---|---|
| Dashboard summary | p95 < 50ms | Redis → fallback recompute |
| Subject rollups list | p95 < 80ms | `student_subject_rollups` |
| Concept node detail | p95 < 30ms | direct `student_concept_progress` PK lookup |
| Full graph export | async | background job |

---

## 13. Graph Caching Strategy

### 13.1 Cache layers

| Layer | Technology | Contents |
|---|---|---|
| **L1 — Request** | in-process LRU | hot concept nodes (single request scope) |
| **L2 — Redis** | ElastiCache | rollups, adjacency, dashboard summary |
| **L3 — PostgreSQL** | RDS | authoritative `student_concept_progress` |
| **L4 — Event log** | PostgreSQL | `learning_graph_events` for replay |

### 13.2 Redis key catalog

| Key pattern | Value | TTL | Invalidate |
|---|---|---|---|
| `lg:node:{tenant}:{student}:{concept}` | serialized node scores | 60s | `LearningGraphUpdated` for concept |
| `lg:summary:{tenant}:{student}` | dashboard summary | 120s | any graph update for student |
| `lg:rollup:subj:{tenant}:{student}` | subject rollups hash | 300s | graph update |
| `lg:rollup:topic:{tenant}:{student}:{subject}` | topic rollups | 300s | graph update |
| `lg:adj:{exam}:{catalog_ver}:{rel_type}` | adjacency list | 24h | `DomainCatalogUpdated` |

### 13.3 Cache-aside pattern

```
read_node(student, concept):
  v = redis.get(key)
  IF v: RETURN v
  row = db.get(student_concept_progress)
  IF retention stale (now - materialized_at > 1h): row = MaterializeRetention(row, now)
  redis.setex(key, 60, row)
  RETURN row
```

**Never cache negative / missing nodes** for unrated concepts without TTL — use short TTL (30s) to prevent stale "unrated" after first event.

### 13.4 Stampede protection

Use Redis lock `lg:lock:rollup:{student}` with 5s lease during rollup rebuild. Concurrent requests serve stale rollup until rebuild completes (stale-while-revalidate).

---

## 14. Backfill and Migration Procedures

### 14.1 Catalog version migrations

**Trigger:** `domain_catalog_version` bump on exam (major or minor).

| Change type | Graph action |
|---|---|
| New concept (`status=active`) | Run `BackfillNewConcepts` (§14.2) |
| Concept deprecated | Set `node_state=deprecated` on all student rows |
| New `PREREQUISITE` edge | Invalidate adjacency cache only |
| `PREREQUISITE` cycle fix | Block publish until resolved |
| Importance inputs change (PYQ remap) | Run `RefreshImportanceForExam` |

**Workflow `MigrateCatalogVersion`:**

```
1.  Load catalog diff (old_version → new_version)
2.  BEGIN batch job (checkpoint table: catalog_migration_runs)
3.  Apply deprecations (sync, fast)
4.  Apply new concept backfill (async, batched by tenant)
5.  Refresh importance (async)
6.  Invalidate all adjacency + rollup caches for exam
7.  Mark migration complete; emit CatalogMigrationCompleted
```

**Checkpointing:** store `last_processed_student_id` per migration run for resumability.

### 14.2 New concept backfill

**Algorithm `BackfillNewConcepts(concept_ids[], exam_id)`:**

```
FOR each tenant batch:
  FOR each student WHERE student.exam_id = exam_id AND status=active:
    FOR each concept_id in concept_ids:
      IF NOT EXISTS node(student, concept_id):
        INSERT student_concept_progress (unrated initial values §4.5)
        EMIT GraphNodeCreated
```

**Performance:** batch size 500 students × bulk insert; target 10k students × 10 new concepts in <10 min.

**Do not** retroactively create evidence; new nodes start `unrated`.

### 14.3 Scoring formula version migration

**Trigger:** `ScoringFormulaVersionChanged` (e.g., `readiness_v1_1`, `mastery_v1` → `mastery_v2`).

```
1.  Shadow mode: compute new scores, log delta distribution (Scoring v1.1 §8.2)
2.  IF delta within tolerance OR approved:
      FOR each event in learning_graph_events chronological:
        replay Apply*Update handlers with new formula version
      OR full recompute from evidence stores (faster than event replay if optimized)
3.  Update *_version columns
4.  Rebuild rollups + Twin + dashboard projections
```

**Source of truth for replay:** evidence stores (assessments, revisions, study sessions) are authoritative; event log is audit trail. Prefer **evidence-based recompute** over naive event replay if handlers are not strictly pure historically.

### 14.4 Student exam migration (future)

Out of V1 scope. Placeholder: archive graph to `student_concept_progress_archive` before reprovisioning.

---

## 15. Event Sourcing Requirements

### 15.1 Event store schema — `learning_graph_events`

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID PK | idempotency key |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `concept_id` | string nullable | null for bulk operations |
| `event_type` | enum | see §7.1 |
| `event_version` | int | schema version |
| `payload` | JSONB | event-specific evidence |
| `score_snapshot_before` | JSONB | optional audit |
| `score_snapshot_after` | JSONB | optional audit |
| `scoring_versions` | JSONB | formula versions used |
| `occurred_at` | timestamptz | business time |
| `recorded_at` | timestamptz | system time |
| `causation_id` | UUID nullable | upstream event |
| `correlation_id` | UUID | request trace |

### 15.2 Event types and payload minimums

| event_type | payload must include |
|---|---|
| `StudySessionLogged` | `session_id`, `concept_id`, `engaged_minutes`, `activity_pings` |
| `AssessmentCompleted` | `assessment_id`, `attempt_id`, `concept_scores[]`, `channel=mcq\|mains` |
| `RevisionCompleted` | `revision_id`, `recall_grade`, `concept_id` |
| `GraphNodeCreated` | `concept_id`, `catalog_version` |
| `GraphNodeDeprecated` | `concept_id`, `reason` |
| `ImportanceRefreshed` | `concept_id`, `old_importance`, `new_importance` |

### 15.3 Retention policy

| Data | Retention |
|---|---|
| `learning_graph_events` | **7 years** (compliance / dispute resolution) |
| `score_audit_log` | 7 years |
| `processed_events` | 90 days (idempotency window) |

### 15.4 Replay requirements

System MUST support:

1. **Single-node replay** for debugging (`replay_events(student, concept, from, to)`).
2. **Full student replay** for formula migration (§14.3).
3. **Deterministic output:** same events + same config ⇒ identical scores (Scoring spec §1.5).

Replay MUST NOT mutate historical event rows; only downstream projections update.

---

## 16. Performance Requirements

Targets align with `MASTER_IMPLEMENTATION_PLAN.md` V1 (10,000 students, thousands of concurrent assessments).

### 16.1 Write path

| Operation | Target | Notes |
|---|---|---|
| `ApplyMasteryUpdate` (sync) | p95 < **150ms** | includes DB write + event append |
| Bulk nightly retention materialize | **≤30 min** for 10k students × ~500 rated nodes | batched Celery |
| Importance refresh (exam-wide) | **≤15 min** async | off critical path |
| Catalog backfill (10 new concepts × 10k students) | **≤10 min** | bulk insert |

### 16.2 Read path

| Operation | Target |
|---|---|
| Single concept node | p95 < **30ms** |
| Dashboard summary (cached) | p95 < **50ms** |
| Subject rollups (17 subjects) | p95 < **80ms** |
| Mentor `GetPlanEligibleConcepts` | p95 < **200ms** |
| Full graph export (500 nodes) | async; **≤5s** worker job |

### 16.3 Storage estimates (10k students)

| Entity | Rows | Approx size |
|---|---|---|
| `student_concept_progress` | 10k × ~500 active ≈ **5M rows** | ~2 GB with indexes |
| `learning_graph_events` | ~50 events/student/month | plan partitioning by month |
| `student_subject_rollups` | 10k × 17 ≈ **170k rows** | small |

### 16.4 Indexing (logical)

- PK `(tenant_id, student_id, concept_id)` on `student_concept_progress`
- `(tenant_id, student_id, node_state, importance_score DESC)` for Mentor weak frontier
- `(tenant_id, student_id, subject_id, node_state)` for rollups
- `(tenant_id, student_id, occurred_at)` on `learning_graph_events`
- Partial index WHERE `node_state = 'rated'` for retention batch jobs

### 16.5 Partitioning (Phase 2+, 100k students)

- `student_concept_progress` hash partition on `tenant_id` or `student_id`
- `learning_graph_events` time-range partition on `occurred_at` (monthly)

---

## 17. Data Ownership Boundaries

### 17.1 Write ownership matrix

| Data | Sole writer | Readers |
|---|---|---|
| `student_concept_progress.*score*` | **Learning Graph Service** | all engines (read-only) |
| `learning_graph_events` | Learning Graph Service (append) | replay jobs, audit |
| `concepts.importance` | Importance refresh job (via Scoring fn) | Learning Graph (copy), PYQ engine |
| `concept_relationships` | Domain catalog service | Learning Graph (traverse) |
| `preparation_twins.*` | Twin builder | Mentor, APIs |
| `revisions` | Revision Engine | Mentor, Twin |
| `student_*_rollups` | Rollup projection worker | Dashboard APIs |
| Weakness | **nobody persists authoritatively** | computed inline (Scoring v1.1 R1) |

### 17.2 Forbidden operations

1. Mentor Agent writing scores (architecture Rule 3).
2. API routes mutating `mastery_score` directly.
3. Assessment module updating graph without emitting domain event.
4. Twin builder writing to `student_concept_progress`.
5. Cross-tenant reads even for "analytics aggregation" without tenant filter.

### 17.3 Repository contract

```python
# ConceptProgressRepository — ONLY called from LearningGraphService
get_node(tenant_id, student_id, concept_id) -> ConceptProgressNode
save_node(node, expected_row_version) -> None  # raises OptimisticLockError
list_rated_nodes(tenant_id, student_id, filters) -> list[ConceptProgressNode]
bulk_insert_unrated_nodes(tenant_id, student_id, concept_ids[]) -> int

# FORBIDDEN on repository:
# patch_mastery_direct(), upsert_without_event()
```

### 17.4 Audit

Every score mutation writes to `score_audit_log`:

```
{ tenant_id, student_id, concept_id, score_name, old, new, version, event_id, request_id, at }
```

---

## 18. Database Representation

### 18.1 Core entities (logical ER)

```
exams ──< subjects ──< topics ──< concepts
                                  │
students ──< student_concept_progress >── concepts
         ──< learning_graph_events
         ──< student_subject_rollups   (read model)
         ──< student_topic_rollups     (read model)

concepts ──< concept_relationships >── concepts
pyq_questions ──< pyq_mappings >── concepts
current_affairs ──< current_affairs_mappings >── concepts
```

### 18.2 Table summary

| Table | Purpose | Writer |
|---|---|---|
| `student_concept_progress` | **Graph nodes** | Learning Graph Service |
| `learning_graph_events` | Event log | Learning Graph Service |
| `processed_events` | Idempotency | Learning Graph Service |
| `score_audit_log` | Audit | Learning Graph Service |
| `student_subject_rollups` | Read model | Projection worker |
| `student_topic_rollups` | Read model | Projection worker |
| `student_graph_summary` | Read model | Projection worker |
| `catalog_migration_runs` | Migration checkpoint | Migration job |
| `student_retention_events` | Optional retention detail | Learning Graph Service |

### 18.3 Relationship to legacy `syllabus_nodes`

`MASTER_IMPLEMENTATION_PLAN` references `syllabus_nodes` from early blueprint. **Canonical V1 mapping:**

| Legacy | This spec |
|---|---|
| `syllabus_nodes` (Subject/Topic/Concept levels) | Split into `subjects`, `topics`, `concepts` (`EXAM_DOMAIN_SPECIFICATION.md`) |
| `student_concept_progress.concept_id` | FK to `concepts.concept_id` |

If `syllabus_nodes` table exists during migration, treat as **deprecated view** over subjects/topics/concepts or migrate with one-time ETL.

---

## 19. Failure Recovery

### 19.1 Optimistic lock conflict

```
ON OptimisticLockError:
  reload node
  re-apply event idempotently (same event_id deduped if already applied)
  retry max 3 times with jitter
  IF still failing: dead-letter queue + alert
```

### 19.2 Partial batch failure (nightly retention)

Checkpoint per `(tenant_id, student_id)`; resume from last success. Nodes already materialized in run are skipped via `retention_materialized_at` marker.

### 19.3 Event handler failure

| Failure | Action |
|---|---|
| Transient DB | Celery retry with exponential backoff |
| Scoring domain error | dead-letter + no partial score write |
| Duplicate event | ack silently |
| Corrupt payload | quarantine event; alert; no graph mutation |

### 19.4 Recovery invariant

After any failure, **`student_concept_progress` MUST reflect a consistent subset of applied events** — never half-updated mastery without corresponding audit/event row. Use **single transaction** per event application: event insert + node update + audit.

### 19.5 Disaster recovery

- PostgreSQL PITR (RPO < 24h per DevOps spec).
- Redis cache loss: cold rebuild from PostgreSQL; no data loss.
- Replay graph from events + evidence if DB corruption isolated to progress table.

---

## 20. Future Multi-Exam Support

Aligned with `EXAM_DOMAIN_SPECIFICATION.md` §15 — **no Learning Graph redesign**.

### 20.1 Isolation model

| Dimension | Strategy |
|---|---|
| Catalog | `exam_id` on all domain tables |
| Student graph | `student.exam_id` determines node set |
| Events | include `exam_id` in payload |
| Rollups | scoped per exam |
| Cache keys | include `exam_id` |

### 20.2 Multi-exam student (V3)

One student preparing for UPSC + APPSC:

- Separate `student_concept_progress` rows per `(student, concept_id)` — concepts namespaced by exam code (`upsc.cse.*` vs `appsc.group1.*`).
- Optional `RELATED_TO` edges across exams in catalog.
- Readiness computed per exam context; no merged Readiness in V1/V2.

### 20.3 Cross-exam analytics (institute)

Faculty aggregates MAY span exams by querying multiple node sets with explicit exam filter — never implicit merge.

---

## Appendix A — Event → score mutation matrix

| Event | mastery | mastery_nonmcq | retention state | retention score | confidence | importance | node_state |
|---|---|---|---|---|---|---|---|
| StudySessionLogged | ✓ | ✓ | ✓ t=0 | ✓ | — | — | maybe → rated |
| AssessmentCompleted (MCQ) | ✓ | — | — | lazy | ✓ | — | maybe → rated |
| AssessmentCompleted (Mains) | ✓ | ✓ | — | lazy | — | — | maybe → rated |
| RevisionCompleted | ✓ | ✓ | ✓ | ✓ | — | — | maybe → rated |
| PYQDataChanged | — | — | — | — | — | ✓ global+copy | — |
| RetentionMaterialize (nightly) | recency | recency | — | ✓ | — | — | — |
| DomainCatalogUpdated | — | — | — | — | — | maybe | deprecated/new |

---

## Appendix B — Configuration keys (Learning Graph)

| Key | Default | Purpose |
|---|---|---|
| `PREREQ_MASTERY_FLOOR` | 40 | Mentor prerequisite gate |
| `HIGH_IMPORTANCE_THRESHOLD` | 70 | Readiness coverage denom |
| `RETENTION_MATERIALIZE_INTERVAL_HOURS` | 24 | nightly + lazy threshold |
| `MASTERY_RECENCY_BATCH_DAYS` | 90 | nightly mastery recency pass |
| `GRAPH_NODE_CACHE_TTL_SECONDS` | 60 | Redis L2 |
| `ROLLUP_CACHE_TTL_SECONDS` | 300 | Redis rollups |
| `GRAPH_EVENT_IDEMPOTENCY_TTL_DAYS` | 90 | processed_events retention |
| `CA_REVISION_PRIORITY_BOOST` | 1.15 | EXAM_DOMAIN §12.3 |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `REVISION_ENGINE_SPECIFICATION` (future) | §7 events, §8.2 retention, importance inputs, priority consumes graph |
| `MENTOR_AGENT_SPECIFICATION` (future) | §10 traversal, tool shapes, prerequisite gate |
| `PREPARATION_TWIN_SPECIFICATION` (future) | §11 rollups, §9 Readiness inputs, event subscriptions |
| API layer | §12 read models, §13 caching |
| Scoring Engine | §8 invoke points; formulas unchanged |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `EXAM_DOMAIN_SPECIFICATION.md` §10 | Node set, relationships, rollups — inherited verbatim |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | MasteryNonMCQ cache, Weakness not persisted, Readiness inputs |
| `MASTER_IMPLEMENTATION_PLAN.md` | Single writer, event-driven, 10k scale, modular monolith |
| Blueprint Rule 5 | Learning Graph is source of truth — §1, §17 |
| Blueprint Rule 4 | Explainability via event log + audit — §15 |

---

*End of Learning Graph Specification v1.0. This document is the canonical architecture for student knowledge state. Implement `LearningGraphService` as the sole writer of `student_concept_progress`; all other systems consume via repositories, tools, and projections defined here.*
