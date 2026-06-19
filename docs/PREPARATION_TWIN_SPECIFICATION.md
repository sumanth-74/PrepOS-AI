# PrepOS AI — Preparation Twin Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for student Preparation Twin architecture
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`, `REVISION_ENGINE_SPECIFICATION.md` (v1.1)
Authoring lens: Principal Architect · Learning Scientist · Staff Backend Engineer · Distributed Systems Architect · UPSC EdTech Domain Expert

> **Scope.** This document defines the **Preparation Twin**: the student's digital twin and **canonical behavioral + academic state snapshot**. It specifies aggregate structure, event-driven projection pipelines, storage, read models, integration contracts, and ownership boundaries.
>
> **Non-goals:** UI layout, marketing, sprint tasks, SQL DDL, LLM prompts, recommendation ranking logic. The Twin **does not** schedule revisions, **does not** mutate Learning Graph scores, and **does not** replace the Mentor Agent. Scoring **formulas** live in `SCORING_ENGINE_SPECIFICATION_V1_1.md`; per-concept scores live in `LEARNING_GRAPH_SPECIFICATION.md`; revision queue lives in `REVISION_ENGINE_SPECIFICATION.md`.
>
> **Core invariant:** the Preparation Twin is an **event-sourced projection**. It is the **authoritative source for student state snapshots** consumed by Mentor, Dashboard, Analytics, and Faculty — but it is **never** the authoritative source for per-concept Mastery/Retention (Learning Graph) or revision rows (Revision Engine).

---

## 0. Canonical requirements map

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and bounded context | §1 |
| 2 | Ownership boundaries | §2, §20 |
| 3 | Twin aggregate model | §3 |
| 4 | Academic profile | §4 |
| 5 | Behavioral profile | §5 |
| 6 | Revision health integration | §6 |
| 7 | Revision fatigue integration | §7 |
| 8 | Revision streak integration | §8 |
| 9 | Learning Graph integration | §9 |
| 10 | Assessment integration | §10 |
| 11 | Current Affairs integration | §11 |
| 12 | Readiness snapshot integration | §12 |
| 13 | Event-driven architecture | §13 |
| 14 | Domain events emitted | §14 |
| 15 | Domain events consumed | §15 |
| 16 | Twin projection pipelines | §16 |
| 17 | Twin recomputation rules | §17 |
| 18 | Read models | §18 |
| 19 | Storage architecture | §19 |
| 20 | Data ownership matrix | §20 |
| 21 | Failure recovery | §21 |
| 22 | Caching strategy | §22 |
| 23 | Performance requirements | §23 |
| 24 | Database schema definitions | §24 |
| 25 | API read contracts | §25 |
| 26 | Mentor integration | §26 |
| 27 | Dashboard integration | §27 |
| 28 | Explainability model | §28 |
| 29 | Future AI prediction extensions | §29 |
| 30 | Consistency checklist | Appendix D |

---

## 1. Purpose and bounded context

### 1.1 What the Preparation Twin is

The Preparation Twin is PrepOS's **consolidated, time-versioned representation of how a student is preparing** for a target government exam. It aggregates:

- **Academic state** — knowledge distribution, assessment performance, syllabus coverage, CA engagement (derived from Learning Graph + Assessment + Domain).
- **Behavioral state** — study discipline, revision compliance, fatigue, streaks (derived from Study/Revision events + Revision Engine metrics).
- **Prediction snapshot** — Readiness, gated Prelims/Mains predictions, top drivers (computed by Scoring Engine functions; **stored** on Twin).

```
Authoritative sources (never written by Twin)     Twin (this spec)              Consumers (read-only)
─────────────────────────────────────────────     ────────────────              ───────────────────
student_concept_progress (Learning Graph)    ──►  academic_profile.knowledge    Mentor (tools)
revisions / revision_sessions (Revision)     ──►  behavioral_profile.revision_* Dashboard
assessments / attempts (Assessment)          ──►  academic_profile.assessment   Analytics
current_affairs activity (CA module)         ──►  academic_profile.ca         Faculty
Scoring pure functions                       ──►  prediction_profile            Presentation Service
```

### 1.2 What the Twin is NOT

| Misconception | Reality |
|---|---|
| Dashboard | Dashboard **reads** Twin + read models; Twin has no UI |
| Recommendation engine | Mentor + Revision Engine decide actions; Twin holds state |
| Learning Graph duplicate | Twin stores **aggregates**, not per-concept score authority |
| LLM memory | Twin is deterministic JSON; LLM reads via tools |

### 1.3 Bounded context (DDD)

```
┌─────────────────────────────────────────────────────────────────┐
│              Preparation Twin Context (this spec)                │
│  preparation_twins · twin_events · twin_projection_checkpoints   │
│  TwinBuilderService · ScoringOrchestrator (pure fn invocation)   │
└───────────────┬─────────────────────────────────────────────────┘
                │ subscribes (events only)
    ┌───────────┼───────────┬──────────────┬──────────────┐
    ▼           ▼           ▼              ▼              ▼
Learning    Revision    Assessment    Current       Domain
Graph       Engine      Engine        Affairs       Catalog
Context     Context     Context       Context       Context
```

**Anti-corruption:** TwinBuilder reads upstream via **ports** (repository interfaces); never imports upstream write repositories.

### 1.4 Why it exists

UPSC preparation spans **months to years** across hundreds of concepts, daily habits, mocks, and mains answers. Point-in-time graph rows alone cannot answer:

- "Is this student exam-ready overall?" (Readiness)
- "Are they keeping up with forgetting?" (Revision Health)
- "Are they burning out?" (Revision Fatigue)
- "Which subject drags Readiness down?" (Drivers)
- "How did mock performance shift the prediction band?"

The Twin is the **moat data structure** (`02-domain-model.md` §17): competitors store progress percentages; PrepOS stores **Preparation Identity** — a reproducible, explainable snapshot rebuilt from events.

### 1.5 Success criteria

1. Same event log + config ⇒ identical Twin (deterministic replay).
2. Mentor can assemble a daily plan from Twin + tools without DB joins across 6 tables at request time.
3. Dashboard headline metrics (`readiness`, `revision_health`) served p95 < 50ms from cache/Twin row.
4. Zero Twin writes to `student_concept_progress` or `revisions`.

---

## 2. Ownership boundaries

### 2.1 Write ownership (hard rules)

| Data | Sole writer | Twin relationship |
|---|---|---|
| `student_concept_progress.*score*` | **Learning Graph Service** | Read-only input |
| `revisions`, `revision_sessions` | **Revision Engine** | Read-only input |
| `revision_health` **computation** | **Revision Engine** | Twin **persists** emitted value |
| `revision_fatigue` **computation** | **Revision Engine** | Twin **persists** emitted value |
| `revision_streak` **computation** | **Revision Engine** | Twin **persists** emitted value |
| `preparation_twins.*` | **Twin Builder Service** | **Authoritative snapshot store** |
| `twin_events` | Twin Builder (append) | Audit / replay |
| Readiness / Predictions **computation** | **Scoring pure functions** invoked by Twin Builder | Twin **persists** results |
| `mentor_plans` | Mentor module | Reads Twin; never writes Twin |
| Dashboard read models | Projection workers | Copy from Twin; not authoritative |

### 2.2 Forbidden operations

1. TwinBuilder calling `ConceptProgressRepository.save_node()`.
2. TwinBuilder `UPDATE revisions SET ...`.
3. Mentor Agent writing `preparation_twins` directly.
4. API handlers patching `prediction_profile.readiness` without event.
5. Twin storing per-concept Mastery as **authoritative** — graph remains source; Twin may cache denormalized rollups for read performance with explicit `as_of` timestamp.

### 2.3 Determinism boundary

| Computed on Twin rebuild | Computed upstream, copied to Twin |
|---|---|
| Readiness, sub-scores, drivers | Revision Health (Revision Engine event payload) |
| Predicted Prelims/Mains + bands | Revision Fatigue (Revision Engine event payload) |
| Knowledge rollups from graph read | Revision Streak (Revision Engine event payload) |
| Assessment aggregates | — |
| CA coverage aggregates | — |

---

## 3. Twin aggregate model

### 3.1 Aggregate root

**`PreparationTwin`** — one aggregate per `(tenant_id, student_id, exam_id)`.

```
PreparationTwin
├── identity
│   ├── tenant_id, student_id, exam_id
│   ├── twin_version          // optimistic lock
│   └── last_rebuilt_at
├── academic_profile          // §4 JSONB
├── behavioral_profile        // §5 JSONB
├── prediction_profile        // §12 JSONB
├── metadata
│   ├── scoring_versions      // map score → formula version
│   ├── catalog_version_bound
│   └── rebuild_causation_id  // last triggering event
└── lineage
    ├── last_event_id_processed
    └── projection_version    // e.g. twin_projection_v1
```

### 3.2 Profile separation rationale

| Profile | Question answered | Update frequency |
|---|---|---|
| **Academic** | "What does the student know and how do they perform?" | On graph/assessment/CA events |
| **Behavioral** | "How consistently do they prepare?" | On study/revision/session events |
| **Prediction** | "Where are they heading for the exam?" | Nightly + post-assessment |

Legacy blueprint "Revision Profile" is **folded into behavioral_profile.revision_*** — not a fourth top-level profile — to avoid overlapping Revision Engine ownership.

### 3.3 Aggregate lifecycle

```
                    ┌─────────────┐
StudentRegistered │  provisioned │  empty profiles; readiness=null
       ──────────►│             │
                    └──────┬──────┘
                           │ first evidence event
                           ▼
                    ┌─────────────┐
                    │   active    │  continuous event-driven updates
                    │             │
                    └──────┬──────┘
                           │ student archived / exam migrated (future)
                           ▼
                    ┌─────────────┐
                    │  archived   │  frozen snapshot; no rebuild
                    └─────────────┘
```

### 3.4 Architecture diagram

```
Domain Events (bus)
        │
        ▼
┌───────────────────┐
│ TwinEventConsumer │  idempotency (event_id)
└─────────┬─────────┘
          ▼
┌───────────────────┐
│ TwinBuilderService│
│  · route handler  │
│  · load twin      │
│  · invoke scoring │
│  · merge profiles │
└─────────┬─────────┘
          │
    read  │  write
    ▼     ▼
 Ports   preparation_twins + twin_events
(Graph,  │
Revision,│ emit TwinUpdated
Assess,  ▼
CA)   Downstream: cache invalidation,
      dashboard projection, analytics
```

---

## 4. Academic profile

Scholastic competence snapshot — **aggregates only**, never per-concept authority.

### 4.1 Schema — `academic_profile` (JSONB)

```json
{
  "knowledge": {
    "strongest_subject": { "subject_id": "upsc.cse.polity", "label": "Polity", "mastery_avg": 78.2 },
    "weakest_subject":   { "subject_id": "upsc.cse.economy", "label": "Economy", "mastery_avg": 41.5, "topic_coverage": 0.35 },
    "most_forgotten_topic": { "topic_id": "...", "label": "Monetary Policy", "retention_avg": 38.0 },
    "mastery_histogram": { "0_25": 12, "25_50": 45, "50_75": 120, "75_100": 88 },
    "retention_histogram": { "0_25": 8, "25_50": 52, "50_75": 140, "75_100": 65 },
    "subject_rollups": [
      { "subject_id": "...", "mastery_avg": 62.1, "retention_avg": 58.3, "coverage": 0.72, "importance_mass": 8420.0 }
    ],
    "topic_rollups_top_weak": [
      { "topic_id": "...", "retention_avg": 38.0, "importance_mass": 920.0 }
    ],
    "rated_concept_count": 265,
    "active_concept_count": 497,
    "high_importance_coverage": 0.68,
    "as_of": "2026-06-18T02:00:00Z"
  },
  "assessment": {
    "mcq": {
      "accuracy_30d": 0.66,
      "accuracy_90d": 0.61,
      "attempts_30d": 842,
      "negative_marking_risk": 0.18,
      "guessing_rate": 0.12,
      "avg_time_per_question_sec": 42,
      "last_attempt_at": "2026-06-17T18:30:00Z"
    },
    "mains": {
      "avg_score_10": 6.2,
      "essays_evaluated_90d": 14,
      "writing_quality_trend": "improving",
      "last_evaluated_at": "2026-06-15T10:00:00Z"
    },
    "prelims_mocks": {
      "count": 2,
      "recency_weighted_mean": 86.0,
      "last_mock_at": "2026-06-10T09:00:00Z"
    }
  },
  "current_affairs": {
    "coverage_90d": 0.55,
    "accuracy_90d": 0.62,
    "linked_concepts_engaged_30d": 18,
    "last_ca_activity_at": "2026-06-17T07:00:00Z"
  },
  "syllabus_engagement": {
    "coverage_overall": 0.53,
    "coverage_high_importance": 0.68,
    "subjects_started": 14,
    "subjects_total": 17
  }
}
```

### 4.2 Build algorithm `RebuildAcademicProfile`

```
INPUT:  tenant_id, student_id, exam_id, now
1.  rated_nodes = LearningGraphReadPort.list_rated_nodes(...)
2.  subject_rollups = RollupCalculator.subject_rollups(rated_nodes)    // LG §11.2
3.  topic_rollups   = RollupCalculator.topic_rollups(rated_nodes)
4.  strongest/weakest = argmax/argmin subject_mastery (weakest: topic_coverage > 0.2)
5.  most_forgotten = argmin topic_retention WHERE importance_mass > threshold
6.  histograms = bucket counts from rated_nodes mastery/retention
7.  mcq_stats = AssessmentReadPort.mcq_aggregate(student, 30d, 90d)
8.  mains_stats = AssessmentReadPort.mains_aggregate(student, 90d)
9.  mock_stats = AssessmentReadPort.prelims_mock_aggregate(student)
10. ca_stats = CurrentAffairsReadPort.engagement_aggregate(student, 90d)
11. coverage = graph coverage denominators (EXAM_DOMAIN §11.2)
12. MERGE into academic_profile; set as_of=now
```

### 4.3 Data sources

| Field | Source | Formula ref |
|---|---|---|
| Subject/topic rollups | `student_concept_progress` + catalog | LG §11, EXAM_DOMAIN §10.5 |
| MCQ accuracy | `assessment_attempts` | Scoring Readiness MCQSub inputs |
| Mains avg | evaluated answers | Scoring WritingSub |
| CA coverage | CA mappings + activity | Scoring CASub (V2) |
| Coverage | rated vs high-importance concepts | Scoring v1.1 §4.4 |

### 4.4 Staleness rules

| Submodule | Max stale before forced rebuild |
|---|---|
| `knowledge.*` | 24h (nightly) OR `LearningGraphUpdated` |
| `assessment.*` | `AssessmentCompleted` immediate |
| `current_affairs.*` | `CurrentAffairsEngaged` OR nightly |

---

## 5. Behavioral profile

Habit, discipline, and load — **canonical store** for revision behavioral metrics emitted by Revision Engine.

### 5.1 Schema — `behavioral_profile` (JSONB)

```json
{
  "study": {
    "consistency_score": 72.0,
    "sessions_7d": 11,
    "sessions_30d": 38,
    "avg_session_minutes": 47,
    "preferred_study_hour_local": 20,
    "streak_days": 5,
    "last_study_at": "2026-06-17T21:00:00Z"
  },
  "revision": {
    "health": {
      "value": 84.0,
      "band": "good",
      "computed_at": "2026-06-18T02:00:00Z",
      "window_days": 60,
      "version": "revision_health_v1"
    },
    "fatigue": {
      "value": 42.0,
      "band": "moderate",
      "computed_at": "2026-06-18T02:00:00Z",
      "sessions_7d": 6,
      "items_7d": 48,
      "version": "revision_fatigue_v1"
    },
    "streak": {
      "current_days": 12,
      "longest_days": 28,
      "streak_at_risk": false,
      "last_on_time_date": "2026-06-17",
      "computed_at": "2026-06-18T02:00:00Z"
    },
    "backlog_intervention_active": false,
    "overdue_count": 2,
    "completed_today": 8
  },
  "discipline_index": 78.5,
  "as_of": "2026-06-18T02:00:00Z"
}
```

### 5.2 `discipline_index` (composite behavioral headline)

Internal engine metric (faculty-visible; optional Mentor hint). **Not** a student dashboard headline (Readiness + Revision Health occupy that).

```
discipline_index = round(
  0.45 · revision_health +
  0.30 · study_consistency_score +
  0.15 · (100 − revision_fatigue) +
  0.10 · min(100, current_streak_days · 8),
  2)
```

Null-safe: redistribute weights over present components.

### 5.3 Study consistency score

```
sessions_30d target = STUDY_SESSION_TARGET_30D (default 20)
consistency_score = round(100 · min(1, sessions_30d / target), 2)
```

Enhanced with recency weighting (optional V1.1): last-7-day share ≥ 40% of last-30-day sessions adds +5 bonus (cap 100).

---

## 6. Revision health integration

### 6.1 Ownership split (Revision Engine §15.1)

| Step | Owner |
|---|---|
| Compute `revision_health` | **Revision Engine** (`RevisionHealthCalculator`) |
| Emit `RevisionHealthRecomputed` | **Revision Engine** |
| Persist to Twin | **Twin Builder** (this spec) |

Twin **never recomputes** Revision Health from raw `revisions` rows in the hot path — it **trusts the event payload** for consistency with Revision Engine. Nightly **verification job** MAY recompute and alert on drift > 0.5 pts.

### 6.2 Event handler

```
ON RevisionHealthRecomputed(payload):
  twin = load_or_create(student)
  twin.behavioral_profile.revision.health = {
    value: payload.revision_health,          // null allowed
    band: band_label(payload.revision_health, REVHEALTH_BANDS),
    computed_at: payload.computed_at,
    window_days: payload.window_days,
    window_stats: { numerator, denominator },
    version: "revision_health_v1"
  }
  recompute discipline_index
  save twin + append twin_events
  EMIT TwinUpdated { changed_sections: ["behavioral_profile.revision.health"] }
```

### 6.3 Formula reference

Scoring v1.0 §6 (unchanged v1.1). See `REVISION_ENGINE_SPECIFICATION.md` §15.2.

### 6.4 Display contract

Presentation Service maps `value: null` → display "—" (Scoring v1.1 §6.2). Band thresholds: 85/70/50 (Scoring §6.7).

---

## 7. Revision fatigue integration

### 7.1 Ownership split (Revision Engine §15.6)

| Step | Owner |
|---|---|
| Compute `revision_fatigue` | **Revision Engine** |
| Emit `RevisionFatigueRecomputed` | **Revision Engine** |
| Persist to Twin | **Twin Builder** |

### 7.2 Event handler

```
ON RevisionFatigueRecomputed(payload):
  twin.behavioral_profile.revision.fatigue = {
    value: payload.revision_fatigue,
    band: band_label(payload.revision_fatigue, FATIGUE_BANDS),  // 30/60/80
    computed_at: payload.computed_at,
    sessions_7d: payload.sessions_7d,
    items_7d: payload.items_7d,
    components: payload.components,
    version: "revision_fatigue_v1"
  }
  recompute discipline_index
  save + TwinUpdated
```

### 7.3 Mentor consumption

When `fatigue.band ∈ {high, exhausted}` (≥60), Mentor deterministic fallback reduces presented task count by 20% (Mentor spec) — Twin provides the signal; Mentor applies UX policy.

### 7.4 Formula reference

Revision Engine §15.6.1 — load-based 0–100 (higher = more fatigued).

---

## 8. Revision streak integration

### 8.1 Ownership split (Revision Engine §15.7)

| Step | Owner |
|---|---|
| Compute streak metrics | **Revision Engine** |
| Emit `RevisionStreakRecomputed` | **Revision Engine** |
| Persist to Twin | **Twin Builder** |

### 8.2 Event handler

```
ON RevisionStreakRecomputed(payload):
  twin.behavioral_profile.revision.streak = {
    current_days: payload.current_streak_days,
    longest_days: payload.longest_streak_days,
    streak_at_risk: payload.streak_at_risk,
    last_on_time_date: payload.last_on_time_date,
    computed_at: payload.computed_at
  }
  twin.behavioral_profile.study.streak_days = payload.current_streak_days  // denormalized convenience
  recompute discipline_index
  save + TwinUpdated
```

### 8.3 Rules (inherited from Revision Engine)

- On-time completions only extend streak.
- Late/missed/skipped break current streak.
- `streak_at_risk=true` when local hour ≥ 20 and no on-time completion today.

---

## 9. Learning Graph integration

### 9.1 Read contract — `LearningGraphReadPort`

```python
# TwinBuilder MAY call:
list_rated_nodes(tenant_id, student_id, filters) -> list[ConceptProgressNode]
list_subject_rollups(tenant_id, student_id) -> list[SubjectRollup]   # prefer materialized LG read model
get_coverage_stats(tenant_id, student_id, exam_id) -> CoverageStats

# TwinBuilder MUST NOT call:
save_node(...)
bulk_patch_scores(...)
```

### 9.2 Primary trigger: `LearningGraphUpdated`

```
ON LearningGraphUpdated(payload):
  IF payload.changed_scores intersects {mastery, retention, importance}:
    enqueue PartialRebuild(student, sections=[academic.knowledge, prediction])
  ELSE:
    skip (confidence-only change may affect overconfidence counts in faculty views only)
```

Partial rebuild reads graph; **does not write back**.

### 9.3 Rollup consistency

Twin subject/topic rollups MUST use **identical formulas** to Learning Graph §11 (`importance`-weighted means). Implementation SHOULD read `student_subject_rollups` / `student_topic_rollups` when `computed_at` within 1h of `now` to avoid duplicate computation.

### 9.4 Coverage and Readiness coupling

`academic_profile.syllabus_engagement.coverage_high_importance` MUST match Readiness coverage denominator (Scoring v1.1 §4.4). Single function `ComputeCoverage()` shared between Readiness rebuild and academic profile.

### 9.5 Catalog migration

On `DomainCatalogUpdated`:

```
RebuildAcademicProfile with new denominators
Reset prediction_profile coverage if concept set changed
Set metadata.catalog_version_bound = new_version
```

---

## 10. Assessment integration

### 10.1 Events consumed

| Event | Twin action |
|---|---|
| `AssessmentCompleted` (MCQ) | Rebuild `academic.assessment.mcq`; recompute Readiness + Prelims prediction |
| `AssessmentCompleted` (Mains) | Rebuild `academic.assessment.mains`; recompute WritingSub + Mains prediction |
| `AssessmentCompleted` (prelims_mock) | Rebuild `academic.assessment.prelims_mocks`; recompute Prelims prediction; may unlock display gate |
| `AnswerEvaluated` | Same as Mains path |
| `StudySessionLogged` | Rebuild `behavioral.study` (not assessment) |

### 10.2 MCQ aggregate algorithm

```
INPUT: attempts in last 30d / 90d
accuracy = recency_difficulty_weighted_correct / total   // same as Scoring MCQSub input
negative_marking_risk = f(guessing_rate, wrong_on_high_confidence)
guessing_rate = share of fast-wrong attempts (< GUessing_TIME_THRESHOLD)
```

Source tables: `assessment_attempts`, `assessment_responses` (concept-tagged).

### 10.3 Assessment → graph boundary

Twin consumes **post-graph** state. Sequence:

```
AssessmentCompleted → Learning Graph updates mastery → LearningGraphUpdated → Twin rebuild
```

Twin handler for `AssessmentCompleted` SHOULD debounce 5s and coalesce with subsequent `LearningGraphUpdated` into single rebuild.

### 10.4 Prelims mock gate inputs

Twin stores `prelims_mocks.count` for Presentation gating (Scoring v1.1 §5.1). Display state computed at read time by Presentation Service using Twin fields — not stored redundantly on Twin.

---

## 11. Current Affairs integration

### 11.1 Scope (V1 / V2)

| V1 | V2 (full CASub) |
|---|---|
| Track linked-concept engagement counts | Accuracy on CA-tagged MCQs |
| `last_ca_activity_at` | `coverage_90d`, `accuracy_90d` in CASub |

### 11.2 Events consumed

| Event | Action |
|---|---|
| `CurrentAffairsPublished` | No immediate Twin rebuild (Revision handles priority) |
| `CurrentAffairsEngaged` | Increment engagement counters; rebuild CA subsection |
| `AssessmentCompleted` with CA-tagged questions | Update CA accuracy rollups |

### 11.3 CA aggregate algorithm

```
linked_concepts_engaged_30d = COUNT DISTINCT concept_id
  FROM study_sessions UNION revision_completions
  WHERE concept has CURRENT_AFFAIRS_OF edge to CA published in last 90d

coverage_90d = |engaged high-importance CA-linked concepts| / |total CA-linked high-importance|
accuracy_90d = CA-tagged MCQ accuracy (V2)
```

### 11.4 Readiness CASub

When `CASub` absent (V1 insufficient data), Readiness redistributes weights (Scoring v1.1 §4.3). Twin stores `prediction_profile.readiness.subscores.ca: null`.

---

## 12. Readiness snapshot integration

### 12.1 Schema — `prediction_profile` (JSONB)

```json
{
  "readiness": {
    "value": 71.2,
    "band": "on_track",
    "version": "readiness_v1_1",
    "computed_at": "2026-06-18T02:00:00Z",
    "subscores": {
      "knowledge": { "value": 59.0, "weight_applied": 0.40, "label": "KnowledgeSub" },
      "retention": { "value": 58.0, "weight_applied": 0.33 },
      "mcq":       { "value": 66.0, "weight_applied": 0.27 },
      "writing":   null,
      "ca":        null
    },
    "coverage": 0.70,
    "coverage_factor": 0.85,
    "drivers": [
      { "rank": 1, "label": "Low retention in Economy", "subject_id": "upsc.cse.economy", "contribution": 8.2 },
      { "rank": 2, "label": "Thin coverage in Ethics", "subject_id": "upsc.cse.ethics", "contribution": 6.1 }
    ]
  },
  "predicted_prelims": {
    "point": 81.6,
    "interval": 5.0,
    "version": "pred_prelims_v1",
    "computed_at": "2026-06-18T02:00:00Z",
    "mock_trust": 0.5,
    "display_state": "visible",
    "gate": { "n_prelims_mocks": 2, "threshold": 1 }
  },
  "predicted_mains": {
    "point": null,
    "interval": null,
    "display_state": "hidden",
    "gate": { "n_mains_eval": 4, "threshold": 10, "quality_gate_passed": false }
  },
  "as_of": "2026-06-18T02:00:00Z"
}
```

### 12.2 Build algorithm `RebuildPredictionProfile`

```
INPUT:  twin academic inputs, graph read, assessment read, now
1.  KnowledgeSub = importance_weighted_mean(MasteryNonMCQ) over rated nodes   // v1.1 §4.2
2.  RetentionSub = importance_weighted_mean(retention) over rated nodes
3.  MCQSub, WritingSub, CASub from assessment/CA ports
4.  readiness = ReadinessEngine v1.1 formula (§4.3)
5.  drivers = Top2Drivers(readiness subscores, subject rollups)                // v1.1 R8
6.  predicted_prelims = PredPrelimsEngine(...)                                  // Scoring §8
7.  predicted_mains = PredMainsEngine(...)                                    // Scoring §9
8.  display_state flags from gating rules (v1.1 §5) — stored for audit; Presentation re-evaluates
9.  MERGE prediction_profile
```

### 12.3 Driver computation (R8)

```
FOR each subject S with rollup data:
  shortfall_j = max(0, TARGET_SUBSCORE - subscore_j) for each active Readiness component
  driver_score(S) = Σ_j weight_j · shortfall_j · importance_mass(S) / total_importance
RETURN top 2 subjects by driver_score DESC
Generate human label: "Low {dimension} in {subject_name}"
```

Twin stores drivers; Presentation Service filters raw sub-scores from student API (Scoring v1.1 §7.1).

### 12.4 Update triggers

| Trigger | Rebuild scope |
|---|---|
| `LearningGraphUpdated` | readiness + predictions |
| `AssessmentCompleted` | readiness + affected predictions |
| Nightly beat | full prediction_profile (retention decay) |
| `ScoringFormulaVersionChanged` | full replay |

---

## 13. Event-driven architecture

### 13.1 Processing pipeline

```
Event received (Kafka / in-process bus)
     │
     ▼
┌─────────────────┐
│ Idempotency     │  twin_processed_events(event_id)
└────────┬────────┘
         ▼
┌─────────────────┐
│ Route to        │  handler map §15
│ handler         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ TwinBuilder     │  load twin (row_version)
│ Service         │  read upstream ports
└────────┬────────┘  invoke scoring fns
         ▼
┌─────────────────┐
│ Persist         │  preparation_twins + twin_events
│ optimistic lock │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Publish         │  TwinUpdated → cache, dashboard, analytics
└─────────────────┘
```

### 13.2 Idempotency

```
INSERT twin_processed_events (event_id, tenant_id, student_id, processed_at)
ON CONFLICT DO NOTHING → if conflict, ACK without mutation
```

Retention: 90 days (aligns with Learning Graph §7.3).

### 13.3 Ordering

| Scope | Guarantee |
|---|---|
| Per `(tenant_id, student_id)` | **Serial processing** — partition key on consumer |
| Cross-student | Parallel |

`LearningGraphUpdated` before `TwinUpdated` downstream; Twin never races graph writer (different consumer groups).

### 13.4 Debouncing

Coalesce within 5s window per student:

```
AssessmentCompleted + LearningGraphUpdated → single RebuildPredictionProfile
```

Implemented via debounce queue keyed `{tenant}:{student}`.

---

## 14. Domain events emitted

Twin Builder is a **consumer-first** service; it emits few outbound events.

| Event | Sync/async | Payload summary | Consumers |
|---|---|---|---|
| **`TwinUpdated`** | async | `{ twin_id, student_id, changed_sections[], snapshot_at }` | Cache invalidation, Dashboard projection, Analytics |
| **`TwinProvisioned`** | sync | `{ student_id, exam_id }` | Onboarding workflows |
| **`TwinRebuildCompleted`** | async | `{ student_id, rebuild_type, duration_ms, projection_version }` | Ops metrics, replay jobs |
| **`TwinRebuildFailed`** | async | `{ student_id, error, event_id, dead_letter }` | Alerting |
| **`TwinDriftDetected`** | async | `{ metric, expected, actual, revision_health? }` | Verification job |

### 14.1 `TwinUpdated` payload

```json
{
  "event_id": "uuid",
  "tenant_id": "uuid",
  "student_id": "uuid",
  "exam_id": "upsc_cse",
  "changed_sections": ["prediction_profile.readiness", "academic_profile.knowledge"],
  "readiness_value": 71.2,
  "revision_health_value": 84.0,
  "occurred_at": "ISO8601",
  "causation_id": "upstream_event_uuid"
}
```

---

## 15. Domain events consumed

Full catalog of inbound events Twin Builder handles.

| Event | Source | Handler | Rebuild scope |
|---|---|---|---|
| `StudentRegistered` | Auth/Onboarding | ProvisionTwin | create empty twin |
| `StudentOnboardingCompleted` | Onboarding | FullRebuild | all profiles |
| `LearningGraphUpdated` | Learning Graph | PartialRebuild | academic.knowledge, prediction |
| `GraphNodeCreated` | Learning Graph | PartialRebuild | coverage denominators |
| `GraphNodeDeprecated` | Learning Graph | PartialRebuild | coverage |
| `StudySessionLogged` | Study | RebuildBehavioralStudy | behavioral.study |
| `AssessmentCompleted` | Assessment | RebuildAcademicAssessment + Prediction | academic.assessment, prediction |
| `AnswerEvaluated` | Assessment/Mains | RebuildMains + Prediction | academic.assessment.mains, prediction |
| `RevisionCompleted` | Revision → Graph | Debounced via LG event | — |
| `RevisionHealthRecomputed` | Revision Engine | ApplyRevisionHealth | behavioral.revision.health |
| `RevisionFatigueRecomputed` | Revision Engine | ApplyRevisionFatigue | behavioral.revision.fatigue |
| `RevisionStreakRecomputed` | Revision Engine | ApplyRevisionStreak | behavioral.revision.streak |
| `RevisionBacklogIntervention` | Revision Engine | SetBacklogFlag | behavioral.revision.backlog_intervention_active |
| `CurrentAffairsEngaged` | CA module | RebuildCA | academic.ca |
| `PYQDataChanged` | PYQ | PartialRebuild | prediction (importance inputs) |
| `DomainCatalogUpdated` | Domain | FullRebuild | all profiles |
| `ScoringFormulaVersionChanged` | Config | FullReplay | all profiles from checkpoint |
| `FacultyWeightUpdated` | Faculty | PartialRebuild | prediction |
| `StudentExamDateChanged` | Student profile | PartialRebuild | prediction proximity inputs |
| `NightlyTwinRebuildRequested` | Scheduler | FullRebuild | all profiles |

### 15.1 Events explicitly NOT consumed

| Event | Reason |
|---|---|
| `RevisionPlanGenerated` | Queue state; Revision Engine owns |
| `RevisionCompleted` (direct) | Graph is intermediate; avoid double rebuild |
| `MentorPlanGenerated` | Mentor output; not Twin input |

---

## 16. Twin projection pipelines

### 16.1 Pipeline types

| Pipeline | Trigger | Steps |
|---|---|---|
| **P1 — Provision** | StudentRegistered | INSERT twin defaults → TwinProvisioned |
| **P2 — Partial Academic** | LearningGraphUpdated | Read graph/rollups → RebuildAcademicKnowledge → RebuildPrediction → save |
| **P3 — Partial Behavioral** | RevisionHealth/Fatigue/Streak | Apply event payload → discipline_index → save |
| **P4 — Assessment** | AssessmentCompleted | Rebuild assessment slice → RebuildPrediction → save |
| **P5 — Full Nightly** | Cron 02:30 student TZ | P2 + P4 + P3 verify + Retention-driven prediction refresh |
| **P6 — Full Replay** | ScoringFormulaVersionChanged | Checkpoint replay from twin_events + upstream evidence |

### 16.2 Nightly orchestration

```
FOR each active student (batched 500):
  1. Wait for RetentionSnapshotBuilt (Revision) + LG retention materialize
  2. Run P5 Full Nightly
  3. Emit TwinRebuildCompleted
Checkpoint: twin_scheduler_runs.last_student_id
```

### 16.3 Partial vs full rebuild decision

```
IF event IN {DomainCatalogUpdated, ScoringFormulaVersionChanged, StudentOnboardingCompleted}:
  FullRebuild
ELIF event IN {RevisionHealthRecomputed, RevisionFatigueRecomputed, RevisionStreakRecomputed}:
  Apply* only (no graph read)
ELIF event IN {LearningGraphUpdated}:
  PartialRebuild(academic.knowledge, prediction)
ELIF event IN {AssessmentCompleted}:
  PartialRebuild(academic.assessment, prediction)
ELSE:
  route per §15 table
```

---

## 17. Twin recomputation rules

### 17.1 Determinism contract

Given:

- Snapshot of upstream evidence at time T (graph rows, assessment attempts, revision events consumed),
- `ScoringConfig` version set,
- Domain catalog version,

Twin Builder MUST produce **identical** `preparation_twins` JSON.

### 17.2 Version pins

Every profile subsection stores `version` and `computed_at`. Top-level `metadata.scoring_versions`:

```json
{
  "readiness": "readiness_v1_1",
  "pred_prelims": "pred_prelims_v1",
  "pred_mains": "pred_mains_v1",
  "revision_health": "revision_health_v1",
  "masterynonmcq": "masterynonmcq_v1"
}
```

### 17.3 Recompute matrix

| Data changed | academic | behavioral | prediction |
|---|---|---|---|
| Mastery/Retention on graph | ✓ knowledge | — | ✓ readiness |
| MCQ attempt | ✓ assessment | — | ✓ readiness, prelims |
| Mains eval | ✓ assessment | — | ✓ readiness, mains |
| Study session | — | ✓ study | — |
| Revision Health event | — | ✓ health | — |
| Revision Fatigue event | — | ✓ fatigue | — |
| Revision Streak event | — | ✓ streak | — |
| CA engagement | ✓ ca | — | ✓ readiness (if CASub active) |
| Exam date change | — | — | ✓ proximity in labels only |
| Time alone (nightly) | ✓ retention rollups | ✓ recency weights | ✓ readiness (RetentionSub decay) |

### 17.4 Optimistic concurrency

```
save(twin, expected_row_version):
  UPDATE preparation_twins SET profiles=..., row_version=row_version+1
  WHERE id=? AND row_version=expected
  IF 0 rows: raise OptimisticLockError → reload + idempotent retry
```

Max 3 retries with jitter.

### 17.5 Drift verification (nightly)

```
VerifyRevisionHealth():
  engine_value = RevisionHealthCalculator.recompute(student)   // read-only call to same pure fn
  twin_value = twin.behavioral_profile.revision.health.value
  IF abs(engine_value - twin_value) > 0.5: EMIT TwinDriftDetected
```

---

## 18. Read models

Query-optimized projections; **Twin row remains authoritative**; read models are caches.

### 18.1 `student_twin_snapshot` (1 row per student)

Denormalized flat extract for dashboard API:

| Column | Source |
|---|---|
| `readiness_value` | prediction_profile.readiness.value |
| `readiness_band` | prediction_profile.readiness.band |
| `readiness_drivers` | JSON top-2 |
| `revision_health_value` | behavioral_profile.revision.health.value |
| `revision_fatigue_value` | behavioral_profile.revision.fatigue.value |
| `current_streak_days` | behavioral_profile.revision.streak.current_days |
| `strongest_subject_id` | academic_profile.knowledge.strongest_subject |
| `weakest_subject_id` | academic_profile.knowledge.weakest_subject |
| `coverage_high_importance` | academic_profile.syllabus_engagement |
| `prelims_prediction_state` | computed gate |
| `last_twin_update_at` | last_rebuilt_at |

Refresh: on `TwinUpdated` (async worker, ≤5s lag).

### 18.2 `twin_readiness_history` (time series)

| Column | Description |
|---|---|
| `student_id`, `recorded_date` | PK |
| `readiness_value` | daily snapshot |
| `coverage` | |
| `subscores` | JSON |

Retention: 24 months online. Nightly append after P5.

### 18.3 `twin_faculty_batch_rollups` (institute)

Pre-aggregated per `(tenant, batch_id, subject_id)` for faculty heatmaps — built from Twin + batch membership; min cohort rule enforced at query time.

### 18.4 Invalidation

```
TwinUpdated → invalidate twin:snapshot:{tenant}:{student}
           → upsert student_twin_snapshot
           → enqueue DashboardSummaryJob (coordinates LG read model §12)
```

---

## 19. Storage architecture

### 19.1 Layer model

| Layer | Technology | Contents |
|---|---|---|
| **L1 — Authoritative** | PostgreSQL `preparation_twins` | Full JSONB profiles |
| **L2 — Event log** | PostgreSQL `twin_events` | Append-only audit |
| **L3 — Read models** | PostgreSQL + Redis | `student_twin_snapshot`, cache |
| **L4 — Checkpoints** | PostgreSQL | `twin_projection_checkpoints`, `twin_processed_events` |

### 19.2 JSONB vs normalized

**V1:** profiles stored as JSONB columns for velocity. **Phase 2:** optional extract hot fields (`readiness_value`, `revision_health_value`) to indexed columns for analytics — must stay in sync via projection trigger.

### 19.3 Retention

| Data | Retention |
|---|---|
| `preparation_twins` | life of student account |
| `twin_events` | **7 years** |
| `twin_readiness_history` | 24 months hot, then archive |
| `twin_processed_events` | 90 days |

---

## 20. Data ownership matrix

| Entity / Field | Writer | Readers | Notes |
|---|---|---|---|
| `preparation_twins` row | **Twin Builder** | Mentor tools, APIs, Analytics | Authoritative snapshot |
| `academic_profile.*` | Twin Builder | Mentor, Dashboard, Faculty | Derived from graph/assessment |
| `behavioral_profile.revision.health` | Twin Builder (from RE event) | Dashboard, Mentor | Computed by Revision Engine |
| `behavioral_profile.revision.fatigue` | Twin Builder (from RE event) | Mentor, Faculty | Computed by Revision Engine |
| `behavioral_profile.revision.streak` | Twin Builder (from RE event) | Dashboard | Computed by Revision Engine |
| `prediction_profile.readiness` | Twin Builder (Scoring fn) | Dashboard, Mentor | Formula v1.1 |
| `prediction_profile.predicted_*` | Twin Builder (Scoring fn) | Dashboard | Gated at presentation |
| `student_concept_progress` | Learning Graph | Twin (read port) | **Never Twin writer** |
| `revisions` | Revision Engine | Twin (read optional) | **Never Twin writer** |
| `student_twin_snapshot` | Twin projection worker | Dashboard API | Non-authoritative cache |
| `twin_events` | Twin Builder | Replay, audit | Append-only |

---

## 21. Failure recovery

### 22.1 Handler failure

| Failure | Action |
|---|---|
| Transient DB | Celery retry exponential backoff (max 5) |
| OptimisticLockError | Reload twin; idempotent retry |
| Upstream read timeout | Skip student; alert; retry next beat |
| Scoring domain error | Dead-letter; **no partial profile write** |
| Duplicate event | ACK silently |

### 22.2 Partial write prohibition

Twin update is **single transaction**: all profile sections in a rebuild commit together OR none. Exception: Revision Health/Fatigue/Streak handlers update **only** behavioral subsection in one transaction.

### 22.3 Replay procedure

```
FullReplay(student, from_event_id):
  1. Load catalog + ScoringConfig at target version
  2. Reset twin profiles to provisioned empty
  3. Replay twin_events chronological OR replay upstream learning_graph_events + assessment + revision_events
  4. Compare hash to production twin; log delta report
  5. IF approved: swap twin row
```

Prefer **upstream evidence replay** over twin_events when formulas change (Learning Graph §14.3 pattern).

### 22.4 Disaster recovery

- PostgreSQL PITR restores `preparation_twins` + `twin_events`.
- Twin can be **fully rebuilt** from upstream event logs if isolated corruption.
- Redis cache loss: cold rebuild from `student_twin_snapshot` / `preparation_twins`.

### 22.5 Recovery invariant

After failure, `preparation_twins.last_event_id_processed` MUST reflect a **consistent** subset of applied inbound events — never a half-updated prediction_profile without matching academic_profile timestamp.

---

## 22. Caching strategy

### 23.1 Redis key catalog

| Key | Value | TTL | Invalidate |
|---|---|---|---|
| `twin:snapshot:{tenant}:{student}` | serialized student_twin_snapshot | 120s | TwinUpdated |
| `twin:full:{tenant}:{student}` | full twin JSON (Mentor tools) | 60s | TwinUpdated |
| `twin:readiness:{tenant}:{student}` | readiness + drivers only | 120s | TwinUpdated prediction |
| `twin:lock:rebuild:{tenant}:{student}` | rebuild mutex | 10s lease | — |

### 23.2 Cache-aside (dashboard)

```
GET dashboard:
  v = redis.get(twin:snapshot:...)
  IF v: RETURN v
  row = db.get(student_twin_snapshot) OR extract from preparation_twins
  redis.setex(120, row)
  RETURN row
```

### 23.3 Stale-while-revalidate

During rebuild, serve previous snapshot with `stale=true` header (API metadata); trigger async refresh. Max stale age: 300s before synchronous rebuild.

### 23.4 Coherence with Learning Graph cache

Twin cache invalidation on `TwinUpdated` only — Twin does **not** invalidate `lg:*` keys.

---

## 23. Performance requirements

Targets: V1 **10,000 students** (`MASTER_IMPLEMENTATION_PLAN.md`).

### 24.1 Write path (projection)

| Operation | Target |
|---|---|
| Apply RevisionHealth/Fatigue/Streak event | p95 < **50ms** |
| Partial rebuild (graph updated, 1 student) | p95 < **300ms** |
| Full nightly rebuild (1 student) | p95 < **800ms** |
| Full tenant nightly batch | **≤30 min** (10k students) |

### 24.2 Read path

| Operation | Target |
|---|---|
| `GET /twins/me` (cached snapshot) | p95 < **40ms** |
| `GET /twins/me` (cold) | p95 < **100ms** |
| Mentor `GetPreparationTwinTool` | p95 < **80ms** |
| Dashboard aggregation | p95 < **50ms** via read model |

### 24.3 Storage estimates (10k students)

| Entity | Rows | Size |
|---|---|---|
| `preparation_twins` | 10k | ~50 KB/row JSONB → ~500 MB |
| `twin_events` | ~3/student/day | partition monthly |
| `student_twin_snapshot` | 10k | small |
| `twin_readiness_history` | 10k × 365 | ~3.6M rows/year |

### 24.4 Indexing

- PK `(tenant_id, student_id, exam_id)` on `preparation_twins`
- `(tenant_id, student_id, last_rebuilt_at DESC)`
- `(tenant_id, occurred_at)` on `twin_events`
- GIN index on `prediction_profile->'readiness'->'value'` (Phase 2 analytics)

---

## 24. Database schema definitions

### 25.1 `preparation_twins`

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | no | PK |
| `tenant_id` | UUID | no | |
| `student_id` | UUID | no | FK students |
| `exam_id` | string | no | FK exams |
| `status` | enum | no | `provisioned\|active\|archived` |
| `academic_profile` | JSONB | no | §4 schema |
| `behavioral_profile` | JSONB | no | §5 schema |
| `prediction_profile` | JSONB | no | §12 schema |
| `metadata` | JSONB | no | scoring_versions, catalog_version |
| `last_rebuilt_at` | timestamptz | no | |
| `last_event_id_processed` | UUID | yes | |
| `projection_version` | string | no | `twin_projection_v1` |
| `row_version` | int | no | optimistic lock |
| `created_at` | timestamptz | no | |
| `updated_at` | timestamptz | no | |

**Unique:** `(tenant_id, student_id, exam_id)`

### 25.2 `twin_events`

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID PK | |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `twin_id` | UUID FK | |
| `event_type` | enum | `TwinUpdated\|TwinProvisioned\|TwinRebuildCompleted\|...` |
| `event_version` | int | |
| `inbound_event_type` | string nullable | causation |
| `inbound_event_id` | UUID nullable | |
| `payload` | JSONB | |
| `profile_snapshot_hash` | string nullable | SHA256 of profiles post-write |
| `occurred_at` | timestamptz | |
| `recorded_at` | timestamptz | |

### 25.3 `twin_processed_events`

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID PK | inbound idempotency |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `processed_at` | timestamptz | |

### 25.4 `twin_projection_checkpoints`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `run_type` | enum | `nightly\|replay\|migration` |
| `tenant_id` | UUID | |
| `last_student_id` | UUID | resume cursor |
| `started_at` | timestamptz | |
| `completed_at` | timestamptz nullable | |
| `status` | enum | |

### 25.5 `student_twin_snapshot`

See §18.1 — denormalized read model.

### 25.6 ER diagram

```
students 1──1 preparation_twins
students 1──* twin_events
students 1──1 student_twin_snapshot (read model)
students 1──* twin_readiness_history

preparation_twins ──reads──► student_concept_progress (via port, not FK)
preparation_twins ──reads──► assessments, revisions (via port)
```

---

## 25. API read contracts

Logical API surface (Presentation Service may filter by role). Base path: `/api/v1/twins`.

### 26.1 `GET /api/v1/twins/me`

**Purpose:** Full Twin for authenticated student (internal fields filtered by Presentation).

```json
{
  "exam_id": "upsc_cse",
  "last_rebuilt_at": "2026-06-18T02:00:00Z",
  "academic_profile": { "...": "subset per role" },
  "behavioral_profile": { "...": "revision health/fatigue/streak for display" },
  "prediction_profile": { "...": "readiness + gated predictions" }
}
```

SLA: §23.2.

### 26.2 `GET /api/v1/twins/me/snapshot`

Lightweight dashboard extract (from `student_twin_snapshot`):

```json
{
  "readiness": { "value": 71, "band": "on_track", "drivers": [ "...top 2..." ] },
  "revision_health": { "value": 84, "band": "good" },
  "revision_streak": { "current_days": 12, "at_risk": false },
  "coverage": { "high_importance": 0.68 },
  "subjects": { "strongest": "Polity", "weakest": "Economy" },
  "predictions": {
    "prelims": { "state": "visible", "band": { "low": 78, "high": 88 } },
    "mains": { "state": "hidden", "unlock_hint": "..." }
  }
}
```

Aligns with Scoring v1.1 §7.1 dashboard shape.

### 26.3 `GET /api/v1/twins/me/readiness/history?days=90`

Returns `twin_readiness_history` series for trend charts.

### 26.4 Internal — `GET /api/v1/internal/twins/{student_id}`

Full engine profiles for Mentor tools and faculty drill-down. RBAC: `mentor_agent`, `faculty`, `admin`. Includes raw sub-scores, discipline_index, fatigue components.

### 26.5 Write endpoints

**None** for clients. Twin updates are **event-only**. Admin replay: `POST /api/v1/internal/twins/{student_id}/rebuild` → enqueues FullRebuild job (audit logged).

---

## 26. Mentor integration

### 27.1 Division of responsibility

| Concern | Twin | Mentor |
|---|---|---|
| Student state snapshot | **Authoritative** | Reads via tool |
| Daily plan tasks | — | Assembles from Twin + Revision queue + Graph tools |
| Explainability numbers | Stores drivers, rollups | Renders natural language |
| Load reduction on fatigue | Provides `fatigue.band` | Applies UX policy |

### 27.2 Tools (read-only)

| Tool | Source | Returns |
|---|---|---|
| `GetPreparationTwinTool` | `GET internal/twins/{id}` | Full profiles |
| `GetTwinSnapshotTool` | snapshot read model | Dashboard subset |
| `GetReadinessDriversTool` | prediction_profile.readiness.drivers | Top-2 only |

Mentor **must not** query `preparation_twins` via raw SQL — tool layer enforces tenant scope.

### 27.3 Deterministic fallback inputs

```
fallback_plan uses:
  twin.prediction_profile.readiness.drivers  → study focus subjects
  twin.academic_profile.knowledge.weakest_subject
  twin.behavioral_profile.revision.fatigue   → capacity modifier
  revision queue (Revision Engine)           → revision tasks
```

### 27.4 Explainability linkage

Every Mentor task `reasoning_json` cites Twin fields:

```json
{
  "task_type": "study",
  "concept_id": "...",
  "reason_codes": ["weakest_subject", "readiness_driver"],
  "twin_refs": {
    "weakest_subject_mastery": 41.5,
    "readiness_driver_rank": 1,
    "driver_label": "Low retention in Economy"
  }
}
```

---

## 27. Dashboard integration

### 28.1 Data flow

```
preparation_twins
      │ TwinUpdated
      ▼
student_twin_snapshot ──► GET /analytics/dashboard (via Presentation)
      │
      └── coordinates with student_graph_summary (LG §12) for graph counts
```

### 28.2 Field mapping

| Dashboard widget | Twin source | Presentation filter |
|---|---|---|
| Readiness dial | `prediction_profile.readiness` | Student display |
| Readiness drivers | `readiness.drivers` | Top-2 only (R8) |
| Revision Health dial | `behavioral_profile.revision.health` | Student display |
| Predicted score card | `prediction_profile.predicted_*` + gate | Band format (R2) |
| Strongest/weakest subject | `academic_profile.knowledge` | Labels only |
| Streak badge | `behavioral_profile.revision.streak` | Optional V1.1 |

### 28.3 What Dashboard does NOT read directly

- `student_concept_progress` for headline KPIs — goes through Twin snapshot for consistency.
- Raw `revisions` table for health — uses Twin (Revision Engine → event → Twin path).

Per-concept graph screen still reads Learning Graph API for Mastery/Retention (Scoring v1.1 §7.2).

---

## 28. Explainability model

### 29.1 Principles

1. **Provenance chain:** every Twin field traces to `(source_event, formula_version, computed_at)`.
2. **No black boxes:** Readiness drivers decompose to named sub-score shortfalls × subject.
3. **Role-aware exposure:** students see display projections; faculty see aggregates; internal tools see engine values.
4. **Twin does not explain in natural language** — that is Mentor/Presentation; Twin stores structured refs.

### 29.2 `explainability` block (optional metadata on twin)

```json
{
  "metadata": {
    "explainability": {
      "last_rebuild_pipeline": "P5_full_nightly",
      "inputs_hash": "sha256:...",
      "upstream_events": ["LearningGraphUpdated:uuid", "RevisionHealthRecomputed:uuid"]
    }
  }
}
```

### 29.3 Driver label generation

```
Template: "{dimension} in {subject_name}"
dimension ∈ { Low retention, Thin coverage, Weak MCQ accuracy, Weak writing, Low CA engagement }
subject_name from EXAM_DOMAIN catalog
```

Bilingual labels (future): store `label_key` + params; render locale-side.

### 29.4 Audit trail

`twin_events` + inbound `causation_id` provide end-to-end trace for dispute resolution ("why did Readiness drop 5 pts overnight?").

---

## 29. Future AI prediction extensions

V1 predictions are **deterministic linear models** (Scoring §8/§9). This section defines extension points without breaking ownership.

### 30.1 What ML may do (future)

| Capability | Boundary |
|---|---|
| Retrain Prelims/Mains coefficients | New `pred_prelims_v2`; Twin stores version; replay required |
| Personalize Readiness weights | Faculty-approved config per institute; still deterministic |
| Early-warning risk classifier | **Separate** `risk_score` in metadata; does not override Readiness |
| NLP study habit clustering | Behavioral metadata only; no graph writes |

### 30.2 What ML must never do

1. Write `student_concept_progress` or `revisions`.
2. Replace Revision Health/Fatigue computation (Revision Engine owns).
3. Be shown to students without confidence interval or sample-size disclosure.
4. Bypass prediction gating (Scoring v1.1 §5).

### 30.3 `prediction_profile.ml_extensions` (placeholder schema)

```json
{
  "ml_extensions": {
    "enabled": false,
    "model_version": null,
    "risk_flags": [],
    "shadow_predictions": { "prelims_point": null, "delta_from_deterministic": null }
  }
}
```

Shadow mode: run ML parallel to deterministic; compare offline before promotion.

### 30.4 Evaluation harness

| Metric | Gate to promote |
|---|---|
| Mock MAE vs actual Prelims | ≥ 5% better than v1 linear |
| Calibration (interval coverage) | 68% band within ±2 pts |
| Non-inferior Readiness correlation | ρ ≥ 0.85 with deterministic readiness |

---

## Appendix A — Service module layout

```
domain/twin/
  entities/           PreparationTwin, TwinEvent
  services/           TwinBuilderService, ScoringOrchestrator
  repositories/       TwinRepository, TwinEventRepository
  ports/              LearningGraphReadPort, RevisionReadPort, AssessmentReadPort
  projectors/         AcademicProjector, BehavioralProjector, PredictionProjector
  policies/           RebuildPolicy, DriftVerificationPolicy

application/twin/
  use_cases/          ProvisionTwin, RebuildTwin, ApplyRevisionMetrics
  dto/

infrastructure/twin/
  consumers/          TwinEventConsumer
  read_models/        StudentTwinSnapshotBuilder
  cache/
  workers/            nightly_rebuild, replay
```

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `TWIN_PROJECTION_VERSION` | `twin_projection_v1` | |
| `TWIN_REBUILD_DEBOUNCE_SECONDS` | 5 | §13.4 |
| `TWIN_SNAPSHOT_CACHE_TTL_SECONDS` | 120 | §22 |
| `TWIN_STALE_MAX_SECONDS` | 300 | §22.3 |
| `TWIN_DRIFT_THRESHOLD_REVISION_HEALTH` | 0.5 | §17.5 |
| `STUDY_SESSION_TARGET_30D` | 20 | §5.3 |
| `TWIN_NIGHTLY_REBUILD_HOUR_LOCAL` | 2:30 | §16.2 |
| `READINESS_FORMULA_VERSION` | `readiness_v1_1` | §12 |
| `PRELIMS_MOCK_THRESHOLD` | 1 | gating |
| `MAINS_ANSWER_THRESHOLD` | 10 | gating |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `MENTOR_AGENT_SPECIFICATION` | §27 tools, explainability refs, fatigue signal |
| Presentation / API layer | §26 contracts, §28 mapping |
| Faculty analytics | §18.3 batch rollups, discipline_index |
| ML platform (future) | §29 extension schema |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | Twin reads graph; never writes; rollups §11; readiness inputs §9; dashboard handoff §12 |
| `REVISION_ENGINE_SPECIFICATION.md` (v1.1) | Health/Fatigue/Streak via events §6–§8; never writes revisions |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Readiness v1.1 §4; prediction gating §5; presentation split §6–§7 |
| `SCORING_ENGINE_SPECIFICATION.md` | Readiness, predictions, Revision Health formulas |
| `EXAM_DOMAIN_SPECIFICATION.md` | §13 Twin dependencies; subject/topic labels |
| `MASTER_IMPLEMENTATION_PLAN.md` | S6 Twin sprint; event-driven rule; modular monolith |
| Blueprint Rule 5 | Graph owns concept scores — §2, §9 |
| Blueprint Rule 4 | Explainability — §29 |
| Architectural review (Revision v1.1) | Fatigue + streak integrated §7–§8 |

---

*End of Preparation Twin Specification v1.0. Implement `TwinBuilderService` as the sole writer of `preparation_twins`; all upstream engines emit domain events; the Twin projects state without mutating Learning Graph scores or Revision Engine scheduling.*
