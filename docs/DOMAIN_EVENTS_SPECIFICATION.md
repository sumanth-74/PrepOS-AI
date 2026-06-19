# PrepOS AI — Domain Events Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for cross-engine event architecture
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, all `*_SPECIFICATION.md` engine documents, `06-api-spec.md`
Authoring lens: Principal Distributed Systems Architect · Staff Backend Architect · Event-Driven Systems Designer

> **Scope.** This document unifies **domain event contracts**, **outbox/idempotency**, **ordering guarantees**, **consumer/producer registry**, **Celery routing**, and **failure recovery** across PrepOS bounded contexts. Individual engines define *business semantics* in their specs; this document defines *how events move* and *what every handler must obey*.
>
> **Non-goals:** UI, marketing, sprint tasks, SQL DDL, business formulas (Scoring specs), individual handler algorithms (engine specs).
>
> **Core invariant:** every cross-context state change that affects another bounded context MUST pass through a **versioned domain event** with **`event_id` idempotency** and **durable outbox** before async fan-out. No service writes another context's authoritative tables.

---

## 0. Canonical requirements map

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and event taxonomy | §1 |
| 2 | Global event envelope | §2 |
| 3 | Outbox pattern | §3 |
| 4 | Idempotency contract | §4 |
| 5 | Ordering guarantees | §5 |
| 6 | Producer registry | §6 |
| 7 | Consumer registry | §7 |
| 8 | Critical path flows | §8 |
| 9 | Platform lifecycle events | §9 |
| 10 | Learning Graph events | §10 |
| 11 | Revision Engine events | §11 |
| 12 | Assessment Engine events | §12 |
| 13 | PYQ Intelligence events | §13 |
| 14 | Current Affairs Engine events | §14 |
| 15 | Preparation Twin events | §15 |
| 16 | Mentor Agent events | §16 |
| 17 | Domain catalog events | §17 |
| 18 | Study session events | §18 |
| 19 | Celery queue routing | §19 |
| 20 | `processed_events` stores | §20 |
| 21 | Dead letter and retry | §21 |
| 22 | Replay and migration | §22 |
| 23 | WebSocket bridge events | §23 |
| 24 | Event versioning | §24 |
| 25 | Observability | §25 |
| 26 | Consistency checklist | Appendix D |

---

## 1. Purpose and event taxonomy

### 1.1 Why this document exists

PrepOS uses **event-driven integration** between modular monolith bounded contexts. Without a unified contract:

- Duplicate `event_id` handling diverges per team.
- Outbox vs fire-and-forget inconsistencies cause lost updates.
- Ordering bugs corrupt `student_concept_progress`.
- Twin double-rebuilds waste compute.

This spec is the **integration layer** above engine specs.

### 1.2 Event classes

| Class | Scope | Examples |
|---|---|---|
| **Domain event** | Cross-context business fact | `AssessmentCompleted`, `RevisionCompleted` |
| **Integration event** | Derived notification / projection | `LearningGraphUpdated`, `TwinUpdated` |
| **Command event** | Scheduled work request | `RetentionMaterializeRequested`, `NightlyTwinRebuildRequested` |
| **Internal event** | Single-context only | `ImportanceRecomputeCompleted`, `MentorLLMValidationFailed` |

**Rule:** only **Domain** and **Integration** events use the global envelope (§2). Internal events MAY use a reduced envelope within one module.

### 1.3 Transport (V1)

| Layer | Technology |
|---|---|
| Durable write | PostgreSQL outbox table per producer context |
| Async dispatch | Celery workers |
| Fan-out (optional) | Redis pub/sub for WebSocket bridge |
| Sync in-process | Direct service call **only** within same transaction boundary (e.g. graph handler in API process) |

No Kafka in V1. Design allows future extraction.

### 1.4 Naming convention

```
PascalCase past tense for facts:     AssessmentCompleted
PascalCase for commands:             RetentionMaterializeRequested
NO prefixes like prepos.             event_type string is global enum
```

---

## 2. Global event envelope

### 2.1 Required fields (all domain/integration events)

```json
{
  "event_id": "uuid-v4",
  "event_version": 1,
  "event_type": "AssessmentCompleted",
  "occurred_at": "2026-06-18T10:30:00Z",
  "recorded_at": "2026-06-18T10:30:00.512Z",
  "tenant_id": "uuid",
  "correlation_id": "uuid",
  "causation_id": "uuid-nullable",
  "producer": "assessment_service",
  "payload": { }
}
```

| Field | Rule |
|---|---|
| `event_id` | UUID v4; **global idempotency key** |
| `event_version` | Schema version for `payload`; increment on breaking change |
| `occurred_at` | Business time (UTC) |
| `recorded_at` | System insert time |
| `tenant_id` | Required; null only for platform-global catalog events with explicit flag |
| `correlation_id` | Trace across chain (request_id or workflow id) |
| `causation_id` | Parent `event_id` if caused by another event |
| `producer` | Bounded context service name |
| `payload` | Event-specific; documented in §6–§18 |

### 2.2 Optional metadata

```json
"metadata": {
  "exam_id": "upsc_cse",
  "student_id": "uuid",
  "schema_ref": "assessment_completed_v1"
}
```

Promoted fields (`student_id`, `exam_id`) SHOULD appear in metadata for routing without parsing full payload.

### 2.3 Platform-global events

When `tenant_id` is null (e.g. `PYQDataChanged` for global catalog):

```json
"metadata": { "scope": "platform", "exam_id": "upsc_cse" }
```

Consumers MUST NOT apply to wrong tenant.

---

## 3. Outbox pattern

### 3.1 Producer obligation

Every emitting service:

```
BEGIN TRANSACTION
  1. Mutate authoritative state (assessments row, revisions row, etc.)
  2. INSERT into {context}_outbox (
       event_id, event_type, payload, status='pending', recorded_at
     )
COMMIT
  3. Publisher worker reads pending → publish to Celery → status='published'
```

**Never** publish to Celery before DB commit.

### 3.2 Outbox tables (logical)

| Table | Owner |
|---|---|
| `learning_graph_outbox` | Learning Graph (for `LearningGraphUpdated`) |
| `assessment_outbox` | Assessment |
| `revision_outbox` | Revision |
| `pyq_outbox` | PYQ |
| `ca_outbox` | Current Affairs |
| `twin_outbox` | Twin (for `TwinUpdated`) |
| `mentor_outbox` | Mentor |

Single-table `domain_outbox` is acceptable in modular monolith if namespaced by `producer` column.

### 3.3 Publisher sweeper

| Condition | Action |
|---|---|
| `status=pending` AND `age > 5 min` | Retry publish |
| `status=published` AND `age > 7 days` | Archive/delete per retention |
| Publish fails 5× | `status=failed`; alert; DLQ (§21) |

### 3.4 At-least-once delivery

Consumers MUST be **idempotent** (§4). Producers guarantee **at-least-once** publish, not exactly-once end-to-end.

---

## 4. Idempotency contract

### 4.1 Consumer algorithm

```
HandleEvent(envelope):
  1.  VALIDATE envelope schema + tenant scope
  2.  INSERT INTO {consumer}_processed_events (event_id, event_type, processed_at)
      ON CONFLICT (event_id) DO NOTHING
      RETURNING inserted
  3.  IF NOT inserted: RETURN 200 OK (already processed)
  4.  Execute handler (may be no-op if state already reflects event)
  5.  COMMIT
```

### 4.2 Processed event retention

| Store | Retention |
|---|---|
| `{service}_processed_events` | **90 days** (config `EVENT_IDEMPOTENCY_TTL_DAYS`) |
| Audit / replay | `learning_graph_events`, `revision_events`, `twin_events` — 7 years where applicable |

After TTL, **replay safety** relies on handler no-op when state already applied.

### 4.3 Natural keys (supplement)

Some handlers also dedupe on business keys:

| Handler | Natural key |
|---|---|
| `CompleteRevision` | `(revision_id, recall_session_id)` |
| Mentor plan generation | `(student_id, plan_date, horizon, regenerate=false)` |
| Assessment scoring | `(attempt_id)` for `AssessmentCompleted` |

`event_id` remains primary; natural keys prevent duplicate facts from different events.

### 4.4 Forbidden patterns

1. Consumer writes producer's authoritative table.
2. Skip idempotency because handler "looks safe."
3. Use `assessment_id` alone as idempotency for `AssessmentCompleted` (retries must use new `event_id` only on new facts).

---

## 5. Ordering guarantees

### 5.1 Strict serial (MUST)

| Partition key | Scope | Reason |
|---|---|---|
| `{tenant_id}:{student_id}:{concept_id}` | Learning Graph mutations | Score consistency |
| `{tenant_id}:{student_id}:{revision_id}` | Revision completion | Single terminal state |
| `{tenant_id}:{student_id}:{attempt_id}` | Assessment scoring | One completion event |

Celery queue routing uses partition key as task routing id where supported.

### 5.2 Per-student soft order (SHOULD)

Twin rebuilds for same student debounced 5s (`PREPARATION_TWIN_SPECIFICATION.md` §9.3) to coalesce `AssessmentCompleted` + `LearningGraphUpdated`.

### 5.3 No cross-student order

Bulk jobs (`PYQDataChanged`, `DomainCatalogUpdated`) process students in arbitrary batch order.

### 5.4 Causation chains

Expected chains:

```
AssessmentCompleted → LearningGraphUpdated → TwinUpdated
RevisionCompleted → LearningGraphUpdated → TwinUpdated
PYQDataChanged → (importance copy per student batches) → LearningGraphUpdated*
```

*May batch many concepts into one `LearningGraphUpdated` per student or emit per concept per LG spec.

---

## 6. Producer registry

Master list of **who emits what**. Payload details in cited engine spec sections.

| Event | Producer | Class | Sync/async | Spec ref |
|---|---|---|---|---|
| `StudentRegistered` | Auth/Onboarding | Domain | sync | §9.1 |
| `StudentOnboardingCompleted` | Onboarding | Domain | sync | §9.2 |
| `StudentPreferencesUpdated` | Student profile | Domain | sync | §9.3 |
| `StudentExamDateChanged` | Student profile | Domain | sync | §9.4 |
| `StudySessionLogged` | Study / CA bridge | Domain | sync | §18 |
| `AssessmentSubmitted` | Assessment | Internal→Domain | sync | §12.1 |
| `AssessmentCompleted` | Assessment | Domain | sync MCQ | §12.2 |
| `AssessmentScoringFailed` | Assessment | Internal | async | §12.3 |
| `AnswerEvaluated` | Assessment | Domain | async | §12.4 |
| `RecallSessionCompleted` | Assessment | Internal | sync | §12.5 |
| `DiagnosticCompleted` | Assessment | Domain | sync | §12.2 |
| `RevisionPlanGenerated` | Revision | Integration | async | §11.1 |
| `RevisionCompleted` | Revision | Domain | sync | §11.2 |
| `RevisionMissed` | Revision | Domain | async | §11.3 |
| `RevisionSkipped` | Revision | Domain | sync | §11.4 |
| `RevisionBacklogIntervention` | Revision | Domain | async | §11.5 |
| `RevisionBacklogCompressed` | Revision | Domain | async | §11.6 |
| `RevisionSessionStarted` | Revision | Domain | sync | §11.7 |
| `RevisionSessionCompleted` | Revision | Domain | sync | §11.7 |
| `RevisionSessionAbandoned` | Revision | Domain | sync | §11.7 |
| `RevisionHealthRecomputed` | Revision | Integration | async | §11.8 |
| `RevisionFatigueRecomputed` | Revision | Integration | async | §11.8 |
| `RevisionStreakRecomputed` | Revision | Integration | async | §11.8 |
| `LearningGraphUpdated` | Learning Graph | Integration | sync/async | §10.1 |
| `GraphNodeCreated` | Learning Graph | Integration | async | §10.2 |
| `GraphNodeDeprecated` | Learning Graph | Integration | async | §10.2 |
| `PYQDataChanged` | PYQ Intelligence | Domain | async | §13.1 |
| `FacultyWeightUpdated` | PYQ Intelligence | Domain | async | §13.2 |
| `PYQIngestionCompleted` | PYQ | Internal | async | §13.3 |
| `CurrentAffairsPublished` | CA Engine | Domain | async | §14.1 |
| `CurrentAffairsEngaged` | CA Engine | Domain | sync | §14.2 |
| `CurrentAffairsArchived` | CA Engine | Domain | async | §14.3 |
| `TwinUpdated` | Twin Builder | Integration | async | §15.1 |
| `TwinProvisioned` | Twin Builder | Integration | sync | §15.2 |
| `TwinRebuildCompleted` | Twin Builder | Internal | async | §15.3 |
| `TwinRebuildFailed` | Twin Builder | Internal | async | §15.4 |
| `MentorPlanGenerated` | Mentor | Integration | sync | §16.1 |
| `MentorInterventionTriggered` | Mentor | Domain | sync | §16.2 |
| `MentorFacultyEscalation` | Mentor | Domain | async | §16.3 |
| `MentorPlanSuperseded` | Mentor | Internal | sync | §16.4 |
| `DomainCatalogUpdated` | Exam Domain | Domain | async | §17.1 |
| `ScoringFormulaVersionChanged` | Config/Admin | Command | async | §17.2 |
| `RetentionMaterializeRequested` | Scheduler | Command | async | §10.3 |
| `RetentionSnapshotBuilt` | Revision | Integration | async | §11.9 |
| `NightlyTwinRebuildRequested` | Scheduler | Command | async | §15.5 |

---

## 7. Consumer registry

| Event | Consumer(s) | Action summary | Spec ref |
|---|---|---|---|
| `StudentRegistered` | LG, Twin, Mentor, Revision, CA, PYQ | Provision nodes, twin, plans | §9 |
| `AssessmentCompleted` | Learning Graph, Twin, Mentor, Analytics | Mastery/confidence; twin assessment; cache | §12 |
| `RevisionCompleted` | Learning Graph | Mastery/retention | §11 |
| `LearningGraphUpdated` | Twin, Mentor cache, Dashboard | Partial rebuild; invalidation | §10 |
| `PYQDataChanged` | Learning Graph, Twin, Mentor, Assessment | Importance copy; cache | §13 |
| `FacultyWeightUpdated` | Learning Graph, Twin | Importance refresh | §13 |
| `CurrentAffairsPublished` | Revision, Mentor, Assessment | CA relevance; cache | §14 |
| `CurrentAffairsEngaged` | Twin | CA profile | §14 |
| `TwinUpdated` | Mentor, Dashboard, WebSocket | Replan threshold; UI | §15 |
| `RevisionBacklogIntervention` | Mentor | Intervention engine | §11 |
| `RevisionHealthRecomputed` | Twin, Mentor | Behavioral profile | §11 |
| `RevisionFatigueRecomputed` | Twin | Fatigue slice | §11 |
| `RevisionStreakRecomputed` | Twin | Streak slice | §11 |
| `DomainCatalogUpdated` | LG, Revision, PYQ, CA, Twin | Catalog sync | §17 |
| `ScoringFormulaVersionChanged` | LG, Twin, Revision | Replay/backfill | §22 |
| `MentorPlanGenerated` | WebSocket, Analytics | UI push | §16 |
| `StudySessionLogged` | Learning Graph, Twin | Mastery study channel | §18 |

### 7.1 Explicit non-consumers

| Event | Service | Reason |
|---|---|---|
| `RevisionCompleted` | Twin (direct) | Via `LearningGraphUpdated` only |
| `MentorPlanGenerated` | Twin | Output not input |
| `RevisionPlanGenerated` | Twin | Queue owned by Revision |

Documented in `PREPARATION_TWIN_SPECIFICATION.md` §15.1.

---

## 8. Critical path flows

### 8.1 MCQ assessment loop (S10)

```
POST /assessments/{id}/submit
  → AssessmentSubmitted (optional audit)
  → Score pipeline
  → AssessmentCompleted [outbox]
       → LG: ApplyMasteryUpdate + ApplyConfidenceUpdate
       → LearningGraphUpdated [outbox]
            → Twin: PartialRebuild (debounced)
            → TwinUpdated
       → Mentor: invalidate assess cache
  → WebSocket: assessment_complete
```

**SLA:** `AssessmentCompleted` → `LearningGraphUpdated` p95 **< 500ms** (MCQ sync).

### 8.2 Revision completion loop (S5)

```
POST /revisions/{id}/complete
  → RevisionCompleted [outbox]
       → LG: ApplyMasteryUpdate + ApplyRetentionStateUpdate
       → LearningGraphUpdated
            → Twin: debounced rebuild
  → RevisionHealthRecomputed (async)
       → Twin: behavioral.revision.health
```

### 8.3 PYQ importance propagation (S7)

```
PYQ publish → PYQDataChanged [outbox]
  → LG: RefreshImportanceForExam (batched all students)
  → LearningGraphUpdated (batched)
  → Twin: prediction partial rebuild
  → Mentor/PYQ/Assessment: cache invalidation
```

**SLA:** all students importance copied p95 **< 15 min**.

### 8.4 Mentor daily plan (S8)

```
GET /mentor/today (or scheduled job)
  → Read Twin, Graph ports, Revision, PYQ, CA, Assessment tools
  → Persist mentor_plans
  → MentorPlanGenerated [outbox]
  → WebSocket: plan_generated
```

No domain events consumed for plan **content** except prior state built from events.

---

## 9. Platform lifecycle events

### 9.1 `StudentRegistered`

```json
{
  "event_type": "StudentRegistered",
  "payload": {
    "student_id": "uuid",
    "user_id": "uuid",
    "exam_id": "upsc_cse",
    "tenant_id": "uuid"
  }
}
```

**Consumers:** Learning Graph (bulk node create), Twin (`TwinProvisioned`), Mentor (schedule first plan), Revision (initial plan materialization).

### 9.2 `StudentOnboardingCompleted`

Payload: `student_id`, `diagnostic_offered`, `target_stages[]`.

Twin: `FullRebuild`.

### 9.3 `StudentPreferencesUpdated`

Payload: changed preference keys. Mentor: replan next day.

### 9.4 `StudentExamDateChanged`

Payload: `old_date`, `new_date`, `days_to_exam`. Revision: recompute proximity factor; Twin: prediction refresh.

---

## 10. Learning Graph events

### 10.1 `LearningGraphUpdated`

**Producer:** Learning Graph Service  
**Spec:** `LEARNING_GRAPH_SPECIFICATION.md` §7.5

```json
{
  "event_type": "LearningGraphUpdated",
  "payload": {
    "student_id": "uuid",
    "concept_id": "upsc.cse.polity...",
    "changed_scores": ["mastery", "retention"],
    "mastery_score": 62.5,
    "retention_score": 54.0,
    "node_state": "rated",
    "scoring_versions": { "mastery": "mastery_v1", "retention": "retention_v1" }
  }
}
```

**Partition key:** `{tenant}:{student}:{concept}`.

### 10.2 `GraphNodeCreated` / `GraphNodeDeprecated`

Catalog lifecycle; Twin coverage denominators; Revision cancels deprecated concept revisions.

### 10.3 `RetentionMaterializeRequested`

Nightly command; LG batch materializes decayed retention scores.

---

## 11. Revision Engine events

**Spec:** `REVISION_ENGINE_SPECIFICATION.md` §12

### 11.1 `RevisionPlanGenerated`

Daily queue materialized; Dashboard projection; Mentor cache invalidation.

### 11.2 `RevisionCompleted` (critical)

```json
{
  "event_type": "RevisionCompleted",
  "payload": {
    "revision_id": "uuid",
    "student_id": "uuid",
    "concept_id": "string",
    "recall_grade": "good",
    "recall_session_id": "uuid",
    "lateness_class": "on_time"
  }
}
```

**Sole trigger** for LG revision-channel mastery/retention update.

### 11.3–11.6

`RevisionMissed`, `RevisionSkipped`, `RevisionBacklogIntervention`, `RevisionBacklogCompressed` — see Revision spec §10–§11.

### 11.7 Session events

`RevisionSessionStarted|Completed|Abandoned` → fatigue/streak calculators.

### 11.8 Health / fatigue / streak

`RevisionHealthRecomputed`, `RevisionFatigueRecomputed`, `RevisionStreakRecomputed` → Twin behavioral slices (payload includes computed values; Twin persists, does not recompute in hot path).

### 11.9 `RetentionSnapshotBuilt`

Nightly pre-scheduler gate (`REVISION_ENGINE_SPECIFICATION.md` §13.5).

---

## 12. Assessment Engine events

**Spec:** `ASSESSMENT_ENGINE_SPECIFICATION.md` §19–§21

### 12.1 `AssessmentSubmitted`

Pre-score audit; optional analytics. Not consumed by LG.

### 12.2 `AssessmentCompleted`

Full payload in Assessment spec §20. **Critical path event.**

### 12.3 `AssessmentScoringFailed`

Triggers retry UI; DLQ after max retries.

### 12.4 `AnswerEvaluated`

Mains async path → LG mains mastery → Twin WritingSub.

### 12.5 `RecallSessionCompleted`

Internal; Revision validates via Assessment read port, not via this event for LG.

---

## 13. PYQ Intelligence events

**Spec:** `PYQ_INTELLIGENCE_SPECIFICATION.md` §18–§20

### 13.1 `PYQDataChanged`

Global catalog; LG copies `importance_score` to all student nodes.

### 13.2 `FacultyWeightUpdated`

Incremental importance recompute for listed concepts.

### 13.3 Internal

`PYQIngestionCompleted`, `ImportanceRecomputeCompleted`, `PYQMappingQuarantined` — admin/observability only.

---

## 14. Current Affairs Engine events

**Spec:** `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` §16–§18

### 14.1 `CurrentAffairsPublished`

Revision CA relevance refresh; Mentor/Assessment cache invalidation. Twin does **not** immediate full rebuild.

### 14.2 `CurrentAffairsEngaged`

Twin `RebuildCA`; may follow `StudySessionLogged` chain.

### 14.3 `CurrentAffairsArchived`

Feeds drop item; CA relevance decays naturally.

---

## 15. Preparation Twin events

**Spec:** `PREPARATION_TWIN_SPECIFICATION.md` §13–§15

### 15.1 `TwinUpdated`

```json
{
  "event_type": "TwinUpdated",
  "payload": {
    "twin_id": "uuid",
    "student_id": "uuid",
    "changed_sections": ["academic.knowledge", "prediction.readiness"],
    "snapshot_at": "ISO8601",
    "projection_version": "twin_v1"
  }
}
```

Mentor: replan if readiness Δ ≥ 3 (`MENTOR_REPLAN_READINESS_DELTA`).

### 15.2 `TwinProvisioned`

Onboarding empty twin created.

### 15.3–15.4 Internal

`TwinRebuildCompleted`, `TwinRebuildFailed`, `TwinDriftDetected` — ops.

### 15.5 `NightlyTwinRebuildRequested`

Scheduler command; full rebuild pipeline P5.

---

## 16. Mentor Agent events

**Spec:** `MENTOR_AGENT_SPECIFICATION.md` §25

### 16.1 `MentorPlanGenerated`

WebSocket `plan_generated`; analytics.

### 16.2 `MentorInterventionTriggered`

Notifications; faculty dashboard for escalations.

### 16.3 `MentorFacultyEscalation`

Institute risk workflows.

### 16.4 Internal

`MentorLLMValidationFailed`, `MentorPlanSuperseded` — audit/observability.

---

## 17. Domain catalog events

### 17.1 `DomainCatalogUpdated`

**Producer:** Exam Domain / syllabus admin  
**Payload:** `exam_id`, `catalog_version`, `concepts_added[]`, `concepts_deprecated[]`

**Consumers:** LG backfill, Revision cancel, PYQ/CA mapping revalidation, Twin full rebuild.

### 17.2 `ScoringFormulaVersionChanged`

**Payload:** `formula_key`, `old_version`, `new_version`, `replay_required`

Triggers LG evidence replay + Twin full replay (`PREPARATION_TWIN_SPECIFICATION.md` §16.1 P6).

---

## 18. Study session events

### 18.1 `StudySessionLogged`

**Producers:** Study module; CA Engine via bridge (`CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` §13)

```json
{
  "event_type": "StudySessionLogged",
  "payload": {
    "session_id": "uuid",
    "student_id": "uuid",
    "concept_id": "string",
    "engaged_minutes": 25,
    "activity_type": "study|ca_reading",
    "source_ref": { "type": "ca", "ca_id": "uuid-optional" }
  }
}
```

**Consumer:** Learning Graph (study channel mastery + retention touch); Twin behavioral study.

---

## 19. Celery queue routing

### 19.1 Queues (V1)

| Queue | Workers | Events / jobs |
|---|---|---|
| `default` | general | Mentor, notifications |
| `learning_graph` | graph mutations | LG handlers, importance copy |
| `revision` | revision | Scheduling, CA relevance refresh |
| `assessment` | assessment | Scoring, Mains eval |
| `twin` | twin | Rebuilds, debounced |
| `analytics` | analytics | Aggregates, non-critical |
| `pyq` | pyq | Importance batch |
| `ca` | ca | Ingestion, rollups |

### 19.2 Routing rules

```
route(event):
  IF event_type IN Assessment*: return assessment
  IF event_type IN Revision* AND NOT RevisionCompleted: return revision
  IF event_type == RevisionCompleted: return learning_graph   // sync path may bypass queue
  IF event_type == LearningGraphUpdated: return twin
  IF event_type == PYQDataChanged: return learning_graph
  ...
```

`RevisionCompleted` sync handler MAY run in API process; async fan-out still uses queues for Twin.

### 19.3 Priority

| Priority | Events |
|---|---|
| High | `RevisionCompleted`, `AssessmentCompleted` (sync path) |
| Normal | `LearningGraphUpdated`, `TwinUpdated` |
| Low | Analytics, `ImportanceRecomputeCompleted` |

---

## 20. `processed_events` stores

### 20.1 Per-consumer tables

| Table | Owner |
|---|---|
| `learning_graph_processed_events` | LG |
| `twin_processed_events` | Twin |
| `mentor_processed_events` | Mentor |
| `revision_processed_events` | Revision |
| `analytics_processed_events` | Analytics |

Columns: `event_id PK`, `event_type`, `processed_at`, `handler_version`, `duration_ms`.

### 20.2 Unified alternative

Single `domain_processed_events(event_id, consumer_name)` acceptable in monolith.

---

## 21. Dead letter and retry

### 21.1 Retry policy

| Error class | Retries | Backoff |
|---|---|---|
| Transient DB | 5 | exponential 1s–60s |
| Validation | 0 | DLQ immediately |
| Tenant mismatch | 0 | DLQ + security alert |

### 21.2 Dead letter queue

`domain_dead_letters(event_id, event_type, payload, error, failed_at, consumer)`.

Admin replay tool: re-enqueue after fix (new `event_id` OR same id if processed_events row removed in controlled replay).

### 21.3 Poison message handling

After 5 failures: stop retry; alert; leave authoritative state consistent (outbox marked failed, source transaction already committed).

---

## 22. Replay and migration

### 22.1 Evidence-based replay (preferred)

On `ScoringFormulaVersionChanged`:

```
FOR each student:
  Recompute from evidence stores (assessments, revisions, study)
  NOT naive event log replay unless handlers proven pure
```

`LEARNING_GRAPH_SPECIFICATION.md` §14.3.

### 22.2 Event log replay (debug)

Single-node replay for support; production migration uses evidence recompute.

### 22.3 Version migration

1. Deploy consumer understanding `event_version` N and N+1.
2. Producers emit new version.
3. Retire old handler after TTL.

---

## 23. WebSocket bridge events

Not domain events — **UI notifications** derived from integration events:

| WS type | Triggered by |
|---|---|
| `assessment_complete` | `AssessmentCompleted` |
| `plan_generated` | `MentorPlanGenerated` |
| `twin_updated` | `TwinUpdated` (optional) |
| `token` | Agent streaming |

Bridge service subscribes to Redis pub/sub fed by outbox publishers. **Never** source of truth.

---

## 24. Event versioning

### 24.1 Rules

1. **Additive changes** (new optional payload fields): same `event_version`.
2. **Breaking changes**: increment `event_version`; support N and N-1 for 90 days.
3. Document in engine spec + this registry appendix.

### 24.2 Schema registry (logical)

Table `event_schema_registry(event_type, event_version, json_schema, effective_from)`.

Validation at outbox insert (producer) and consumer ingress.

---

## 25. Observability

### 25.1 Required log fields

`event_id`, `event_type`, `tenant_id`, `student_id`, `correlation_id`, `producer`, `consumer`, `duration_ms`, `outcome`.

### 25.2 Metrics

| Metric | Type |
|---|---|
| `domain_events_published_total` | counter by type |
| `domain_events_processed_total` | counter by consumer,type |
| `domain_events_processing_duration_ms` | histogram |
| `domain_outbox_pending_count` | gauge |
| `domain_dead_letter_total` | counter |
| `domain_idempotency_skips_total` | counter |

### 25.3 Tracing

OpenTelemetry span links: HTTP request → outbox insert → Celery task → handler → downstream outbox.

---

## Appendix A — Full event catalog (alphabetical)

| Event | Producer | Primary consumers |
|---|---|---|
| `AnswerEvaluated` | Assessment | LG, Twin |
| `AssessmentCompleted` | Assessment | LG, Twin, Mentor |
| `AssessmentScoringFailed` | Assessment | Ops |
| `AssessmentSubmitted` | Assessment | Analytics |
| `CAMappingReviewRequired` | CA | Faculty |
| `CAIngestionCompleted` | CA | Admin |
| `CurrentAffairsArchived` | CA | Revision |
| `CurrentAffairsEngaged` | CA | Twin |
| `CurrentAffairsPublished` | CA | Revision, Mentor |
| `DiagnosticCompleted` | Assessment | LG, Twin |
| `DomainCatalogUpdated` | Exam Domain | LG, Revision, PYQ, CA, Twin |
| `FacultyWeightUpdated` | PYQ | LG, Twin |
| `GraphNodeCreated` | LG | Twin |
| `GraphNodeDeprecated` | LG | Twin, Revision |
| `ImportanceRecomputeCompleted` | PYQ | Ops |
| `LearningGraphUpdated` | LG | Twin, Mentor |
| `MentorFacultyEscalation` | Mentor | Institute |
| `MentorInterventionTriggered` | Mentor | Notifications |
| `MentorLLMValidationFailed` | Mentor | Ops |
| `MentorPlanGenerated` | Mentor | WebSocket |
| `MentorPlanSuperseded` | Mentor | Audit |
| `NightlyTwinRebuildRequested` | Scheduler | Twin |
| `PYQDataChanged` | PYQ | LG, Twin, Mentor, Assessment |
| `PYQIngestionCompleted` | PYQ | Admin |
| `PYQMappingQuarantined` | PYQ | Faculty |
| `RecallSessionCompleted` | Assessment | Internal |
| `RetentionMaterializeRequested` | Scheduler | LG |
| `RetentionSnapshotBuilt` | Revision | Revision scheduler |
| `RevisionBacklogCompressed` | Revision | Analytics |
| `RevisionBacklogIntervention` | Revision | Mentor |
| `RevisionCompleted` | Revision | LG |
| `RevisionFatigueRecomputed` | Revision | Twin |
| `RevisionHealthRecomputed` | Revision | Twin, Mentor |
| `RevisionMissed` | Revision | Twin, Analytics |
| `RevisionPlanGenerated` | Revision | Dashboard, Mentor |
| `RevisionSessionAbandoned` | Revision | Revision |
| `RevisionSessionCompleted` | Revision | Revision, Twin |
| `RevisionSessionStarted` | Revision | Revision |
| `RevisionSkipped` | Revision | Analytics |
| `RevisionStreakRecomputed` | Revision | Twin |
| `ScoringFormulaVersionChanged` | Config | LG, Twin, Revision |
| `StudentExamDateChanged` | Student | Revision, Twin |
| `StudentOnboardingCompleted` | Onboarding | Twin |
| `StudentPreferencesUpdated` | Student | Mentor |
| `StudentRegistered` | Auth | LG, Twin, Mentor, Revision |
| `StudySessionLogged` | Study/CA | LG, Twin |
| `TwinDriftDetected` | Twin | Ops |
| `TwinProvisioned` | Twin | Onboarding |
| `TwinRebuildCompleted` | Twin | Ops |
| `TwinRebuildFailed` | Twin | Ops |
| `TwinUpdated` | Twin | Mentor, Dashboard |

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `EVENT_IDEMPOTENCY_TTL_DAYS` | 90 | §4.2 |
| `OUTBOX_SWEEP_INTERVAL_SECONDS` | 60 | §3.3 |
| `OUTBOX_STALE_PENDING_SECONDS` | 300 | §3.3 |
| `OUTBOX_PUBLISHED_RETENTION_DAYS` | 7 | §3.3 |
| `EVENT_MAX_RETRIES` | 5 | §21.1 |
| `TWIN_REBUILD_DEBOUNCE_SECONDS` | 5 | §5.2 |
| `DOMAIN_EVENT_SCHEMA_VERSION` | 1 | §2 |

---

## Appendix C — Engine spec handoff

| Engine spec | Events defined in detail |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | §7, §15; consumes §9–§14 |
| `REVISION_ENGINE_SPECIFICATION.md` | §12 emit; §12.2 consume |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | §19–§21 |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | §18–§20 |
| `CURRENT_AFFAIRS_ENGINE_SPECIFICATION.md` | §16–§18 |
| `PREPARATION_TWIN_SPECIFICATION.md` | §15 consume; §13 emit |
| `MENTOR_AGENT_SPECIFICATION.md` | §25 |

---

## Appendix D — Consistency checklist

| Rule | Enforcement |
|---|---|
| Blueprint Rule 5 — engines own scores | Only LG writes `student_concept_progress` scores on domain events |
| Blueprint Rule 3 — AI not source of truth | Agent events are integration/output only |
| No cross-context DB writes | Consumer registry §7 |
| Idempotency on every consumer | §4 |
| Outbox before async publish | §3 |
| Twin avoids double rebuild | §7.1 non-consumers |
| Assessment → LG → Twin order | §8.1 |
| Revision recall validated via Assessment port | Not via duplicate events |
| All engine specs reference this doc for integration | Appendix C |

---

*End of Domain Events Specification v1.0*
