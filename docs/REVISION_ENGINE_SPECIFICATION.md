# PrepOS AI — Revision Engine Specification

Version: 1.1
Status: Implementation-Ready · Canonical source of truth for revision scheduling, queue, and compliance architecture
Supersedes: Revision Engine Specification v1.0 (architectural review mandatory changes applied)
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`
Authoring lens: Principal Learning Scientist · Staff Backend Architect · Knowledge Systems Architect · UPSC EdTech Domain Expert

> **Scope.** This document defines the **Revision Engine**: how revision candidates are selected, prioritized, scheduled, completed, recovered, cached, and integrated with the Learning Graph, Preparation Twin, and Mentor Agent. It is the implementation contract for the `revisions` and `revision_sessions` tables, `student_retention_snapshots`, revision event log, queue algorithms, spaced repetition scheduling, Revision Health / Fatigue / Streak inputs, and dashboard read models.
>
> **Non-goals:** UI, marketing, sprint tasks, SQL DDL, LLM prompts, recall-question generation content. Scoring **formulas** for Weakness and Revision Health live in `SCORING_ENGINE_SPECIFICATION.md` (v1.0 §5, §6). **Revision Priority** uses the **weighted additive formula defined in this spec §5** (v1.1 supersedes the multiplicative form in Scoring v1.0 §10.4 for scheduling). Domain **taxonomy** lives in `EXAM_DOMAIN_SPECIFICATION.md`. Learning Graph **score storage** lives in `LEARNING_GRAPH_SPECIFICATION.md`.
>
> **Core invariant:** the Revision Engine **never mutates** `student_concept_progress` score columns. It reads graph state, writes `revisions` rows and revision-domain events, and emits `RevisionCompleted` (and related domain events) so the **Learning Graph Service** alone updates Mastery and Retention.

---

## 0. Canonical requirements map

This document is the authoritative answer to the 20 required areas:

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and responsibilities | §1 |
| 2 | Revision queue architecture | §3 |
| 3 | Revision candidate selection algorithms | §4 |
| 4 | Priority scoring formulas | §5 |
| 5 | Retention-driven scheduling | §6 |
| 6 | Spaced repetition model | §7 |
| 7 | Daily revision plan generation | §8 |
| 8 | Current affairs priority boosts | §9 |
| 9 | Missed revision recovery rules | §10 |
| 10 | Revision completion lifecycle | §11 |
| 11 | Event-driven updates | §12 |
| 12 | Integration with Learning Graph | §13 |
| 13 | Integration with Mentor Agent | §14 |
| 14 | Revision Health calculation | §15 |
| 15 | Dashboard read models | §16 |
| 16 | Caching strategy | §17 |
| 17 | Data ownership boundaries | §18 |
| 18 | Failure recovery | §19 |
| 19 | Performance requirements | §20 |
| 20 | Future AI-powered revision planning | §21 |

### 0.1 v1.1 change log (architectural review — mandatory)

| # | Change | Section |
|---|---|---|
| C1 | Multiplicative priority → **weighted additive** scoring | §5.1 |
| C2 | **Priority Stability Window** (3-day lock) | §5.7 |
| C3 | **`RevisionSession`** aggregate entity + lifecycle | §11.6 |
| C4 | **Backlog Compression Policy** for large missed backlogs | §10.5 |
| C5 | **Revision Fatigue Score** for Twin integration | §15.6 |
| C6 | **`ConceptRevisionHistory`** read model | §16.4 |
| C7 | **Revision Streak** metrics | §16.5 |
| C8 | **Priority Decay Factor** after repeated successful recalls | §5.8 |
| C9 | **`RetentionSnapshot`** optimization layer | §13.5 |
| C10 | Fixed CA boost → **weighted CA relevance** scoring | §9 |

**Unchanged (review-approved):** event ownership, Learning Graph read-only integration, cache strategy, outbox completion path, Revision Health formula, spacing rules, mandatory override set.

---

## 1. Purpose and responsibilities

### 1.1 What the Revision Engine is

The Revision Engine is PrepOS's **deterministic forgetting-fighting system**. It transforms per-concept knowledge state (Mastery, Retention, Importance, derived Weakness) from the Learning Graph into a **time-bounded, explainable revision queue** — then closes the loop by recording recall outcomes that flow back into the graph via domain events.

```
Learning Graph (read)          Revision Engine (this spec)          Downstream (read)
─────────────────────          ───────────────────────────          ─────────────────
mastery, retention,     ──►    candidate filter                     Mentor (plan merge)
importance, node_state         priority rank                        Twin (Revision Health)
catalog relationships          spaced schedule                      Dashboard read models
student exam_date              revisions table                      Analytics
                               revision_events (log)
                                      │
                                      ▼
                               RevisionCompleted ──► Learning Graph Service (sole score writer)
```

### 1.2 Why it exists

UPSC preparation fails when high-yield material is **understood once and forgotten**. The Revision Engine operationalizes three learning-science commitments:

1. **Forgetting is predictable** — Retention decays as a function of stability and elapsed time (Scoring v1.0 §3; Learning Graph §8.2).
2. **Spacing beats cramming** — successful recalls at increasing intervals grow stability; same-day repeats do not (Scoring v1.0 §3.11).
3. **Yield-aware prioritization** — time is finite; weighted additive priority over Importance, retention gap, weakness, exam proximity, and CA relevance ranks what matters most (§5; supersedes multiplicative Scoring v1.0 §10.4 for scheduling).

Without this engine, Retention scores are diagnostic only. With it, they drive **daily action** and measurable **Revision Health** discipline.

### 1.3 Responsibilities (in scope)

| Responsibility | Owner | Notes |
|---|---|---|
| Eligible concept filtering | Revision Engine | `node_state=rated`, active catalog, stage filters |
| Weakness computation for priority | Revision Engine | **On demand** inline (Scoring v1.1 R1); never persisted on graph |
| Revision Priority ranking | Revision Engine | Weighted additive §5.1 (`revision_priority_v1_1`) |
| Spaced repetition scheduling | Revision Engine | Min interval `0.5×S`; dedupe rules |
| Daily Top-N queue materialization | Revision Engine | Writes `revisions` rows |
| RevisionSession lifecycle | Revision Engine | §11.6 aggregate for batch recall |
| Recall completion validation | Revision Engine | Recall grade required |
| Emit `RevisionCompleted` | Revision Engine | Triggers graph update |
| Compute Revision Health | Revision Engine | Formula Scoring v1.0 §6; emit for Twin |
| Compute Revision Fatigue | Revision Engine | §15.6; emit for Twin |
| Missed/overdue detection | Revision Engine | Nightly + on-read |
| Backlog compression | Revision Engine | §10.5 when backlog exceeds threshold |
| CA relevance scoring | Revision Engine | Weighted additive component §9 |
| Hard constraint overrides | Revision Engine | High-importance + low retention |
| RetentionSnapshot refresh | Revision Engine | §13.5 nightly pre-scheduler |

### 1.4 Non-responsibilities (explicitly out of scope)

| Item | Actual owner |
|---|---|
| Mastery / Retention **score persistence** | Learning Graph Service |
| Retention stability `S` mutation on completion | Learning Graph Service (via `RevisionCompleted`) |
| Recall **question content** generation | Assessment / Knowledge modules (V1: template bank; future: AI-assisted) |
| Daily **study** task selection | Mentor Agent (reads weak frontier from Learning Graph §10) |
| LLM narration of revision tasks | Mentor Agent |
| Readiness computation | Scoring / Twin builder |
| Importance global computation | PYQ / Importance refresh job |

### 1.5 Systems that read or write

| System | Read | Write | Notes |
|---|---|---|---|
| **Revision Engine** | graph nodes, RetentionSnapshot, catalog, CA mappings, student profile | `revisions`, `revision_sessions`, `revision_events` | sole writer of revision rows |
| **Learning Graph Service** | `RevisionCompleted` | `student_concept_progress` | sole writer of concept scores |
| **Scoring Engine** | — | via Learning Graph only | pure functions invoked by graph |
| **Preparation Twin builder** | `revisions`, `RevisionHealthRecomputed`, `RevisionFatigueRecomputed`, streak metrics | `preparation_twins.behavior_profile` | persists Revision Health + Fatigue |
| **Mentor Agent** | revision queue via tools | `mentor_plans` (plan assembly) | never writes scores or revisions |
| **Dashboard Read Model Builder** | revision projections | read tables / cache | read-side only |

---

## 2. Design principles

| # | Principle | Rule |
|---|---|---|
| RE1 | **Graph read-only** | Revision Engine MUST NOT UPDATE `student_concept_progress` score columns. |
| RE2 | **Event-closed loop** | Score changes happen only when Learning Graph Service handles `RevisionCompleted`. |
| RE3 | **Deterministic scheduling** | Same graph snapshot + config + `now` ⇒ identical queue (Scoring §1.5). |
| RE4 | **Explainable priorities** | Every scheduled revision stores `priority_score` + `priority_factors` JSON for Mentor/API. |
| RE5 | **Weakness on demand** | Compute Weakness inline at scheduling time (Scoring v1.0 §5); do not read deprecated `weakness_score` column as authoritative. |
| RE6 | **Tenant isolation** | Every row, query, cache key includes `tenant_id`. |
| RE7 | **Idempotent handlers** | `event_id` deduplication on all revision event consumers. |
| RE8 | **Timezone-aware scheduling** | `scheduled_date` is a **calendar date in the student's timezone**; store UTC timestamps for audit. |
| RE9 | **Recall-gated completion** | `status=completed` requires valid `recall_grade`; prevents health/retention gaming (Scoring §3.11, §6.11). |
| RE10 | **Prerequisites do not block revision** | Forgotten prerequisites get **higher** priority, not exclusion (EXAM_DOMAIN §10.4). |
| RE11 | **Single revision writer** | Only Revision Engine mutates `revisions` lifecycle fields. |
| RE12 | **Stale-while-revalidate reads** | Dashboard reads may serve cached queue up to TTL; completion path is always consistent. |
| RE13 | **Capacity-bounded daily load** | Top-N capped by student daily revision minutes / institute policy. |
| RE14 | **Version everything** | `priority_version`, `scheduler_version` on rows match `ScoringConfig`. |
| RE15 | **Additive priority** | Weighted sum prevents multiplicative score compression (§5.1). |
| RE16 | **Priority stability** | Scheduled priorities locked 3 days unless urgent override (§5.7). |
| RE17 | **Session aggregate** | Multi-item recall flows through `RevisionSession` (§11.6). |
| RE18 | **Backlog compression** | Large missed backlogs coalesce by topic — never silent delete (§10.5). |
| RE19 | **Snapshot scheduling** | Nightly batch reads `RetentionSnapshot`, not live graph scan (§13.5). |
| RE20 | **Fatigue awareness** | Revision Fatigue Score informs Twin/Mentor load reduction (§15.6). |

---

## 3. Revision queue architecture

### 3.1 Logical model

The revision queue is not a separate persistent queue table. It is the **materialized set of `revisions` rows** for a student within a rolling planning horizon, ordered by priority and due status.

```
┌─────────────────────────────────────────────────────────────┐
│                    Revision Planning Horizon                 │
│  past overdue │ today │ upcoming (7d default lookahead)      │
└─────────────────────────────────────────────────────────────┘
         │              │                    │
         ▼              ▼                    ▼
   status=missed   status=scheduled    status=scheduled
   (recoverable)  scheduled_date=today  scheduled_date>today
```

Three logical queues (views over `revisions`):

| Queue | Filter | Purpose |
|---|---|---|
| **Overdue** | `status IN (scheduled, in_progress)` AND `scheduled_date < today` | Recovery (§10) |
| **Today** | `scheduled_date = today` AND `status IN (scheduled, in_progress)` | Primary daily workload |
| **Upcoming** | `scheduled_date > today` AND `scheduled_date ≤ today+7` | Preview / Mentor weekly plan |

### 3.2 Architecture diagram

```
                    ┌──────────────────────────┐
                    │   Nightly Scheduler Job   │
                    │  1. BuildRetentionSnapshot│
                    │  2. MaterializeDailyPlan  │
                    └─────────────┬────────────┘
                                  │
     ┌────────────────────────────┼────────────────────────────┐
     │                            ▼                            │
     │              ┌─────────────────────────┐                │
     │              │  RevisionEngineService   │                │
     │              │  · SelectCandidates      │                │
     │              │  · ComputePriorities     │                │
     │              │  · ApplyStabilityLock    │                │
     │              │  · ApplySpacingRules     │                │
     │              │  · BacklogCompression    │                │
     │              │  · MaterializeDailyPlan  │                │
     │              └─────────────┬───────────┘                │
     │                            │                            │
     │    read snapshot/graph     │ write                      │
     ▼                            ▼                            ▼
student_retention_snapshots  revisions table          revision_events
student_concept_progress     revision_sessions        concept_revision_history
     ▲                            │
     │                            │ RevisionCompleted
     │                            ▼
     │              ┌─────────────────────────┐
     └──────────────│  LearningGraphService    │
                    │  (sole score writer)     │
                    └─────────────────────────┘

On-demand path:
  POST /revision-sessions → StartRevisionSession
  POST /revisions/{id}/complete → CompleteRevisionInSession → RevisionCompleted
```

### 3.3 Service boundaries (modular monolith)

```
domain/revision/
  entities/          # RevisionItem, RevisionSession, RevisionEvent, RecallGrade
  services/          # RevisionEngineService, RevisionHealthCalculator, RevisionFatigueCalculator
  repositories/      # RevisionRepository, RevisionSessionRepository, RetentionSnapshotRepository
  policies/          # SpacingPolicy, CapacityPolicy, RecoveryPolicy, BacklogCompressionPolicy
  selectors/         # CandidateSelector, PriorityRanker

application/revision/
  use_cases/         # GenerateDailyPlan, CompleteRevision, StartRevisionSession, MarkMissedRevisions
  dto/

infrastructure/revision/
  cache/             # Redis key patterns
  read_models/       # student_revision_summary, concept_revision_history
  workers/           # nightly_scheduler, snapshot_builder, health_recomputer
  snapshots/         # student_retention_snapshots
```

Scoring pure functions (`Weakness`, `RevisionHealth`, `exam_proximity`) live in `domain/scoring/` and are **called by** Revision Engine services. **Revision Priority** is implemented in `domain/revision/policies/PriorityPolicy` per §5 — not the multiplicative Scoring v1.0 §10.4 helper.

### 3.4 Planning horizon and row lifecycle coupling

| Horizon | Default | Config key |
|---|---|---|
| Lookahead scheduling | 7 calendar days | `REVISION_LOOKAHEAD_DAYS` |
| Overdue retention in queue | 14 days (then archive to missed) | `REVISION_OVERDUE_MAX_DAYS` |
| Priority stability lock | 3 calendar days | `PRIORITY_STABILITY_DAYS` |
| Revision Health window | 60 days | `REVHEALTH_WINDOW_DAYS` |
| Health recency half-life | 30 days | `REVHEALTH_HALFLIFE_DAYS` |
| Backlog compression threshold | 30 missed+overdue items | `BACKLOG_COMPRESSION_THRESHOLD` |

---

## 4. Revision candidate selection algorithms

### 4.1 Eligibility predicate

A concept is a **revision candidate** iff all conditions hold:

```
Eligible(C, student, now):
  node = graph.get(student, C.concept_id)
  concept = catalog.get(C.concept_id)

  node.node_state == 'rated'
  AND concept.status == 'active'
  AND node.retention_last_event_at IS NOT NULL   // has been studied or revised
  AND NOT SpacingBlocked(node, now)              // §7.2
  AND NOT HasActiveRevisionToday(student, C)       // dedupe same day
  AND StageFilter(student, concept) == true      // optional §4.3
```

**Explicit exclusions:**

| Condition | Rationale |
|---|---|
| `node_state = unrated` | Never studied — Mentor handles as *new study*, not revision (Scoring §5.10) |
| `node_state = deprecated` | Frozen; excluded from plans (Learning Graph §5) |
| Retention = null on rated node | Transient; run `MaterializeRetention` on read before scheduling |
| Same concept already `scheduled`/`in_progress` for today | One active revision row per concept per day |

### 4.2 Algorithm `SelectCandidates`

```
INPUT:  tenant_id, student_id, now, exam_id
OUTPUT: candidate_concept_ids[]

1.  rated_nodes = snapshot.list_rated_nodes(tenant, student)   // §13.5 RetentionSnapshot
    OR graph.list_rated_nodes(...) if snapshot stale/missing
2.  FOR each node IN rated_nodes:
      node = ensure_retention_materialized(node, now)
3.  candidates = []
4.  FOR each node IN rated_nodes:
      IF Eligible(node, student, now):
        candidates.append(node.concept_id)
5.  RETURN candidates
```

**Complexity:** O(N) over rated nodes per student; N ≈ 200–400 typical; ≤500 worst case at V1 scale.

### 4.3 Stage filter (optional config)

When `REVISION_STAGE_FILTER_ENABLED=true`, filter by student's target stage set:

```
StageFilter(student, concept):
  IF student.target_stages includes 'prelims' AND concept.prelims_relevance > 0: RETURN true
  IF student.target_stages includes 'mains'   AND concept.mains_relevance > 0:   RETURN true
  IF student.target_stages is empty: RETURN true   // default: all stages
  RETURN false
```

Source fields: `EXAM_DOMAIN_SPECIFICATION.md` §12.1.

### 4.4 Hard constraint injection (mandatory overrides)

After ranking (§5), apply **constraint pass** before Top-N truncation:

```
MANDATORY_SET = { concept_id |
    importance_score >= HIGH_YIELD_OVERRIDE_IMPORTANCE (80)
    AND materialized_retention < HIGH_YIELD_OVERRIDE_RETENTION (60)
    AND concept_id IN candidates
}

final_queue = TopN(rankings, N)
FOR each c IN MANDATORY_SET:
  IF c NOT IN final_queue AND |final_queue| < N:
    INSERT c at front (bump lowest-priority item if full)
  ELIF c NOT IN final_queue AND |final_queue| == N:
    REPLACE lowest-priority item in final_queue with c
```

Source: `EXAM_DOMAIN_SPECIFICATION.md` §12.3 constraint #3.

### 4.5 Prerequisite tie-break (ordering only)

`PREREQUISITE` edges do **not** filter candidates (EXAM_DOMAIN §10.4). They affect **intra-day ordering** only:

```
OrderWithinDay(queue):
  FOR each pair (A, B) where B is prerequisite of A (A requires B mastered first for study,
  but both need revision):
    IF retention(A) < retention(B):  // A is forgetting faster
      A ranks before B
  Stable sort by priority_score DESC, then prerequisite depth ASC
```

Rationale: if a student forgot a foundation concept, revision should surface it — blocking would hide the problem.

---

## 5. Priority scoring formulas

### 5.1 Canonical formula — weighted additive (v1.1)

**Rationale (C1):** the legacy multiplicative form (`I·gap·W·prox`) compresses scores into a narrow 0–20 band when any factor is moderate, collapsing rank separation between urgent and non-urgent items. The additive form preserves spread while remaining explainable.

Config weights (sum = 1.0), `PRIORITY_W_*`:

| Factor | Weight | Normalized input |
|---|---|---|
| Importance | **0.30** | `imp_s = I / 100` |
| Retention gap | **0.25** | `retgap_s = (100 − R) / 100` |
| Weakness | **0.25** | `weak_s = W / 100` if W not null else **0.50** (neutral) |
| Exam proximity | **0.10** | `prox_s = exam_proximity(D_exam)` ∈ [0.3, 1.0] |
| CA relevance | **0.10** | `ca_s = CARelevanceScore / 100` ∈ [0, 1]; **0** if no linked CA |

```
priority_raw = PRIORITY_W_IMPORTANCE(0.30) · imp_s
             + PRIORITY_W_RETGAP(0.25)      · retgap_s
             + PRIORITY_W_WEAKNESS(0.25)    · weak_s
             + PRIORITY_W_PROXIMITY(0.10)   · prox_s
             + PRIORITY_W_CA(0.10)          · ca_s

priority = round(100 · clamp(priority_raw, 0, 1), 2)
priority_version = revision_priority_v1_1
```

**Exam proximity** (unchanged):

```
D_exam = days between today (student TZ) and student.target_exam_date
exam_proximity(D) = clamp(0.3 + 0.7 · (1 − D / 365), 0.3, 1.0)
```

If `target_exam_date` is null: `prox_s = 0.5` (neutral; log metric `exam_date_missing`).

**Supersedes:** Scoring v1.0 §10.4 multiplicative formula for **Revision Engine scheduling only**. Scoring doc multiplicative form remains historical reference; implementation MUST use this spec.

### 5.2 Weakness inline computation (Scoring v1.0 §5 + v1.1 R1)

At scheduling time, for each candidate concept:

```
INPUT:  m, R, error_rate, confidence  from graph/snapshot + assessment read model
OUTPUT: W (0–100) or null

lack_mastery   = (100 − m) / 100
lack_retention = (100 − R) / 100
error_norm     = clamp(error_rate, 0, 1)

weakness_unit  = 0.55·lack_mastery + 0.30·lack_retention + 0.15·error_norm
overconfident  = (confidence − m) >= 25 AND m < 70
W = round(clamp(100·weakness_unit + (10 if overconfident else 0), 0, 100), 2)
```

**Do not** read `student_concept_progress.weakness_score_cache` as authoritative (Learning Graph §4.2, Scoring v1.1 R1).

**Error rate source:** rolling 30-day MCQ wrong-rate per concept from assessment read model; default `0` if no MCQs.

### 5.3 CA relevance component (see §9)

`ca_s` is computed by `CARelevanceScore(concept_id, student, now)` — a **weighted additive input**, not a post-hoc multiplier.

### 5.4 Algorithm `ComputePriorities`

```
INPUT:  candidates[], student, now, existing_scheduled_rows[]
OUTPUT: ranked list of { concept_id, priority, priority_factors }

FOR each concept_id IN candidates:
  node = snapshot.get_node(...) OR graph.get_node(...)
  R = materialized retention at now
  I = node.importance_score
  W = ComputeWeakness(node, assessment_stats)
  prox = exam_proximity(student.exam_date)
  ca_rel = CARelevanceScore(concept_id, student, now)
  priority = RevisionPriorityAdditive(I, R, W, prox, ca_rel)     // §5.1
  priority = ApplyPriorityDecay(priority, concept_id, student)  // §5.8
  priority = ApplyPriorityStabilityLock(priority, existing_row) // §5.7
  factors = { I, R, W, prox, retgap: 100-R, ca_relevance: ca_rel, decay, locked }
  append to list

SORT list BY priority DESC, concept_id ASC
APPLY MandatoryOverridePass (§4.4)
RETURN list
```

### 5.5 Persisted explanation payload

Each `revisions` row stores:

```json
{
  "priority_factors": {
    "importance": 92.0,
    "retention": 50.0,
    "retention_gap": 50.0,
    "weakness": 63.25,
    "exam_proximity": 0.77,
    "days_to_exam": 120,
    "ca_relevance": 68.0,
    "ca_relevance_weighted_contribution": 6.8,
    "priority_decay_factor": 0.84,
    "priority_locked": true,
    "priority_locked_until": "2026-06-21",
    "override_reason": null
  },
  "priority_version": "revision_priority_v1_1",
  "scheduler_version": "scheduler_v1_1"
}
```

Mentor and APIs render explanations from this JSON — never recompute (Scoring §10.5 Rule 4).

### 5.6 Worked example

Fundamental Rights: `I=92, R=50, W=40, D_exam=120, CA_relevance=68`

```
imp_s    = 0.92
retgap_s = 0.50
weak_s   = 0.40
prox_s   = 0.7699
ca_s     = 0.68

priority_raw = 0.30·0.92 + 0.25·0.50 + 0.25·0.40 + 0.10·0.7699 + 0.10·0.68
             = 0.276 + 0.125 + 0.100 + 0.077 + 0.068 = 0.646
priority     = 64.60

After 2 successful recalls (decay §5.8): factor 0.84 → priority = 54.26
```

Low-yield fresh topic: `I=30, R=90, W=20, prox=0.77, ca=0` → `0.30·0.30 + 0.25·0.10 + 0.25·0.20 + 0.10·0.77 + 0 = 0.217` → **priority ≈ 21.7** — still rankable (not compressed to ~0.5).

### 5.7 Priority Stability Window (C2)

Prevents nightly priority recomputation from reshuffling the student's queue (**thrashing**).

```
PRIORITY_STABILITY_DAYS = 3

ApplyPriorityStabilityLock(new_priority, existing_row):
  IF existing_row IS NULL: RETURN new_priority
  IF existing_row.priority_locked_until >= today:
    IF UrgentOverride(node, new_priority): RETURN new_priority   // break lock
    ELSE: RETURN existing_row.priority_score                     // keep locked value
  ELSE:
    RETURN new_priority

On UPSERT scheduled row:
  priority_locked_until = scheduled_date + PRIORITY_STABILITY_DAYS
```

**UrgentOverride** — break lock and recompute when ANY holds:

| Condition | Rationale |
|---|---|
| Materialized `R < 40` | Forgotten band — safety override |
| Concept in `MANDATORY_SET` (§4.4) | High-yield at-risk hard constraint |
| `CARelevanceScore` increased ≥ 15 pts since lock | New CA linkage (§9.4) |
| Student `target_exam_date` changed | Proximity shift |

Locked rows still update `scheduled_date` via retention-driven scheduling (§6); only **priority_score** is stable.

### 5.8 Priority Decay Factor (C8)

Deprioritizes concepts with **sustained successful recall** so capacity shifts to weaker items — without blocking future scheduling entirely.

```
ApplyPriorityDecay(priority, concept_id, student):
  streak = ConsecutiveSuccessfulRecalls(concept_id, window=90 days)
         // good or easy grades only; breaks on forgot/hard
  decay_factor = max(PRIORITY_DECAY_FLOOR(0.60),
                     1.0 − PRIORITY_DECAY_RATE(0.08) · streak)
  RETURN round(priority · decay_factor, 2)

// streak=0 → 1.0 ; streak=3 → 0.76 ; streak=5 → 0.60 (floor)
```

Decay applies to scheduling priority **only** — does not alter Learning Graph Retention/Mastery. `priority_factors.priority_decay_factor` records the multiplier.

**Interaction with spacing:** decay does not bypass `SpacingBlocked` (§7.2) or min interval rules.

---

## 6. Retention-driven scheduling

### 6.1 Scheduling thesis

Revision timing is driven by **when Retention crosses action bands**, not fixed calendar intervals alone. The engine uses materialized Retention and stability `S` from the Learning Graph.

| Retention band | Scoring §3.7 | Scheduler action |
|---|---|---|
| 85–100 | Fresh | Do not proactively schedule unless capacity slack |
| 60–85 | Fading | Schedule within 3 days |
| 40–60 | At risk | Schedule within 1–2 days |
| 0–40 | Forgotten | Schedule today (urgent) |

### 6.2 Algorithm `ComputeDueDate`

```
INPUT:  node (with R, S, retention_last_event_at), priority, now
OUTPUT: scheduled_date (calendar date, student TZ)

t_days = days(now - retention_last_event_at)
S = node.retention_stability_s OR derived from mastery if null

// Predict days until Retention hits band thresholds (inverse of R = 100·e^(-t/S)):
days_until_60 = max(0, S · ln(100/60) - t_days)    // fading threshold
days_until_40 = max(0, S · ln(100/40) - t_days)    // at-risk threshold

IF R < 40:   due_offset = 0
ELIF R < 60: due_offset = min(1, floor(days_until_40))
ELIF R < 85: due_offset = min(3, floor(days_until_60))
ELSE:        due_offset = 7   // low urgency; may fall out of Top-N

scheduled_date = today + due_offset

// Spacing floor: cannot schedule before min interval since last successful revision
last_rev = revisions.last_completed(student, concept_id)
IF last_rev AND days(now, last_rev.completed_at) < 0.5 · S:
  scheduled_date = max(scheduled_date, last_rev.completed_date + ceil(0.5·S))

RETURN scheduled_date
```

### 6.3 Interaction with nightly job

The nightly scheduler:

1. Recomputes priorities for all candidates.
2. Assigns `scheduled_date` via `ComputeDueDate`.
3. Materializes rows for `today` through `today + REVISION_LOOKAHEAD_DAYS`.
4. Does **not** delete completed history; marks overdue (§10).

Retention decay overnight may change `R` — priorities recompute each run subject to **Priority Stability Window** (§5.7); locked rows retain score until lock expires or urgent override fires.

---

## 7. Spaced repetition model

### 7.1 Model alignment

PrepOS uses the **stability-modulated exponential retention model** (Scoring v1.0 §3.5; Learning Graph §8.2) as the production spaced repetition backbone — not a standalone SM-2 implementation. Spacing rules in the Revision Engine **respect** stability updates applied by the Learning Graph on `RevisionCompleted`.

```
Successful recall (good/easy)  →  S multiplied by EF (1.6 / 2.0)  →  longer interval
Failed recall (forgot)         →  S reset toward S_base             →  short interval
Hard recall                    →  S · 1.2                           →  moderate interval
```

The Revision Engine schedules **when** the next revision should occur; the Learning Graph records **how** stability changed.

### 7.2 Minimum inter-repetition interval

```
SpacingBlocked(node, now):
  last_success = revisions.last_successful_completion(student, concept_id)
  IF last_success IS NULL: RETURN false
  S = node.retention_stability_s
  min_interval_days = 0.5 · S
  RETURN days(now, last_success.completed_at) < min_interval_days
```

Source: `EXAM_DOMAIN_SPECIFICATION.md` §12.3 constraint #2.

Default floor: `min_interval_days ≥ 1` when `S < 2` (prevent same-hour spam).

### 7.3 Same-day stability dedupe (anti-cramming)

Per Scoring v1.0 §3.11: repeats on the same calendar day beyond the first successful recall **do not** increase stability in the Learning Graph. The Revision Engine enforces the scheduling side:

```
HasActiveRevisionToday(student, concept_id):
  EXISTS revision WHERE student_id AND concept_id
    AND scheduled_date = today
    AND status IN ('scheduled', 'in_progress', 'completed')
```

After first **successful** completion today, do not schedule another revision for same concept until tomorrow minimum.

### 7.4 Stability-aware capacity spreading

When `REVISION_SPREAD_ENABLED=true`, the scheduler distributes high-priority items across lookahead days to respect daily capacity without starving urgent (R<40) items:

```
SpreadAcrossHorizon(ranked_list, daily_capacity):
  urgent = items with R < 40 OR mandatory override
  Assign all urgent to today (up to capacity)
  remaining_capacity = daily_capacity - |urgent today|
  FOR day in today+1 .. today+lookahead:
    assign next remaining_capacity items from ranked_list to day
```

Urgent items never deferred beyond `today` by spreading.

---

## 8. Daily revision plan generation

### 8.1 Algorithm `MaterializeDailyPlan`

```
INPUT:  tenant_id, student_id, plan_date, now
OUTPUT: revisions[] rows created or updated

1.  student = profile.get(student_id)
2.  Ensure RetentionSnapshot fresh (§13.5) OR fallback live graph
3.  daily_capacity = CapacityPolicy.resolve(student)     // §8.2
4.  IF BacklogCompressionNeeded(student): ApplyBacklogCompression (§10.5)
5.  candidates = SelectCandidates(...)
6.  existing = revisions.list_scheduled_in_horizon(student)
7.  ranked = ComputePriorities(candidates, student, now, existing)
8.  SpreadAcrossHorizon(ranked, daily_capacity)            // §7.4
9.  FOR each plan_date in [today .. today+lookahead]:
      items = ranked.filter(scheduled_for=plan_date).take(daily_capacity)
      FOR each item IN items:
        UPSERT revision row:
          status = 'scheduled'
          scheduled_date = plan_date
          priority_score = item.priority
          priority_factors = item.factors
          priority_locked_until = plan_date + PRIORITY_STABILITY_DAYS
          recall_session_id = null
10. PromoteOverdueItems(student, now)                    // §10.1
11. EMIT RevisionPlanGenerated event
12. Invalidate cache keys for student
13. EMIT RevisionStreakRecomputed + RevisionFatigueRecomputeRequested (async)
```

### 8.2 Daily capacity policy

```
CapacityPolicy.resolve(student):
  base = student.settings.daily_revision_slots OR tenant.default (20)
  cap_minutes = student.settings.daily_revision_minutes OR 60
  avg_minutes_per_revision = REVISION_AVG_MINUTES (default 4)
  slot_cap = floor(cap_minutes / avg_minutes_per_revision)
  RETURN min(base, slot_cap, REVISION_MAX_DAILY_SLOTS)   // hard max 30
```

Aligns with blueprint "Top 20 Revision Items" (`02-domain-model.md` §15) while allowing institute overrides.

### 8.3 Nightly vs on-demand generation

| Trigger | When | Scope |
|---|---|---|
| **Nightly Celery beat** | 02:00 student local TZ | Full horizon materialization for all active students |
| **StudentRegistered / onboarding** | First login | Initial plan for today + lookahead |
| **LearningGraphUpdated** (debounced) | Retention crosses band | Re-evaluate single concept; may insert/update one row |
| **GET /revisions/today** (cache miss) | On read | Ensure today's rows exist; lazy generation |

Debounce `LearningGraphUpdated` scheduling triggers: max 1 replan per `(student, concept)` per hour.

### 8.4 Revision plan state machine (row-level)

```
                    ┌─────────────┐
         create     │  scheduled  │◄──── nightly materialization
        ──────────► │             │
                    └──────┬──────┘
                           │ student starts recall
                           ▼
                    ┌─────────────┐
                    │ in_progress │
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │ recall OK     │ abandon       │ date passed
           ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │  completed  │ │  scheduled  │ │   missed    │
    └─────────────┘ │  (revert)   │ └──────┬──────┘
                    └─────────────┘        │ recovery job
                                           ▼
                                    ┌─────────────┐
                                    │  scheduled  │  new row or reschedule
                                    │  (recovery) │
                                    └─────────────┘

    scheduled ──► skipped  (student explicit skip; logged; partial health credit none)
    scheduled ──► deferred (auto: capacity overflow → next day)
```

Terminal states: `completed`, `skipped` (with audit), `missed` (after overdue window without recovery).

---

## 9. Current affairs relevance scoring (C10)

Replaces the v1.0 fixed `×1.15` multiplier with a **weighted CA relevance score** (0–100) consumed as the fifth additive priority component (§5.1).

### 9.1 Algorithm `CARelevanceScore`

```
INPUT:  concept_id, student, now
OUTPUT: ca_relevance (0–100)

links = concept_relationships WHERE type=CURRENT_AFFAIRS_OF AND to=concept_id
ca_hits = []
FOR each link IN links:
  FOR each ca IN current_affairs_mappings(ca, concept_id):
    IF ca.status != 'published': CONTINUE
    IF ca.published_at < now - CA_RELEVANCE_WINDOW_DAYS(30): CONTINUE
    recency_w = 0.5 ^ (days_since(ca.published_at) / CA_RECENCY_HALFLIFE_DAYS(7))
    mapping_strength = clamp(ca.mapping_confidence, 0.3, 1.0)
    stage_fit = 1.0 IF ca.exam_stage IN student.target_stages ELSE 0.70
    edge_weight = clamp(link.relationship_weight, 0.5, 1.0)   // catalog metadata
    ca_hits.append(recency_w · mapping_strength · stage_fit · edge_weight)

IF ca_hits.empty: RETURN 0

raw = max(ca_hits)   // multi-CA: take strongest signal, do not stack
ca_relevance = round(100 · clamp(raw / CA_RELEVANCE_NORM(1.0), 0, 1), 2)
RETURN ca_relevance
```

**Design notes:**

- Recency half-life **7 days** (faster decay than Importance PYQ recency) — CA is time-sensitive.
- `mapping_confidence` from CA linking engine; low-confidence mappings contribute less.
- No CA link ⇒ `ca_s = 0`; priority contribution from CA component is zero (not a penalty).

### 9.2 Integration with additive priority

```
ca_s = CARelevanceScore / 100
weighted_contribution = PRIORITY_W_CA(0.10) · ca_s · 100   // 0–10 pts on 0–100 scale
```

Stored in `priority_factors.ca_relevance` and `ca_relevance_weighted_contribution`.

### 9.3 Mandatory override interaction

Mandatory set (§4.4) is evaluated **before** CA component matters for inclusion — a high-yield fading concept enters Top-N regardless of CA score. CA relevance breaks **priority ties** among similar-yield items.

### 9.4 Stability lock break (§5.7)

When `CARelevanceScore` increases by ≥ `CA_LOCK_BREAK_DELTA (15)` since the row was locked, `UrgentOverride` fires and priority recomputes.

### 9.5 CA archival

When CA item archived, it drops out of `ca_hits`; relevance decays naturally — no manual revision row cleanup.

---

## 10. Missed revision recovery rules

### 10.1 Overdue detection

```
PromoteOverdueItems(student, now):
  FOR each revision WHERE status IN ('scheduled', 'in_progress')
    AND scheduled_date < today:
      IF days_overdue <= REVISION_OVERDUE_MAX_DAYS (14):
        keep status = 'scheduled'   // remains in overdue queue, priority escalated
        priority_score = min(100, priority_score + OVERDUE_PRIORITY_BUMP)   // default +5 per week overdue
      ELSE:
        status = 'missed'
        EMIT RevisionMissed
```

### 10.2 Recovery scheduling

```
RecoverMissedRevisions(student, now):
  missed = revisions WHERE status='missed' AND missed_at >= now - 30 days
  FOR each m IN missed (limit RECOVERY_DAILY_CAP = 5 per day):
    IF NOT SpacingBlocked:
      CREATE new revision row:
        scheduled_date = today
        priority_score = max(m.original_priority, ComputePriorities(...).priority)
        recovery_of_revision_id = m.id
        priority_factors.recovery = true
```

Recovery items count toward daily capacity but get **front-loaded** after mandatory overrides.

### 10.3 Health impact of missed items

Missed revisions contribute **0.0 credit** to Revision Health (Scoring §6.4). Late completion within 7 days yields partial credit (0.6 / 0.3 tiers) — recovery completions use the **actual completion date**, not the original scheduled date.

### 10.4 Backlog collapse (Revision Health < 50)

When computed Revision Health drops below 50:

```
BacklogCollapsePolicy:
  RECOVERY_DAILY_CAP = 3                    // reduce load
  REVISION_MAX_DAILY_SLOTS = min(current, 15)
  EMIT RevisionBacklogIntervention event → Mentor consumes for messaging
```

Engine reduces scheduled volume; does **not** delete missed history.

### 10.5 Backlog Compression Policy (C4)

When missed + overdue backlog exceeds sustainable recovery rate, **compress** without losing audit history.

```
BacklogCompressionNeeded(student):
  backlog_count = count(revisions WHERE status IN ('missed','scheduled') AND scheduled_date < today - 1)
  RETURN backlog_count >= BACKLOG_COMPRESSION_THRESHOLD (30)

ApplyBacklogCompression(student, now):
1.  Group missed revisions by topic_id (from concept catalog)
2.  FOR each topic group:
      keep = revision with MAX(priority_score) in group
      rest = other missed rows in group
      FOR each r IN rest:
        r.status = 'compressed'
        r.compression_batch_id = new UUID
        r.compressed_into_revision_id = keep.id
        EMIT RevisionBacklogCompressed { r.id, keep.id, topic_id }
3.  Set RECOVERY_DAILY_CAP = min(current, BACKLOG_COMPRESSION_RECOVERY_CAP)  // default 3
4.  EMIT RevisionBacklogIntervention { reason: 'compression', backlog_before, backlog_after }
5.  Persist compression run in revision_compression_runs (checkpoint)
```

**Invariants:**

| Rule | Enforcement |
|---|---|
| No silent delete | Compressed rows retain `status=compressed`; full history in `revision_events` |
| Mandatory set preserved | High-yield at-risk concepts (`§4.4`) NEVER compressed away — always recover individually |
| One active recovery per topic | After compression, at most one `scheduled` recovery row per `topic_id` until cleared |
| Reversible | Faculty tool may `decompress` batch → restore `missed` status (audit logged) |

**Interaction with §10.4:** Backlog Collapse (health < 50) may **trigger** compression in addition to capacity reduction. Compression is the structural remedy for large backlogs; collapse is the behavioral trigger.

---

## 11. Revision completion lifecycle

### 11.1 Completion prerequisites

```
CompleteRevision(revision_id, recall_grade, recall_session_id):
  VALIDATE revision.status IN ('scheduled', 'in_progress')
  VALIDATE recall_grade IN ('forgot', 'hard', 'good', 'easy')
  VALIDATE recall_session_id references valid recall attempt with ≥1 graded prompt
  VALIDATE recall attempt.concept_id == revision.concept_id
```

Recall session validation prevents click-through gaming (Scoring §3.11, §6.11).

### 11.2 Completion algorithm

```
1.  revision.status = 'completed'
2.  revision.completed_at = now (UTC)
3.  revision.completed_date = today (student TZ)
4.  revision.recall_grade = recall_grade
5.  revision.recall_session_id = recall_session_id
6.  revision.lateness_class = ComputeLateness(scheduled_date, completed_date)
       // on_time | late_7d | late_gt_7d
7.  Persist revision row + append revision_events (RevisionCompletedRecorded)
8.  IF revision.revision_session_id: increment session.completed_count; check session completion (§11.6)
9.  EMIT domain event RevisionCompleted:
       { event_id, tenant_id, student_id, concept_id, revision_id,
         recall_grade, recall_session_id, occurred_at }
10. DO NOT mutate graph scores in this service
11. Invalidate revision cache for student
12. EMIT RevisionHealthRecomputeRequested (async)
13. Upsert concept_revision_history projection job (§16.4)
14. Upsert RetentionSnapshot row for concept (debounced consumer, §13.5.4)
```

### 11.3 Lateness classification

| Condition | `lateness_class` | Health credit (Scoring §6.4) |
|---|---|---|
| `completed_date ≤ scheduled_date` | `on_time` | 1.0 |
| `completed_date ≤ scheduled_date + 7 days` | `late_7d` | 0.6 |
| `completed_date > scheduled_date + 7 days` | `late_gt_7d` | 0.3 |
| Not completed by overdue max | `missed` | 0.0 |

### 11.4 Downstream: Learning Graph handling

On `RevisionCompleted`, Learning Graph Service (`LEARNING_GRAPH_SPECIFICATION.md` §7.1, §8.1–§8.2):

1. `ApplyMasteryUpdate` (revision channel, 20% weight).
2. `ApplyRetentionStateUpdate` with `recall_grade`.
3. Update `last_revision_at`, increment `n_revision`.
4. Emit `LearningGraphUpdated`.

Revision Engine **subscribes** to `LearningGraphUpdated` only for cache invalidation and optional debounced replan — never writes scores.

### 11.5 Skip and defer flows

| Action | Who initiates | Effect |
|---|---|---|
| **Skip** | Student explicit action | `status=skipped`; no `RevisionCompleted`; no health credit; audit log |
| **Defer** | Scheduler capacity | `scheduled_date += 1`; `priority_factors.deferred=true` |
| **Abandon in_progress** | Session timeout (30 min) | Revert to `scheduled`; session → `abandoned` (§11.6) |

### 11.6 RevisionSession aggregate (C3)

A **RevisionSession** groups one or more revision items into a single recall sitting — the unit of student engagement, fatigue measurement, and optional batch completion.

#### 11.6.1 Purpose

- Tie multiple `revisions` rows to one student study sitting.
- Support progressive completion (complete 5 of 20 items in one session).
- Provide session-level metrics for Revision Fatigue (§15.6).
- Replace orphan `in_progress` on individual rows with session-level state.

#### 11.6.2 State machine

```
                    ┌─────────────┐
    StartSession    │   planned   │  created; items linked; none started
   ───────────────► │             │
                    └──────┬──────┘
                           │ student opens first recall item
                           ▼
                    ┌─────────────┐
                    │   active    │  ≥1 item in_progress
                    └──────┬──────┘
                           │
           ┌───────────────┼───────────────┐
           │ all items     │ timeout /     │
           │ terminal      │ explicit exit │
           ▼               ▼               │
    ┌─────────────┐ ┌─────────────┐       │
    │  completed  │ │  abandoned  │◄──────┘
    └─────────────┘ └─────────────┘
```

| State | Meaning |
|---|---|
| `planned` | Session created (auto at day start or explicit `POST /revision-sessions`) |
| `active` | Student actively recalling |
| `completed` | All linked items terminal (`completed` or `skipped`) |
| `abandoned` | Timeout or explicit exit; in-progress items revert to `scheduled` |

#### 11.6.3 Lifecycle algorithms

**`StartRevisionSession`:**

```
INPUT:  student_id, revision_ids[] (subset of today's queue)
1.  VALIDATE all revisions belong to student AND status=scheduled
2.  CREATE revision_sessions { status=planned, session_date=today, item_count=len(ids) }
3.  FOR each revision_id: revision.revision_session_id = session.id
4.  session.status = active on first recall prompt shown
5.  RETURN session
```

**`CompleteRevisionInSession`:** delegates to §11.2 per item; when all items terminal → `session.status=completed`, `completed_at=now`.

**`AbandonRevisionSession`:** revert non-terminal items to `scheduled`; `session.status=abandoned`; emit `RevisionSessionAbandoned`.

#### 11.6.4 Table schema — `revision_sessions`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `session_date` | date | Student TZ |
| `status` | enum | `planned\|active\|completed\|abandoned` |
| `item_count` | int | Linked revisions |
| `completed_count` | int | |
| `skipped_count` | int | |
| `duration_seconds` | int nullable | |
| `started_at` | timestamptz nullable | |
| `completed_at` | timestamptz nullable | |
| `created_at` | timestamptz | |

`revisions.revision_session_id` FK nullable → `revision_sessions.id`.

#### 11.6.5 Events

| Event | When |
|---|---|
| `RevisionSessionStarted` | planned → active |
| `RevisionSessionCompleted` | all items done |
| `RevisionSessionAbandoned` | timeout or exit |

Twin and fatigue calculator consume session events.

---

## 12. Event-driven updates

### 12.1 Domain events emitted by Revision Engine

| Event | Sync/async | Consumers |
|---|---|---|
| `RevisionPlanGenerated` | async | Dashboard projection, analytics |
| `RevisionCompleted` | sync | **Learning Graph Service** (critical path) |
| `RevisionMissed` | async | Twin health, Mentor |
| `RevisionSkipped` | sync | Analytics, health recompute |
| `RevisionHealthRecomputed` | async | Twin builder |
| `RevisionBacklogIntervention` | async | Mentor |
| `RevisionBacklogCompressed` | async | Analytics, Dashboard |
| `RevisionSessionStarted` | sync | Fatigue calculator |
| `RevisionSessionCompleted` | sync | Fatigue, streak, Twin |
| `RevisionSessionAbandoned` | sync | Fatigue |
| `RevisionFatigueRecomputed` | async | Twin builder |
| `RevisionStreakRecomputed` | async | Twin builder, Dashboard |

### 12.2 Domain events consumed by Revision Engine

| Event | Action |
|---|---|
| `StudentRegistered` | Initial `MaterializeDailyPlan` |
| `LearningGraphUpdated` | Debounced replan for affected concept; cache invalidation |
| `DomainCatalogUpdated` | Cancel revisions for deprecated concepts; refresh candidate pool |
| `CurrentAffairsPublished` | Re-evaluate CA relevance for linked concepts (async) |
| `StudentExamDateChanged` | Recompute `prox_f` for all scheduled rows (async) |
| `ScoringFormulaVersionChanged` | Recompute stored priorities if `revision_priority_v1_1` version bump |

| `RetentionSnapshotBuilt` | Nightly scheduler may proceed (§13.5) |

### 12.3 Processing pipeline (completion path)

```
POST /revisions/{id}/complete
     │
     ▼
┌─────────────────┐
│ Validate recall │  recall_session, grade, tenant
└────────┬────────┘
         ▼
┌─────────────────┐
│ Update revision │  single transaction: row + revision_events
│ row             │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Publish         │  RevisionCompleted → message bus / in-process
│ RevisionCompleted│
└────────┬────────┘
         ▼
┌─────────────────┐
│ Learning Graph  │  ApplyMastery + ApplyRetention (separate transaction)
│ Service         │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Publish         │  LearningGraphUpdated → Twin, Dashboard
│ downstream      │
└─────────────────┘
```

### 12.4 Idempotency contract

```
CompleteRevision idempotency:
  IF revision.status == 'completed' AND same recall_session_id:
    RETURN success (duplicate POST)
  IF revision.status == 'completed' AND different recall_session_id:
    RETURN 409 Conflict
```

Event consumers:

1. Insert `event_id` into `processed_events` (revision namespace).
2. Duplicate `RevisionCompleted` → Learning Graph acks without double-apply (Learning Graph §7.3).

### 12.5 Ordering guarantees

| Scope | Guarantee |
|---|---|
| Per `(tenant_id, student_id, revision_id)` | Strict serial completion handling |
| Per student scheduling | Nightly job single-threaded per student (worker partition key) |
| Cross-student | Parallel |

Celery queue partition key for scheduling: `{tenant_id}:{student_id}`.

---

## 13. Integration with Learning Graph

### 13.1 Read contract

Revision Engine reads via **LearningGraphReadPort** (repository interface):

```python
# Allowed reads
get_node(tenant_id, student_id, concept_id) -> ConceptProgressNode
list_rated_nodes(tenant_id, student_id, filters) -> list[ConceptProgressNode]
materialize_retention(node, now) -> ConceptProgressNode   # delegates to graph policy
get_adjacency(exam_id, rel_type) -> AdjacencyList        # cached catalog
```

**Required fields per node:** `mastery_score`, `retention_score`, `retention_stability_s`, `retention_last_event_at`, `importance_score`, `confidence_score`, `node_state`, `subject_id`, `topic_id`, `overconfidence_flag`, `last_revision_at`.

### 13.2 Write contract (forbidden)

```python
# FORBIDDEN on LearningGraphWritePort from Revision Engine:
save_node(...)
patch_mastery(...)
patch_retention(...)
```

All score mutations flow: `RevisionCompleted` → Learning Graph Service only.

### 13.3 Retention materialization on read

Before scheduling, if `retention_score` stale (`now - updated_at > RETENTION_MATERIALIZE_INTERVAL_HOURS`):

```
node = learning_graph.materialize_retention(node, now)
```

Revision Engine MUST NOT implement its own decay formula — call graph service to preserve single formula source (Learning Graph §8.2, RE1).

### 13.4 Feedback loop diagram

```
         ┌──────────────────────────────────────────────┐
         │                                              │
         ▼                                              │
  Read scores ──► Schedule revision ──► Student recall │
         ▲                              │              │
         │                              ▼              │
         │                    RevisionCompleted         │
         │                              │              │
         │                              ▼              │
         └──────── Learning Graph updates S, m, R ─────┘
                    (mastery revision channel + retention state)
```

### 13.5 RetentionSnapshot optimization layer (C9)

Nightly scheduling for 10k students × ~500 rated nodes cannot scan live `student_concept_progress` with per-row `MaterializeRetention` on the critical path. **RetentionSnapshot** is a denormalized, scheduler-optimized read model.

#### 13.5.1 Table — `student_retention_snapshots`

| Column | Type | Description |
|---|---|---|
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `concept_id` | string | |
| `mastery_score` | decimal(5,2) | Copy at snapshot time |
| `retention_score` | decimal(5,2) | Materialized at `snapshot_at` |
| `retention_stability_s` | decimal(8,2) | |
| `retention_last_event_at` | timestamptz | |
| `importance_score` | decimal(5,2) | |
| `confidence_score` | decimal(5,2) nullable | |
| `node_state` | enum | |
| `subject_id` | string | Denormalized |
| `topic_id` | string | Denormalized |
| `snapshot_at` | timestamptz | |
| `snapshot_version` | string | e.g. `retention_snapshot_v1` |

PK: `(tenant_id, student_id, concept_id)`.

#### 13.5.2 Build algorithm `BuildRetentionSnapshot`

```
INPUT:  tenant_id, student_id, now
1.  nodes = graph.list_rated_nodes(student)
2.  FOR each node: node = graph.materialize_retention(node, now)
3.  UPSERT student_retention_snapshots (bulk, batch 500)
4.  EMIT RetentionSnapshotBuilt { student_id, node_count, snapshot_at }
```

**Schedule:** runs **before** nightly `MaterializeDailyPlan` for each student (chained Celery task or same worker pass).

#### 13.5.3 Scheduler read path

```
SelectCandidates / ComputePriorities:
  IF snapshot.snapshot_at >= start_of_today(student_tz) - SNAPSHOT_MAX_STALE_HOURS(26):
    READ student_retention_snapshots
  ELSE:
    FALLBACK graph.list_rated_nodes + materialize_retention (log stale_snapshot)
```

**Correctness:** snapshot is a **performance cache**, not a source of truth. Completion path (`RevisionCompleted`) always reads/writes live graph. Snapshot refreshes on next nightly build or on debounced `LearningGraphUpdated` for touched `(student, concept)`.

#### 13.5.4 Invalidation

```
LearningGraphUpdated(student, concept_id):
  debounced upsert single snapshot row from live graph (max 1/hour/concept)
RevisionCompleted:
  upsert affected concept snapshot row synchronously (post-graph update consumer)
```

#### 13.5.5 Performance impact

| Path | Before | After (snapshot) |
|---|---|---|
| Nightly schedule per student | O(N) graph reads + materialize | O(N) snapshot read (indexed) |
| Target p95 schedule | 500ms | **≤200ms** |

Storage: 10k × 500 ≈ **5M rows** — same order as graph; co-located indexes on `(tenant_id, student_id, node_state)`.

---

## 14. Integration with Mentor Agent

### 14.1 Division of responsibility

| Concern | Revision Engine | Mentor Agent |
|---|---|---|
| What to revise | **Ranked queue** | Reads queue; does not rerank |
| How many revisions today | **Capacity policy** | May reduce presentation, not engine cap |
| Study tasks | — | Weak frontier from Learning Graph §10 |
| Sequencing within day | Priority order + prerequisite tie-break | LLM may reorder **with audit** if within 10% priority tolerance |
| Explanation | Stores `priority_factors` | Renders human-readable strings from factors |
| Plan persistence | `revisions` table | `mentor_plans.plan_json` merges revision + study + assessment |

Blueprint resolution (`MASTER_IMPLEMENTATION_PLAN.md` U3b): Revision Engine is **fully deterministic**; the "Revision Agent" in Part 5 narrates and sequences — it does not compute priorities.

### 14.2 Mentor tools (read-only)

| Tool | Data source | Returns |
|---|---|---|
| `GetRevisionBacklogTool` | Revision Engine API / repository | `{ today[], overdue[], upcoming[], active_session?, revision_health_snapshot, revision_fatigue_snapshot, streak }` |
| `GetLearningGraphTool` | Learning Graph | Score snapshots (no revision queue) |

`GetPlanEligibleConcepts` (Learning Graph §10.2) **merges** `revision queue IDs` from Revision Service — Revision Engine is authoritative for queue membership.

### 14.3 Deterministic fallback planner

When LLM unavailable, Mentor uses:

```
fallback_plan.revisions = revisions.today.take(capacity) ORDER BY priority_score DESC
fallback_plan.study = learning_graph.GetPlanEligibleConcepts.study.take(3)
```

Same inputs → same plan (Mentor architecture Rule 7).

### 14.4 Explainability payload (internal)

Mentor task entry for a revision:

```json
{
  "task_type": "revision",
  "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
  "revision_id": "uuid",
  "display_title": "Fundamental Rights — Article 14",
  "priority_score": 64.60,
  "explainability": {
    "exam_weight": 92,
    "retention_pct": 50,
    "weakness_internal": 40,
    "days_to_exam": 120,
    "ca_relevance": 68,
    "message_key": "revision.high_yield_fading"
  }
}
```

Student-facing API MUST NOT expose raw `weakness_internal` or `priority_score` per Scoring v1.1 presentation rules — Presentation Service filters for student role.

---

## 15. Revision Health calculation

### 15.1 Ownership split

| Step | Owner |
|---|---|
| Compute `revision_health` value | **Revision Engine** (`RevisionHealthCalculator`) |
| Persist to `preparation_twins.behavior_profile` | **Twin builder** (on `RevisionHealthRecomputed`) |
| Display to student | Presentation Service (Scoring v1.1 §2.6) |

### 15.2 Formula (Scoring v1.0 §6 — unchanged in v1.1)

```
window = last REVHEALTH_WINDOW_DAYS (60) of scheduled revisions
numerator   = Σ_{r in window} recency_w(r) · credit(r)
denominator = Σ_{r in window} recency_w(r)
revision_health = round(100 · numerator / denominator, 2)   IF denominator > 0 ELSE null

recency_w(r) = 0.5 ^ (days_since(scheduled_date) / REVHEALTH_HALFLIFE_DAYS)
credit(r)    = 1.0 | 0.6 | 0.3 | 0.0  per lateness_class / §11.3
```

**Denominator rules (Scoring §6.10):**

- Revisions scheduled **today** not yet due: excluded from denominator until end of day passes incomplete.
- Brand-new student with zero scheduled history: `null` (display "—"), not 0.

### 15.3 Algorithm `RecomputeRevisionHealth`

```
INPUT:  tenant_id, student_id, now
OUTPUT: revision_health | null

1.  scheduled = revisions.list_scheduled_in_window(student, 60 days)
2.  Filter to rows where scheduled_date <= yesterday OR status IN (completed, missed, skipped)
3.  Compute numerator/denominator per §15.2
4.  EMIT RevisionHealthRecomputed { value, computed_at, window_stats }
5.  Twin builder persists to behavior_profile.revision_health
```

### 15.4 Triggers

| Trigger | Timing |
|---|---|
| `RevisionCompleted` | Async recompute |
| `RevisionMissed` (nightly batch) | Async |
| Nightly beat | Full recompute all students (recency weights drift daily) |
| `RevisionSkipped` | Async |

### 15.5 Readiness coupling

Revision Health is a **display headline** (Scoring v1.1) and behavioral signal for Mentor. It is **not** a direct input to Readiness formula (Readiness uses Retention sub-score from graph, not compliance). Behavioral correlation is intentional — disciplined revision improves Retention over time.

### 15.6 Revision Fatigue Score (C5)

Student-level score **0–100** (higher = more fatigued) measuring **cognitive load and revision intensity** — distinct from Revision Health (compliance). Consumed by Preparation Twin `behavior_profile.revision_fatigue` and Mentor load reduction.

#### 15.6.1 Formula

```
INPUT:  last 7 days of revision_sessions + revisions for student

sessions_7d        = count revision_sessions WHERE session_date in last 7 days
items_completed_7d = count revisions completed in last 7 days
avg_duration_7d    = mean(session.duration_seconds) / 60   // minutes
late_rate_7d       = late_completions / max(1, completed)
heavy_days_7d      = count days WHERE items_completed >= HEAVY_DAY_THRESHOLD(15)

load_unit = clamp(
    FATIGUE_W_SESSIONS(0.25)   · norm(sessions_7d, 0, 14) +
    FATIGUE_W_ITEMS(0.30)      · norm(items_completed_7d, 0, 80) +
    FATIGUE_W_DURATION(0.20)   · norm(avg_duration_7d, 0, 45) +
    FATIGUE_W_LATE(0.15)       · late_rate_7d +
    FATIGUE_W_HEAVY_DAYS(0.10) · norm(heavy_days_7d, 0, 5),
  0, 1)

revision_fatigue = round(100 · load_unit, 2)
```

#### 15.6.2 Interpretation

| Band | Meaning | Engine action |
|---|---|---|
| 0–30 | Fresh | Normal capacity |
| 30–60 | Moderate | Normal |
| 60–80 | High | Reduce `REVISION_MAX_DAILY_SLOTS` by 20% |
| 80–100 | Exhausted | Trigger `BacklogCollapsePolicy` caps (§10.4) + Mentor intervention |

#### 15.6.3 Ownership

| Step | Owner |
|---|---|
| Compute `revision_fatigue` | **Revision Engine** (`RevisionFatigueCalculator`) |
| Persist to Twin | **Twin builder** on `RevisionFatigueRecomputed` |
| Display | Presentation Service (faculty/Twin; optional student hint via Mentor) |

#### 15.6.4 Triggers

`RevisionSessionCompleted`, `RevisionSessionAbandoned`, nightly beat, `RevisionCompleted` (debounced 1/hour/student).

### 15.7 Revision Streak metrics (C7)

Behavioral gamification inputs for Twin and dashboard read models — **not** a scoring engine headline.

```
ComputeRevisionStreak(student, now):
  current_streak_days = consecutive calendar days (student TZ) ending yesterday
    WHERE EXISTS ≥1 revision completed on_time on that day
  longest_streak_days = max historical run from revision_events
  streak_at_risk = today has zero on_time completions AND hour >= STREAK_RISK_HOUR(20)

EMIT RevisionStreakRecomputed {
  current_streak_days, longest_streak_days, streak_at_risk, last_on_time_date
}
```

**Rules:**

- On-time only (`lateness_class=on_time`) extends streak; late completions count for Health but not streak.
- Skipped/missed days break current streak.
- Stored on `student_revision_summary` (§16.5); Twin builder copies to `behavior_profile.revision_streak`.

---

## 16. Dashboard read models

Read models are query-optimized projections for API handlers. They do not define UI.

### 16.1 Read model tables (logical)

#### `student_revision_summary` (1 row per student)

| Column | Source |
|---|---|
| `today_count` | count revisions scheduled today |
| `overdue_count` | overdue queue size |
| `completed_today_count` | completions today |
| `upcoming_7d_count` | lookahead |
| `revision_health` | from Twin behavior_profile (cached copy) |
| `last_revision_completed_at` | max(completed_at) |
| `last_plan_generated_at` | from RevisionPlanGenerated |
| `backlog_intervention_active` | bool |
| `revision_fatigue` | from Twin behavior_profile (cached) |
| `current_streak_days` | §15.7 |
| `longest_streak_days` | §15.7 |
| `streak_at_risk` | bool |
| `backlog_compressed_count` | count `status=compressed` |

#### `student_revision_daily_stats` (1 row per student per date)

| Column | Source |
|---|---|
| `scheduled_count` | |
| `completed_on_time` | |
| `completed_late` | |
| `missed_count` | |
| `avg_priority_completed` | analytics |

#### Denormalized join for concept drill-down

`revision_items_enriched` view: `revisions` JOIN `concepts` for `concept_name`, `subject_id`, `topic_id` — refreshed on write path synchronously (small row count per student per day).

### 16.2 Invalidation flow

```
RevisionCompleted | RevisionPlanGenerated | RevisionMissed | RevisionBacklogCompressed
  → invalidate Redis: rev:today:{tenant}:{student}, rev:summary:{tenant}:{student}
  → invalidate rev:snapshot:{tenant}:{student} on RevisionCompleted (single-concept upsert follows)
  → upsert student_revision_summary (async worker)
  → enqueue DashboardSummaryJob(student)   // coordinates with Learning Graph read model
```

### 16.3 API read path mapping (logical)

| API | Read model path | SLA |
|---|---|---|
| `GET /revisions/today` | Redis → `revisions` table | §20 |
| Dashboard revision widget | `student_revision_summary` | p95 < 50ms |
| Faculty cohort compliance | aggregate `student_revision_daily_stats` | async |

### 16.4 ConceptRevisionHistory read model (C6)

Per-student, per-concept **append-oriented history** for drill-down, Mentor context, and analytics — not authoritative for scheduling (source: `revisions` + `revision_events`).

#### Table — `concept_revision_history`

| Column | Type | Description |
|---|---|---|
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `concept_id` | string | |
| `revision_id` | UUID | FK revisions |
| `scheduled_date` | date | |
| `completed_date` | date nullable | |
| `status` | enum | Terminal status incl. `compressed` |
| `recall_grade` | enum nullable | |
| `priority_score_at_schedule` | decimal(5,2) | |
| `retention_at_schedule` | decimal(5,2) nullable | From snapshot or graph |
| `lateness_class` | enum nullable | |
| `revision_session_id` | UUID nullable | |
| `recorded_at` | timestamptz | |

**Retention:** rolling **24 months** online; archive to cold storage beyond.

#### Refresh

```
ON RevisionCompleted | RevisionMissed | RevisionSkipped | status→compressed:
  UPSERT concept_revision_history row (async projection worker, idempotent on revision_id)
```

#### Query patterns

| Query | Index |
|---|---|
| Last 10 revisions for concept | `(tenant, student, concept, completed_date DESC)` |
| Success rate by concept | aggregate on `recall_grade` |
| Average inter-revision interval | window on `completed_date` |

### 16.5 Revision Streak storage (C7)

Streak fields live on `student_revision_summary` (§16.1) and are recomputed by `ComputeRevisionStreak` (§15.7):

| Column | Description |
|---|---|
| `current_streak_days` | int |
| `longest_streak_days` | int |
| `streak_at_risk` | bool |
| `last_on_time_revision_date` | date nullable |

Invalidation: any `RevisionCompleted` with `lateness_class=on_time`; nightly beat for `streak_at_risk`.

---

## 17. Caching strategy

### 17.1 Cache layers

| Layer | Technology | Contents |
|---|---|---|
| **L1 — Request** | in-process LRU | today's queue (single request) |
| **L2 — Redis** | ElastiCache | today/overdue/summary |
| **L3 — PostgreSQL** | RDS | authoritative `revisions` |
| **L4 — Event log** | PostgreSQL | `revision_events` |

### 17.2 Redis key catalog

| Key pattern | Value | TTL | Invalidate |
|---|---|---|---|
| `rev:today:{tenant}:{student}` | serialized today queue | 120s | any revision write for student |
| `rev:overdue:{tenant}:{student}` | overdue list | 120s | same |
| `rev:summary:{tenant}:{student}` | summary counts + health | 300s | completion, nightly plan |
| `rev:lock:plan:{tenant}:{student}` | scheduler lock | 30s lease | — |
| `rev:snapshot:{tenant}:{student}` | snapshot metadata | 3600s | RetentionSnapshotBuilt |
| `rev:session:active:{tenant}:{student}` | active session | 1800s | session terminal |

### 17.3 Cache-aside pattern

```
get_today_queue(student):
  v = redis.get(rev:today:...)
  IF v: RETURN v
  rows = db.query(revisions WHERE scheduled_date=today)
  IF empty AND should_lazy_generate: MaterializeDailyPlan(...)
  redis.setex(key, 120, rows)
  RETURN rows
```

### 17.4 Coherence with Learning Graph cache

On `LearningGraphUpdated` for a concept in today's queue:

1. Invalidate `rev:today:*` (priority factors may be stale).
2. Do **not** invalidate `lg:node:*` from Revision Engine (graph owns that key).

### 17.5 Stampede protection

Scheduler lock `rev:lock:plan:{tenant}:{student}` prevents concurrent nightly + lazy generation. Readers serve stale cache during replan (stale-while-revalidate).

---

## 18. Data ownership boundaries

### 18.1 Write ownership matrix

| Data | Sole writer | Readers |
|---|---|---|
| `revisions.*` | **Revision Engine** | Mentor, Twin, Dashboard, Analytics |
| `revision_sessions.*` | **Revision Engine** | Twin, Fatigue calculator |
| `revision_events` | Revision Engine (append) | audit, replay |
| `student_retention_snapshots` | Revision snapshot builder | Revision scheduler |
| `concept_revision_history` | Revision projection worker | Mentor, APIs, Analytics |
| `student_revision_summary` | Revision projection worker | Dashboard APIs |
| `student_concept_progress.*score*` | **Learning Graph Service** | Revision Engine (read-only) |
| `preparation_twins.behavior_profile.revision_health` | **Twin builder** | Dashboard, Mentor |
| `preparation_twins.behavior_profile.revision_fatigue` | **Twin builder** | Mentor, faculty |
| `preparation_twins.behavior_profile.revision_streak` | **Twin builder** | Dashboard, Mentor |
| Weakness | **nobody persists** | computed inline in Revision Engine |
| Revision Priority on row | Revision Engine | Mentor explainability |

### 18.2 Forbidden operations

1. Revision Engine updating `mastery_score`, `retention_score`, or `retention_stability_s` directly.
2. Mentor Agent inserting or completing `revisions` rows without going through Revision API.
3. Assessment module emitting `RevisionCompleted` without recall validation.
4. Twin builder mutating `revisions` table.
5. API routes patching `priority_score` manually.

### 18.3 Repository contract

```python
# RevisionRepository — ONLY called from RevisionEngineService
get_revision(tenant_id, revision_id) -> RevisionItem
list_queue(tenant_id, student_id, queue_type, date) -> list[RevisionItem]
upsert_scheduled(item) -> RevisionItem
complete_revision(item, recall_grade, session_id) -> RevisionItem  # emits event after commit

# FORBIDDEN:
# complete_without_event(), patch_graph_scores()
```

### 18.4 Audit

Every completion and skip writes to `revision_events`:

```
{ tenant_id, student_id, revision_id, concept_id, event_type,
  recall_grade, priority_snapshot, occurred_at, causation_id }
```

---

## 19. Failure recovery

### 19.1 Completion / graph split transaction

`RevisionCompleted` crosses service boundaries. Pattern: **outbox**:

```
BEGIN
  UPDATE revisions SET status=completed ...
  INSERT revision_events ...
  INSERT outbox_events (RevisionCompleted payload)
COMMIT

async dispatcher → Learning Graph Service
  ON success: mark outbox delivered
  ON failure: retry with exponential backoff; revision stays completed (student saw success)
```

Learning Graph retries must be idempotent (`event_id`). Graph lag is acceptable ≤30s; retention display refreshes on next read.

### 19.2 Scheduler failure

| Failure | Action |
|---|---|
| Worker crash mid-student | Checkpoint `revision_scheduler_runs.last_student_id`; resume |
| Duplicate nightly run | Upsert idempotent on `(student, concept, scheduled_date)` unique constraint |
| Graph read timeout | Skip student; alert; retry next beat |

### 19.3 Orphan in_progress

Revisions `in_progress` > 30 minutes without completion → revert to `scheduled` via sweeper job. If linked to `revision_session`, abandon session per §11.6 (`RevisionSessionAbandoned`).

### 19.4 Recovery invariant

After any failure, `revisions` rows MUST NOT show `completed` without a corresponding `revision_events` completion record and outbox `RevisionCompleted` (eventually delivered).

### 19.5 Disaster recovery

- PostgreSQL PITR restores `revisions` + `revision_events`.
- Replay `RevisionCompleted` events to Learning Graph if graph progress table restored from older backup.
- Redis loss: cold rebuild from PostgreSQL.

---

## 20. Performance requirements

Targets align with `MASTER_IMPLEMENTATION_PLAN.md` V1 (10,000 students) and Learning Graph §16.

### 20.1 Write path

| Operation | Target | Notes |
|---|---|---|
| `CompleteRevision` (API) | p95 < **200ms** | revision row + outbox; excludes graph async |
| End-to-end graph update | p95 < **350ms** | includes Learning Graph Apply* |
| Nightly schedule (per student) | p95 < **200ms** | RetentionSnapshot read + additive priority |
| BuildRetentionSnapshot (per student) | p95 < **150ms** | bulk upsert 500 nodes |
| Full tenant nightly batch (10k students) | **≤35 min** | snapshot + plan chained |
| Revision Health recompute | p95 < **100ms** | single student |

### 20.2 Read path

| Operation | Target |
|---|---|
| `GET /revisions/today` (cached) | p95 < **40ms** |
| `GET /revisions/today` (cold) | p95 < **120ms** |
| Overdue + upcoming bundle | p95 < **80ms** |
| `student_revision_summary` | p95 < **50ms** |

### 20.3 Storage estimates (10k students)

| Entity | Rows | Approx size |
|---|---|---|
| `revisions` | ~25 active rows/student + ~200 history/year | ~2.5M active + growth |
| `revision_sessions` | ~1–3/student/day | small |
| `student_retention_snapshots` | ~500/student | ~5M rows at 10k students |
| `concept_revision_history` | ~200/student/year | partition by month |
| `revision_events` | ~1.5 events/student/day | partition by month |
| `student_revision_summary` | 10k | small |

Retention policy: `revision_events` **7 years**; `revisions` completed rows archive to `revisions_archive` after 2 years (optional Phase 2).

### 20.4 Indexing (logical)

- UNIQUE `(tenant_id, student_id, concept_id, scheduled_date)` WHERE status IN ('scheduled','in_progress') — prevents duplicate day rows
- `(tenant_id, student_id, scheduled_date, status)` for today queue
- `(tenant_id, student_id, status, scheduled_date)` for overdue scan
- `(tenant_id, student_id, completed_at DESC)` for health window

### 20.5 Scaling (Phase 2+, 100k students)

- Partition `revisions`, `student_retention_snapshots`, `concept_revision_history` by `tenant_id` or hash `student_id`
- Dedicated Celery queues: `revision.snapshot` → `revision.schedule` (chain per student)
- RetentionSnapshot is **required** at scale — live graph scan forbidden on nightly path
- Priority computation MAY batch in SQL over snapshot table iff output matches `ComputePriorities` golden tests

---

## 21. Future AI-powered revision planning

V1 is **fully deterministic**. This section defines extension points without changing ownership boundaries.

### 21.1 What AI may do (future)

| Capability | Boundary |
|---|---|
| Generate recall question **wording** | Assessment/Knowledge module; graded outcome still `recall_grade` |
| Personalize **capacity** (not priority formula) | Student model suggests 15 vs 20 slots; Revision Engine applies |
| Narrate **why revise now** | Mentor LLM; factors from `priority_factors` JSON only |
| Predict **session duration** | UX hint only; does not affect scheduling |
| Cluster **session grouping** | Mentor orders adjacent concepts (same topic) within 10% priority band |

### 21.2 What AI must never do

1. Override `priority_raw` formula output without human faculty approval audit trail.
2. Write graph scores or skip recall validation.
3. Become source of truth for queue membership — deterministic engine remains authoritative.
4. Hide mandatory override concepts from queue.

### 21.3 `revision_planner_version` extensibility

```
revision_planner_version ∈ { deterministic_v1, ai_assisted_v2 }
```

`ai_assisted_v2` may reorder within-day sequence using LLM proposal **iff** `ValidateReorder(proposal)` passes:

```
- Same multiset of concept_ids as deterministic_v1
- No item dropped that was in mandatory override set
- Max Kendall tau distance ≤ REORDER_TOLERANCE
```

### 21.4 Evaluation harness (future)

Offline metrics before enabling AI assist:

| Metric | Target |
|---|---|
| Recall success rate vs deterministic | ≥ baseline |
| Revision Health trend | non-inferior |
| High-yield coverage in completed set | 100% mandatory set compliance |
| Student session time | ≤110% of deterministic plan |

---

## 22. Database representation

### 22.1 Core entities (logical ER)

```
students ──< revisions >── concepts
         ──< revision_sessions
         ──< revision_events
         ──< student_retention_snapshots
         ──< concept_revision_history  (read model)
         ──< student_revision_summary   (read model)
         ──< student_revision_daily_stats (read model)
         ──< revision_compression_runs

student_concept_progress (read-only FK concept_id; live path on completion)
preparation_twins.behavior_profile (revision_health, revision_fatigue, revision_streak — Twin writer)
outbox_events (RevisionCompleted dispatch)
```

### 22.2 Table schema — `revisions`

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | no | PK |
| `tenant_id` | UUID | no | |
| `student_id` | UUID | no | |
| `concept_id` | string | no | FK concepts |
| `exam_id` | string | no | Denormalized |
| `scheduled_date` | date | no | Student TZ calendar date |
| `completed_at` | timestamptz | yes | UTC |
| `completed_date` | date | yes | Student TZ |
| `status` | enum | no | `scheduled\|in_progress\|completed\|missed\|skipped\|deferred\|compressed` |
| `priority_score` | decimal(5,2) | no | 0–100 at schedule time |
| `priority_factors` | JSONB | no | Explainability payload §5.5 |
| `priority_locked_until` | date | no | Priority Stability Window §5.7 |
| `priority_version` | string | no | e.g. `revision_priority_v1_1` |
| `scheduler_version` | string | no | e.g. `scheduler_v1_1` |
| `recall_grade` | enum | yes | `forgot\|hard\|good\|easy` |
| `recall_session_id` | UUID | yes | FK recall attempt session |
| `revision_session_id` | UUID | yes | FK revision_sessions §11.6 |
| `lateness_class` | enum | yes | `on_time\|late_7d\|late_gt_7d` |
| `recovery_of_revision_id` | UUID | yes | FK revisions |
| `compression_batch_id` | UUID | yes | §10.5 |
| `compressed_into_revision_id` | UUID | yes | §10.5 |
| `row_version` | int | no | Optimistic lock |
| `created_at` | timestamptz | no | |
| `updated_at` | timestamptz | no | |

### 22.3 Table schema — `revision_sessions`

See §11.6.4 for column definitions. FK from `revisions.revision_session_id`.

### 22.4 Table schema — `revision_events`

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID PK | Idempotency |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `revision_id` | UUID nullable | |
| `concept_id` | string | |
| `event_type` | enum | See §12.1 |
| `event_version` | int | Schema version |
| `payload` | JSONB | |
| `occurred_at` | timestamptz | Business time |
| `recorded_at` | timestamptz | System time |
| `causation_id` | UUID nullable | |
| `correlation_id` | UUID | Trace |

### 22.5 Event payload minimums

| event_type | payload must include |
|---|---|
| `RevisionCompleted` | `revision_id`, `concept_id`, `recall_grade`, `recall_session_id` |
| `RevisionPlanGenerated` | `plan_date`, `scheduled_count`, `scheduler_version` |
| `RevisionMissed` | `revision_id`, `scheduled_date`, `days_overdue` |
| `RevisionHealthRecomputed` | `revision_health`, `window_days`, `numerator`, `denominator` |
| `RevisionFatigueRecomputed` | `revision_fatigue`, `sessions_7d`, `items_7d`, `components` |
| `RevisionStreakRecomputed` | `current_streak_days`, `longest_streak_days`, `streak_at_risk` |
| `RevisionBacklogIntervention` | `revision_health`, `new_daily_cap`, `reason` |
| `RevisionBacklogCompressed` | `compression_batch_id`, `topic_id`, `kept_revision_id`, `compressed_count` |
| `RevisionSessionCompleted` | `session_id`, `item_count`, `completed_count`, `duration_seconds` |
| `RetentionSnapshotBuilt` | `student_id`, `node_count`, `snapshot_at` |

---

## Appendix A — Event → system mutation matrix

| Event | revisions table | revision_events | Learning Graph | Twin behavior_profile |
|---|---|---|---|---|
| Nightly schedule | upsert scheduled rows | PlanGenerated | read snapshot/graph | — |
| Build snapshot | — | SnapshotBuilt | read + materialize | — |
| Complete revision | status→completed | append | via RevisionCompleted | health/fatigue/streak async |
| Backlog compress | status→compressed | Compressed | — | — |
| Session complete | session row update | SessionCompleted | — | fatigue async |
| Missed sweep | status→missed | append | — | health async |
| Skip | status→skipped | append | — | health async |
| LearningGraphUpdated | maybe replan; snapshot row | — | writer (other svc) | — |
| RevisionHealthRecomputed | — | append | — | write revision_health |
| RevisionFatigueRecomputed | — | append | — | write revision_fatigue |
| RevisionStreakRecomputed | — | append | — | write revision_streak |

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `REVISION_DEFAULT_DAILY_SLOTS` | 20 | Top-N default |
| `REVISION_MAX_DAILY_SLOTS` | 30 | Hard cap |
| `REVISION_AVG_MINUTES` | 4 | Capacity from minutes |
| `REVISION_LOOKAHEAD_DAYS` | 7 | Planning horizon |
| `REVISION_OVERDUE_MAX_DAYS` | 14 | Before missed |
| `OVERDUE_PRIORITY_BUMP` | 5 | Additive priority per week overdue |
| `RECOVERY_DAILY_CAP` | 5 | Max recovered missed per day |
| `BACKLOG_COMPRESSION_THRESHOLD` | 30 | §10.5 trigger |
| `BACKLOG_COMPRESSION_RECOVERY_CAP` | 3 | Recovery cap under compression |
| `HIGH_YIELD_OVERRIDE_IMPORTANCE` | 80 | Mandatory set |
| `HIGH_YIELD_OVERRIDE_RETENTION` | 60 | Mandatory set |
| `PRIORITY_STABILITY_DAYS` | 3 | §5.7 lock window |
| `CA_LOCK_BREAK_DELTA` | 15 | §9.4 urgent override |
| `CA_RELEVANCE_WINDOW_DAYS` | 30 | §9.1 |
| `CA_RECENCY_HALFLIFE_DAYS` | 7 | §9.1 |
| `CA_RELEVANCE_NORM` | 1.0 | §9.1 normalization anchor |
| `PRIORITY_W_IMPORTANCE` | 0.30 | §5.1 |
| `PRIORITY_W_RETGAP` | 0.25 | §5.1 |
| `PRIORITY_W_WEAKNESS` | 0.25 | §5.1 |
| `PRIORITY_W_PROXIMITY` | 0.10 | §5.1 |
| `PRIORITY_W_CA` | 0.10 | §5.1 |
| `PRIORITY_DECAY_RATE` | 0.08 | §5.8 per successful recall |
| `PRIORITY_DECAY_FLOOR` | 0.60 | §5.8 minimum multiplier |
| `SNAPSHOT_MAX_STALE_HOURS` | 26 | §13.5.3 |
| `REVISION_STAGE_FILTER_ENABLED` | false | Stage filter §4.3 |
| `REVISION_SPREAD_ENABLED` | true | §7.4 |
| `REVHEALTH_WINDOW_DAYS` | 60 | Scoring §6 |
| `REVHEALTH_HALFLIFE_DAYS` | 30 | Scoring §6 |
| `HEAVY_DAY_THRESHOLD` | 15 | §15.6 fatigue |
| `STREAK_RISK_HOUR` | 20 | §15.7 local hour |
| `IN_PROGRESS_TIMEOUT_MINUTES` | 30 | Sweeper §19.3 |
| `REVISION_TODAY_CACHE_TTL_SECONDS` | 120 | Redis §17 |
| `REORDER_TOLERANCE` | 0.15 | Future AI §21.3 |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `MENTOR_AGENT_SPECIFICATION` (future) | §14 tools, explainability JSON, fallback planner |
| `PREPARATION_TWIN_SPECIFICATION` (future) | §15 Health, §15.6 Fatigue, §15.7 Streak events |
| API / Presentation layer | §16 read models; student payload filtering (Scoring v1.1) |
| Assessment / Recall module | §11 recall_session validation contract |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | Graph read-only; RevisionCompleted→graph; no weakness column; snapshot defers to graph materialize |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Weakness on-demand; Revision Health display; additive priority supersedes §10.4 for scheduling |
| `SCORING_ENGINE_SPECIFICATION.md` | §5 Weakness, §6 Health, §3 spacing anti-gaming; §10.4 superseded by this spec §5 for priority |
| `EXAM_DOMAIN_SPECIFICATION.md` | §12 dependencies, mandatory override, CA relevance (replaces fixed boost), prereq tie-break |
| `MASTER_IMPLEMENTATION_PLAN.md` | S5 sprint scope; deterministic engine; event-driven twin |
| Architectural review v1.1 | C1–C10 mandatory changes — §0.1 |
| Blueprint Rule 5 | Learning Graph owns scores — §13, §18 |
| Blueprint Rule 4 | Explainability via priority_factors — §5.5, §14.4 |

---

*End of Revision Engine Specification v1.1. This document is the canonical architecture for revision scheduling and compliance. Implement `RevisionEngineService` as the sole writer of `revisions` and `revision_sessions`; all concept score mutations remain exclusively in `LearningGraphService` via `RevisionCompleted` domain events.*
