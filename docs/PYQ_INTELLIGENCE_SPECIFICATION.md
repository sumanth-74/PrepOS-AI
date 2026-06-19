# PrepOS AI — PYQ Intelligence Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for PYQ Intelligence bounded context
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`, `REVISION_ENGINE_SPECIFICATION.md` (v1.1), `PREPARATION_TWIN_SPECIFICATION.md`, `MENTOR_AGENT_SPECIFICATION.md`, `ASSESSMENT_ENGINE_SPECIFICATION.md`
Authoring lens: Principal Knowledge Systems Architect · UPSC Domain Expert · Staff Backend Architect · Learning Scientist · Data Platform Architect

> **Scope.** This document defines **PYQ Intelligence**: ingestion, verification, concept mapping, Importance computation, trend analysis, faculty weight overrides, read models, events, APIs, and integrations. It is the implementation contract for `pyq_questions`, `pyq_mappings`, `faculty_concept_weights`, Importance refresh jobs, `PYQ_OF` relationship sync, and Mentor tool backing data (`GetPYQInsightsTool`).
>
> **Non-goals:** UI layout, marketing, sprint tasks, SQL DDL, LLM answer evaluation, Assessment attempt scoring, Current Affairs linking. Mastery/Retention formulas live in Scoring specs; **student score columns** on `student_concept_progress` are updated by **Learning Graph Service** on events from this engine — PYQ never writes mastery/retention/confidence.
>
> **Core invariant:** PYQ Intelligence is the **sole writer** of PYQ catalog data and the **sole computer** of global Importance (`concepts.importance`). It emits `PYQDataChanged` / `FacultyWeightUpdated` so Learning Graph copies personalized `importance_score` to every student node — never bypassing the event path.

---

## 0. Canonical requirements map

This document is the authoritative answer to the 30 required areas:

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and bounded context | §1 |
| 2 | Ownership boundaries | §2 |
| 3 | PYQ data model | §3 |
| 4 | Ingestion pipeline architecture | §4 |
| 5 | Verification and quarantine | §5 |
| 6 | Concept mapping workflow | §6 |
| 7 | Mapping validation rules | §7 |
| 8 | Importance Engine overview | §8 |
| 9 | PYQ frequency component | §9 |
| 10 | Recent trend component | §10 |
| 11 | Exam relevance component | §11 |
| 12 | Faculty weight component | §12 |
| 13 | Importance aggregation formula | §13 |
| 14 | Per-student Importance personalization | §14 |
| 15 | Co-occurrence / `frequently_asked_with` (V2) | §15 |
| 16 | `PYQ_OF` relationship sync | §16 |
| 17 | `pyq_count` cache maintenance | §17 |
| 18 | Event-driven architecture | §18 |
| 19 | `PYQDataChanged` event contract | §19 |
| 20 | `FacultyWeightUpdated` event contract | §20 |
| 21 | Integration with Learning Graph | §21 |
| 22 | Integration with Mentor Agent | §22 |
| 23 | Integration with Assessment Engine | §23 |
| 24 | Integration with Revision Engine | §24 |
| 25 | Integration with Preparation Twin | §25 |
| 26 | Read models (`GetPYQInsightsTool`) | §26 |
| 27 | Database schemas | §27 |
| 28 | API contracts | §28 |
| 29 | Ingestion tooling and batch jobs | §29 |
| 30 | Content licensing and provenance | §30 |
| 31 | Caching strategy | §31 |
| 32 | Failure recovery | §32 |
| 33 | Performance requirements | §33 |
| 34 | Observability | §34 |
| 35 | Future AI-assisted mapping | §35 |
| 36 | Consistency checklist | Appendix D |

---

## 1. Purpose and bounded context

### 1.1 What PYQ Intelligence is

PYQ Intelligence transforms **Previous Year Questions** into structured, concept-linked signals that drive **Exam Weight (Importance)**, Mentor prioritization, Assessment question pools, and Revision yield ranking.

```
External PYQ sources          PYQ Intelligence (this spec)           Downstream (event consumers)
────────────────────          ────────────────────────────           ────────────────────────────
Official papers / licensed    ingest → verify → map → compute        Learning Graph (importance copy)
faculty uploads          ──►  ImportanceEngine                  ──►  Mentor (GetPYQInsightsTool)
                                pyq_questions / pyq_mappings          Assessment (mock/drill pools)
                                faculty_concept_weights               Revision (priority via importance)
                                PYQ_OF edges                          Twin / Readiness / Analytics
                                      │
                                      ▼
                               PYQDataChanged / FacultyWeightUpdated
                               → Learning Graph RefreshImportanceForExam
```

### 1.2 What PYQ Intelligence is NOT

| Misconception | Reality |
|---|---|
| Assessment Engine | Assessment **reads** PYQ pool; PYQ **owns** catalog + mappings |
| Learning Graph writer for scores | Never writes `mastery_score`, `retention_score`, etc. |
| Scoring Engine | Implements **Importance formula only** (Scoring v1.0 §4); other scores unchanged |
| Mentor recommender | Supplies **signals**; Mentor decides tasks |
| RAG / Knowledge Agent | PYQ text may feed RAG later; ingestion pipelines are separate |
| LLM auto-map without review | V1 requires human verification for production mappings |

### 1.3 Bounded context (DDD)

```
┌──────────────────────────────────────────────────────────────────┐
│                 PYQ Intelligence Context (this spec)              │
│  IngestionService · MappingService · ImportanceEngine              │
│  pyq_questions · pyq_mappings · faculty_concept_weights           │
│  pyq_ingestion_batches · pyq_mapping_review_queue                 │
└───────────────┬──────────────────────────────────────────────────┘
                │ read catalog           │ events + global importance
    ┌───────────┼───────────┐            ▼
    ▼           ▼           ▼     Learning Graph Service
 Exam Domain  Learning     Assessment   (student importance copy)
 (concepts)   Graph read   (question pools)
```

### 1.4 UPSC domain semantics

| Dimension | PYQ behavior |
|---|---|
| **Prelims GS Paper I** | Primary V1 corpus; MCQ mappings drive Importance |
| **Mains descriptive** | Mapped with `mains_gs1`–`mains_gs4` papers; lower weight in Prelims-focused phase |
| **Essay** | Separate paper tag; feeds WritingSub routing, not MCQ frequency |
| **CSAT** | Tracked; `exam_relevance` reduced unless student targets CSAT |
| **Cross-subject questions** | Multi-concept weights per EXAM_DOMAIN §9.3 |
| **High-yield concepts** | `importance ≥ 70` — Revision mandatory override, Readiness coverage |
| **Unmapped questions** | Quarantined — **never** guessed to nearest concept (EXAM_DOMAIN P6) |

### 1.5 Success criteria

1. Every production `pyq_mappings` row sums to 1.0 ±0.01 and targets `pyq_mappable=true` concepts.
2. `ImportanceEngine` output is **deterministic**: same PYQ corpus + faculty weights + config ⇒ identical `concepts.importance`.
3. `PYQDataChanged` → all affected students' `importance_score` refreshed within **p95 < 15 min** (async batch).
4. `GetPYQInsightsTool` returns in **p95 < 80ms** (cached).
5. Zero PYQ service writes to `student_concept_progress` except via Learning Graph event consumer (architectural test).
6. Ingestion batch is **fully auditable** (source license, operator, diff).

---

## 2. Ownership boundaries

### 2.1 Write ownership matrix

| Data | Sole writer | PYQ relationship |
|---|---|---|
| `pyq_questions` | **PYQ Service** | Authoritative question store |
| `pyq_mappings` | **PYQ Service** | Concept links |
| `pyq_ingestion_batches` | **PYQ Service** | Audit trail |
| `pyq_mapping_review_queue` | **PYQ Service** | Faculty workflow |
| `faculty_concept_weights` | **PYQ Service** | Tenant-scoped overrides |
| `concept_pyq_stats` | **PYQ Service** | Denormalized frequency/trend cache |
| `concepts.importance` | **PYQ Service** (computed) | Global Exam Weight cache |
| `concepts.pyq_count` | **PYQ Service** | Denormalized hit count |
| `concept_relationships` (`PYQ_OF`) | **PYQ Service** | Synced from mappings |
| `student_concept_progress.importance_score` | **Learning Graph Service** | Copied on `PYQDataChanged` |
| `student_concept_progress` other scores | Learning Graph | **Never written by PYQ** |

### 2.2 Forbidden operations

1. PYQ worker updating `mastery_score`, `retention_score`, `confidence_score` on graph rows.
2. Auto-mapping unverified questions to concepts with `confidence < 0.85` in production catalog.
3. Deleting `pyq_questions` without tombstone (`status=archived`) — breaks audit replay.
4. Importance refresh skipping quarantined/unverified mappings.
5. Cross-tenant faculty weight leakage (weights MUST be tenant-scoped).
6. Silent remapping changing Importance without emitting `PYQDataChanged`.

### 2.3 Importance ownership split

| Layer | Owner | Storage |
|---|---|---|
| **Global Importance computation** | PYQ Intelligence (`ImportanceEngine`) | `concepts.importance` |
| **Student Importance copy** | Learning Graph (`RefreshImportanceForExam`) | `student_concept_progress.importance_score` |
| **Formula definition** | This spec §8–§14 (implements Scoring v1.0 §4) | Config keys |

This preserves blueprint Rule 5 (scores owned by engines) while making PYQ the **input authority** for Exam Weight.

---

## 3. PYQ data model

### 3.1 Question entity — `pyq_questions`

| Column | Type | Description |
|---|---|---|
| `question_id` | UUID PK | Stable id |
| `tenant_id` | UUID nullable | null = platform-global catalog |
| `exam_id` | string | e.g. `upsc_cse` |
| `year` | int | Exam year asked |
| `paper` | enum | `prelims_gs1`, `prelims_csat`, `mains_gs1`…`mains_gs4`, `mains_essay` |
| `question_number` | int nullable | Official paper Q number |
| `question_text` | text | Stem (options separate for MCQ) |
| `options_json` | JSONB nullable | MCQ options |
| `correct_option_id` | string nullable | |
| `question_type` | enum | `mcq`, `mains_descriptive`, `essay` |
| `difficulty` | int 1–5 | Default 3; refined by analytics later |
| `marks` | decimal nullable | Mains marks |
| `status` | enum | `draft`, `verified`, `quarantine`, `archived` |
| `source_id` | UUID FK | Provenance (§30) |
| `source_license` | string | License tag |
| `ingestion_batch_id` | UUID FK | |
| `catalog_version` | int | Bumps on publish |
| `created_at` | timestamptz | |
| `verified_at` | timestamptz nullable | |
| `verified_by` | UUID nullable | faculty/admin |

### 3.2 Mapping entity — `pyq_mappings`

Per EXAM_DOMAIN §9.2:

| Column | Type | Description |
|---|---|---|
| `mapping_id` | UUID PK | |
| `question_id` | UUID FK | |
| `concept_id` | string FK | Must be `pyq_mappable=true` |
| `weight` | decimal(4,3) | 0.0–1.0 |
| `mapping_type` | enum | `primary`, `secondary`, `distractor` |
| `mapped_by` | enum | `system`, `faculty`, `admin` |
| `verified` | bool | Production Importance requires true |
| `confidence` | decimal(3,2) nullable | AI suggestions |
| `created_at` | timestamptz | |

**Invariant:** `SUM(weight) GROUP BY question_id` ∈ [0.99, 1.01].

### 3.3 Faculty weight entity — `faculty_concept_weights`

| Column | Type | Description |
|---|---|---|
| `tenant_id` | UUID | Institute scope |
| `concept_id` | string | |
| `faculty_weight` | int 0–100 | Neutral default 50 |
| `reason` | text nullable | Audit |
| `updated_by` | UUID | |
| `updated_at` | timestamptz | |

Platform default when no row: **`FACULTY_WEIGHT_NEUTRAL = 50`**.

### 3.4 Concept PYQ stats cache — `concept_pyq_stats`

| Column | Type | Description |
|---|---|---|
| `exam_id` | string | |
| `concept_id` | string | PK with exam_id |
| `pyq_count` | int | Verified mapping count (weighted) |
| `pyq_count_raw` | int | Unweighted question appearances |
| `hits_last_5y` | decimal | Trend numerator |
| `hits_prior_5y` | decimal | Trend denominator |
| `frequency_norm` | decimal(5,2) | 0–100 |
| `trend_norm` | decimal(5,2) | 0–100 |
| `last_computed_at` | timestamptz | |

---

## 4. Ingestion pipeline architecture

### 4.1 Pipeline stages

```
Source file/API
      │
      ▼
┌─────────────┐
│ Parse       │  schema validation, dedupe by (exam, year, paper, Q#)
└──────┬──────┘
       ▼
┌─────────────┐
│ Normalize   │  clean text, option shuffle metadata, difficulty default
└──────┬──────┘
       ▼
┌─────────────┐
│ License chk │  reject if source not licensed (§30)
└──────┬──────┘
       ▼
┌─────────────┐
│ Persist     │  pyq_questions status=draft; pyq_ingestion_batches row
└──────┬──────┘
       ▼
┌─────────────┐
│ Map queue   │  auto-suggest OR faculty manual (§6)
└──────┬──────┘
       ▼
┌─────────────┐
│ Verify      │  status=verified; mappings verified=true
└──────┬──────┘
       ▼
┌─────────────┐
│ Publish     │  catalog_version++; Importance recompute; PYQDataChanged
└─────────────┘
```

### 4.2 Supported ingestion formats (V1)

| Format | Use case |
|---|---|
| JSON bundle | Internal curated seed (`seeds/pyq_upsc_cse_v1.json`) |
| CSV | Bulk faculty upload (columns: year, paper, q_num, text, optA–D, answer) |
| Admin API | Single-question create |

### 4.3 Dedupe key

```
dedupe_key = hash(exam_id, year, paper, normalize(question_text))
```

Duplicate ingest → link to existing `question_id`; log in batch metadata (no double-count in Importance).

### 4.4 Ingestion batch — `pyq_ingestion_batches`

| Column | Purpose |
|---|---|
| `batch_id` | PK |
| `source_id` | License/provenance |
| `operator_id` | Who ran import |
| `status` | `pending`, `completed`, `failed`, `partial` |
| `stats_json` | `{ inserted, updated, quarantined, duplicates }` |
| `started_at`, `completed_at` | |

---

## 5. Verification and quarantine

### 5.1 Status transitions

```
draft ──verify──► verified ──publish──► (in production pool)
  │
  ├──quarantine──► quarantine (mapping failed / license / QA)
  │
  └──archive──► archived (removed from selection, kept for audit)
```

### 5.2 Quarantine triggers

| Trigger | Action |
|---|---|
| No concept mapping after 30 days | `status=quarantine` |
| Mapping weight sum ≠ 1.0 | Block verify |
| Concept `pyq_mappable=false` | Reject mapping |
| `prelims_relevance=0` for Prelims MCQ primary | Flag for review |
| License expired on `source_id` | Quarantine entire batch |
| Duplicate conflicting answers | Quarantine until resolved |

### 5.3 Verification checklist (faculty)

1. Question text matches official paper.
2. Correct option verified against key.
3. Primary concept reflects what UPSC tested (not distractor topic).
4. Weights reflect multi-concept split.
5. Cross-subject tags validated.

### 5.4 Production eligibility

Only questions with:

```
status == 'verified'
AND all mappings.verified == true
AND source_license active
```

participate in Importance computation and Assessment PYQ pools.

---

## 6. Concept mapping workflow

### 6.1 Mapping modes

| Mode | Who | V1 |
|---|---|---|
| **Manual faculty** | Faculty UI | Primary |
| **Admin bulk** | Platform admin | Seed loads |
| **AI-suggested** | Mapping assistant (V2) | Queue only; §35 |
| **Rule-based seed** | Keyword → concept rules | Bootstrap only; requires verify |

### 6.2 Workflow `SubmitMapping`

```
INPUT: question_id, mappings[{concept_id, weight, mapping_type}]
1.  VALIDATE concepts exist, pyq_mappable=true, active
2.  VALIDATE sum(weights) ≈ 1.0
3.  VALIDATE at most one primary with weight >= 0.50 OR single primary weight=1.0
4.  UPSERT pyq_mappings; set verified=false if faculty, true if admin+confirm
5.  IF question was quarantine AND now valid: status=draft (await verify)
6.  Append pyq_mapping_events audit
```

### 6.3 Review queue — `pyq_mapping_review_queue`

| Column | Purpose |
|---|---|
| `question_id` | FK |
| `priority` | Unmapped high-traffic first |
| `assigned_faculty_id` | nullable |
| `sla_due_at` | |
| `status` | `open`, `in_review`, `resolved`, `escalated` |

**Priority:** recent year > high `paper` weight > duplicate cluster.

### 6.4 Bulk mapping patterns (templates)

| Pattern ID | Rule |
|---|---|
| `single_primary` | One concept weight 1.0 |
| `primary_secondary` | 0.65 / 0.35 split default |
| `cross_subject_gst` | economy 0.6 + polity 0.4 |

Templates accelerate faculty UI; always stored as explicit weights.

---

## 7. Mapping validation rules

### 7.1 Hard rules (reject)

1. Weight sum outside [0.99, 1.01].
2. Map to deprecated concept.
3. Distractor-only mapping (all weights on `distractor` type without primary).
4. More than **5** concepts per question (force simplification).
5. Primary concept weight < 0.50 when multiple primaries declared.

### 7.2 Soft warnings (allow with audit)

1. Cross-subject split with no `primary` ≥ 0.50.
2. Mains question mapped only to Prelims-high concept.
3. Rare concept with sudden spike (possible mis-tag).

### 7.3 Auto-QA job `ValidateMappingQuality`

Nightly scan:

```
FOR each verified question:
  IF primary concept.prelims_relevance == 0 AND paper.startswith('prelims'):
     FLAG mapping_review_queue priority=high
  IF weight entropy > threshold (too many tiny weights):
     FLAG simplify
```

---

## 8. Importance Engine overview

### 8.1 Business purpose

**Importance (Exam Weight)** answers: *"How much does UPSC care about this concept, based on past papers and exam structure?"*

Range: **0–100**. Drives Revision priority, Readiness weighting, Mentor study sorting, Assessment targeting.

### 8.2 Engine placement

```
ImportanceEngine(exam_id, concept_id) → importance 0–100
```

Implemented as **pure function** in PYQ Service; persisted to `concepts.importance`; triggers graph copy via event.

### 8.3 Component overview

| Component | Symbol | Weight (default) | Source |
|---|---|---:|---|
| PYQ frequency | `F` | **0.40** | Verified mappings, recency-weighted |
| Recent trend | `T` | **0.20** | Last 5y vs prior 5y hit ratio |
| Exam relevance | `E` | **0.25** | `prelims_relevance`, `mains_relevance` |
| Faculty weight | `W` | **0.15** | `faculty_concept_weights` |

Config keys: `IMP_WEIGHT_FREQ`, `IMP_WEIGHT_TREND`, `IMP_WEIGHT_EXAM`, `IMP_WEIGHT_FACULTY` — must sum to **1.0**.

### 8.4 Aggregation (preview)

```
importance_raw = IMP_WEIGHT_FREQ * F + IMP_WEIGHT_TREND * T + IMP_WEIGHT_EXAM * E + IMP_WEIGHT_FACULTY * W
importance = round(clamp(importance_raw, 0, 100), 2)
```

### 8.5 Concepts with zero PYQ hits

Concepts with **no verified PYQ mappings** still receive Importance from **E + W** components (structural syllabus weight + faculty boost). `F` and `T` default to **0** unless `IMPORTANCE_BASELINE_NO_PYQ > 0` (default **0**).

This prevents unrated syllabus areas from showing `importance=0` when exam relevance is high.

---

## 9. PYQ frequency component

### 9.1 Hit definition

A **hit** occurs when verified question `Q` maps to concept `C` with weight `w`.

```
hit_strength(Q, C) = w * paper_weight(Q.paper) * type_weight(Q.question_type)
```

**Default weights:**

| Factor | Value |
|---|---|
| `paper_weight(prelims_gs1)` | 1.0 |
| `paper_weight(prelims_csat)` | 0.3 |
| `paper_weight(mains_gs*)` | 0.6 |
| `paper_weight(mains_essay)` | 0.4 |
| `type_weight(mcq)` | 1.0 |
| `type_weight(mains_descriptive)` | 0.8 |

### 9.2 Recency decay

```
year_decay(y) = exp(-PYQ_RECENCY_LAMBDA * (current_year - y))    // default λ=0.12
```

### 9.3 Raw frequency

```
pyq_raw(C) = Σ_{Q mapped to C} hit_strength(Q,C) * year_decay(Q.year)
```

### 9.4 Normalization to 0–100

Log-scaled percentile across active concepts in exam:

```
F(C) = 100 * log(1 + pyq_raw(C)) / log(1 + max_{C'} pyq_raw(C'))
```

If `pyq_raw(C) == 0`: `F(C) = 0`.

**Alternative (small catalogs):** percentile rank — config `IMPORTANCE_FREQ_NORM=log|percentile`.

---

## 10. Recent trend component

### 10.1 Purpose

Boost concepts appearing **more often recently** — captures shifting UPSC emphasis (e.g. environment, IR).

### 10.2 Window definition

```
TRECENT_YEARS = 5
hits_recent(C) = Σ hits where Q.year >= current_year - TRECENT_YEARS + 1
hits_prior(C)  = Σ hits where current_year - 2*TRECENT_YEARS + 1 <= Q.year <= current_year - TRECENT_YEARS
```

Use same `hit_strength` as §9.1 (without double year_decay — trend is explicit windowing).

### 10.3 Trend ratio

```
trend_ratio(C) = (hits_recent(C) + 1) / (hits_prior(C) + 1)
```

### 10.4 Normalization

```
T(C) = clamp(100 * (trend_ratio(C) - TREND_FLOOR) / (TREND_CEIL - TREND_FLOOR), 0, 100)
```

Defaults: `TREND_FLOOR=0.5`, `TREND_CEIL=2.0`.

| trend_ratio | Interpretation | T |
|---|---|---|
| 0.5 | declining | 0 |
| 1.0 | stable | ~33 |
| 2.0 | doubling | 100 |

Store `hits_recent`, `hits_prior`, `trend_norm` in `concept_pyq_stats`.

---

## 11. Exam relevance component

### 11.1 Structural relevance (domain)

From EXAM_DOMAIN §7.3:

```
exam_rel_base(C) = max(C.prelims_relevance, C.mains_relevance)   // 0–100 domain fields
```

### 11.2 Stage-aware adjustment

For global Importance (exam-wide default):

```
E(C) = exam_rel_base(C)   // already 0–100
```

Learning Graph personalization (§14) applies student stage weighting when copying to student nodes.

### 11.3 Optional subject concepts

Optional-subject-only concepts (`exam_stages` includes optional):

```
E(C) *= OPTIONAL_SUBJECT_EXAM_REL_FACTOR   // default 1.0 (no global penalty)
```

Global Importance remains exam-wide; student copy handles optional filtering.

---

## 12. Faculty weight component

### 12.1 Purpose

Institutes may emphasize institute-specific priorities (e.g. batch focusing on Economy).

### 12.2 Value

```
W(C) = faculty_weight(tenant, C)   // 0–100, default 50 neutral
```

Neutral **50** maps to mid-scale — does not drag Importance when faculty silent.

### 12.3 Tenant scope

- Platform tenant (`tenant_id=platform`): default weights for B2C students.
- Institute tenant: overrides platform for their students during personalization (§14).

### 12.4 Update flow

```
UpsertFacultyWeight(tenant, concept, weight, reason):
1.  VALIDATE concept exists
2.  UPSERT faculty_concept_weights
3.  Recompute Importance for affected concepts (async)
4.  EMIT FacultyWeightUpdated
```

---

## 13. Importance aggregation formula

### 13.1 Final formula (Scoring v1.0 §4 — canonical)

```
INPUT: concept C, exam_id, tenant_id (for faculty), config
1.  F = PYQFrequency(C)           // §9
2.  T = PYQTrend(C)               // §10
3.  E = ExamRelevance(C)          // §11
4.  W = FacultyWeight(tenant, C)  // §12
5.  raw = IMP_WEIGHT_FREQ*F + IMP_WEIGHT_TREND*T + IMP_WEIGHT_EXAM*E + IMP_WEIGHT_FACULTY*W
6.  importance = round(clamp(raw, 0, 100), 2)
7.  RETURN importance, components_json { F, T, E, W, raw }
```

### 13.2 Worked example

**Concept:** `upsc.cse.polity.fundamental_rights.article_14`

| Component | Value |
|---|---:|
| F (PYQ frequency) | 92 |
| T (trend) | 78 |
| E (exam relevance) | 95 |
| W (faculty, neutral) | 50 |

```
raw = 0.40*92 + 0.20*78 + 0.25*95 + 0.15*50
    = 36.8 + 15.6 + 23.75 + 7.5 = 83.65
importance = 83.65 → **84** (Exam Weight: High)
```

**Concept:** obscure state-specific topic with no PYQ hits:

| F | T | E | W |
|---|---|---|---|
| 0 | 0 | 42 | 50 |

```
raw = 0.25*42 + 0.15*50 = 10.5 + 7.5 = 18 → importance **18** (Low)
```

### 13.3 Exam Weight bands (Scoring v1.1 R5 display)

| importance | Band |
|---:|---|
| ≥ 70 | High |
| 40–69 | Medium |
| < 40 | Low |

### 13.4 Batch recompute `RefreshImportanceForExam`

```
INPUT: exam_id, tenant_id optional (faculty scope)
1.  concepts = active concepts WHERE exam_id AND pyq_mappable OR exam_relevance > 0
2.  Rebuild concept_pyq_stats for all concepts (§17)
3.  FOR each concept C in batches of 500:
        I = ImportanceEngine(C)
        UPDATE concepts SET importance=I, importance_version=IMPORTANCE_VERSION, components_json=...
4.  Sync PYQ_OF edges (§16)
5.  EMIT PYQDataChanged { exam_id, concepts_affected, catalog_version }
```

---

## 14. Per-student Importance personalization

### 14.1 Executed by Learning Graph (not PYQ)

On `PYQDataChanged`, Learning Graph runs `RefreshImportanceForExam` (`LEARNING_GRAPH_SPECIFICATION.md` §8.3):

```
personalized_I(student, C) = clamp(global_I(C) * stage_mult + faculty_delta, 0, 100)
```

### 14.2 Stage multiplier

```
stage_mult(student, C) =
  IF 'prelims' IN student.target_stages AND C.prelims_relevance >= C.mains_relevance:
     PRELIMS_STAGE_BOOST     // default 1.0 (no change at global level)
  ELIF 'mains' IN student.target_stages AND C.mains_relevance > C.prelims_relevance:
     MAINS_STAGE_BOOST       // default 1.0
  ELSE: 1.0
```

V1 keeps multipliers at **1.0** globally; student **target_stages** filter which concepts appear in Mentor plans (not Importance nulling).

### 14.3 Optional subject rule (EXAM_DOMAIN §4.10 / Mentor §1.4)

```
IF concept.subject_id == student.optional_subject_id:
   weight_mult = 1.0
ELIF concept.is_optional_subject_only AND concept.subject_id != student.optional_subject_id:
   personalized_I = 0   // hide from student importance copy (not in their exam)
ELSE:
   weight_mult = NON_OPTIONAL_IMPORTANCE_FACTOR   // default 0.9
personalized_I = global_I(C) * weight_mult
```

Optional-only concepts for **other** optionals are excluded (`importance_score=0` or node hidden from plans).

### 14.4 Institute faculty override

When student belongs to institute tenant:

```
W(C) = institute_faculty_weight IF exists ELSE platform_faculty_weight IF exists ELSE 50
```

Recompute triggered by `FacultyWeightUpdated` scoped to tenant.

---

## 15. Co-occurrence / `frequently_asked_with` (V2)

### 15.1 Master Plan decision (D8)

`frequently_asked_with` relationship (EXAM_DOMAIN §10.2 legacy) is **deferred to V2**. Schema retained; no V1 Importance effect.

### 15.2 Planned algorithm (V2 outline)

```
FOR each exam year window:
  build co-occurrence pairs (C1, C2) from questions mapping to both
  IF lift(C1,C2) > COOC_LIFT_THRESHOLD:
     UPSERT concept_relationships RELATED_TO tag co_occurrence=pyq
```

### 15.3 Future uses

- Mentor "study together" suggestions
- Question generation clusters
- Optional small boost to Importance for bridge concepts (config gated)

**V1:** co-occurrence edges may be **seeded manually**; Importance ignores them.

---

## 16. `PYQ_OF` relationship sync

### 16.1 Purpose

Graph traversal (Mentor, analytics) uses `PYQ_OF` edges per EXAM_DOMAIN §10.2.

### 16.2 Sync algorithm

```
SyncPYQEdges(exam_id):
1.  DELETE FROM concept_relationships
      WHERE exam_id AND relationship_type='PYQ_OF' AND source_type='pyq_question'
2.  FOR each verified mapping (Q, C, weight):
      INSERT concept_relationships
        source_id=Q.question_id, source_type=pyq_question,
        target_id=C, target_type=concept,
        relationship_type=PYQ_OF,
        weight=mapping.weight, status=active
```

Runs on every Importance publish (same transaction as stats update).

### 16.3 Idempotency

Full replace strategy — deterministic end state from mappings snapshot.

---

## 17. `pyq_count` cache maintenance

### 17.1 Definition

```
pyq_count(C) = COUNT(DISTINCT question_id) WHERE verified mapping to C with weight >= 0.10
```

Weighted count (alternative):

```
pyq_count_weighted(C) = Σ weights across verified mappings
```

**EXAM_DOMAIN** exposes `concepts.pyq_count` — V1 uses **distinct question count**.

### 17.2 Update

Recomputed in `RefreshImportanceForExam` batch; stored on `concepts.pyq_count`, `concepts.pyq_count_cached_at`.

### 17.3 Consumer usage

| Consumer | Use |
|---|---|
| Mentor `GetPYQInsightsTool` | Display "appears in N PYQs" |
| Faculty dashboard | Mapping coverage |
| Importance explainability | `reasoning_json.pyq_count` |

---

## 18. Event-driven architecture

### 18.1 Events emitted

| Event | When | Consumers |
|---|---|---|
| **`PYQDataChanged`** | Importance publish, mapping bulk change | Learning Graph, Twin, Mentor cache, Assessment pools |
| **`FacultyWeightUpdated`** | Faculty weight upsert | Learning Graph, Twin |
| **`PYQIngestionCompleted`** | Batch ingest done | Admin analytics |
| **`PYQMappingQuarantined`** | QA failure | Faculty queue notifications |
| **`ImportanceRecomputeCompleted`** | Batch job finish | Observability |

### 18.2 Events consumed

| Event | Action |
|---|---|
| `DomainCatalogUpdated` | Revalidate mappings against deprecated concepts |
| `StudentRegistered` | No PYQ action (LG copies existing global Importance) |

### 18.3 Outbox

Same pattern as Assessment Engine: durable outbox before bus publish; idempotent consumers.

---

## 19. `PYQDataChanged` event contract

### 19.1 Payload schema (version 1)

```json
{
  "event_id": "uuid",
  "event_version": 1,
  "event_type": "PYQDataChanged",
  "tenant_id": "uuid",
  "exam_id": "upsc_cse",
  "occurred_at": "2026-06-18T03:00:00Z",
  "correlation_id": "uuid",
  "catalog_version": 42,
  "trigger": "ingestion_publish|mapping_update|importance_recompute",
  "concepts_affected_count": 497,
  "concepts_sample": [
    {
      "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
      "importance_old": 81.2,
      "importance_new": 83.65,
      "pyq_count": 14
    }
  ],
  "importance_version": "importance_v1"
}
```

Full delta list optional for large exams — consumer may reload all `concepts.importance` for `exam_id`.

### 19.2 Consumer obligations

1. Learning Graph: run `RefreshImportanceForExam` for all students on exam (batched).
2. Mentor: invalidate `GetPYQInsightsTool` cache.
3. Assessment: invalidate PYQ question pool cache (`ASSESSMENT_ENGINE_SPECIFICATION.md` §31).

---

## 20. `FacultyWeightUpdated` event contract

```json
{
  "event_id": "uuid",
  "event_type": "FacultyWeightUpdated",
  "tenant_id": "uuid",
  "exam_id": "upsc_cse",
  "concept_ids": ["upsc.cse.economy.monetary_policy.repo_rate"],
  "faculty_weight": 85,
  "updated_by": "uuid",
  "occurred_at": "ISO8601"
}
```

Learning Graph recomputes Importance for listed concepts only (incremental path).

---

## 21. Integration with Learning Graph

### 21.1 Division of responsibility

| Action | Owner |
|---|---|
| Compute global Importance | PYQ Intelligence |
| Persist `concepts.importance` | PYQ Intelligence |
| Copy to `student_concept_progress.importance_score` | Learning Graph |
| Apply optional-subject personalization | Learning Graph §14 |
| Use Importance in Revision Priority | Revision Engine (reads graph) |

### 21.2 Learning Graph handler

On `PYQDataChanged`:

```
1.  Load all concepts.importance for exam_id
2.  FOR each student batch (1000):
        FOR each student_concept_progress row:
           personalized = PersonalizeImportance(student, concept, global_I)
           node.importance_score = personalized
3.  Emit LearningGraphUpdated per changed node (batched) OR bulk invalidation
```

### 21.3 Cold start

Before first PYQ seed: `concepts.importance` null → LG uses `exam_relevance` only fallback (`IMPORTANCE_FALLBACK_EXAM_REL=true`) until first `PYQDataChanged`.

---

## 22. Integration with Mentor Agent

### 22.1 `GetPYQInsightsTool` (Mentor §11)

Backed by PYQ read model §26 — not live scans of `pyq_mappings`.

### 22.2 Signals used in planning

| Signal | Planning use |
|---|---|
| `pyq_weak_concepts` | MCQ drill targets (with Assessment gaps) |
| `high_yield_unrated` | New study tasks (`mentor.pyq_high_yield_new`) |
| `trending_topics` | Monthly plan theme |
| Global `importance` on graph | Study/revision sort (via Twin/Graph tools) |

### 22.3 MCQ drill union (Mentor §9.3)

```
candidates = union(assessment_gaps.weak_concepts, pyq.pyq_weak_high_yield)
sort by importance × error_rate DESC
```

PYQ provides `pyq_weak_high_yield` from read model.

### 22.4 Monthly PYQ audit task

Deterministic template in Mentor §11.4 — requires PYQ stats for weakest high-yield topic selection.

---

## 23. Integration with Assessment Engine

### 23.1 Read-only PYQ pool

Assessment selects from verified `pyq_questions` via `PYQReadPort`:

| Method | Purpose |
|---|---|
| `list_eligible_by_concept(concept_id, limit)` | Drill pools |
| `list_mock_candidates(subject_quotas, exclude_ids)` | Prelims mock §7 |
| `get_question(question_id)` | Serve attempt |

### 23.2 Cache invalidation

Assessment listens to `PYQDataChanged` → invalidate `assess:pool:*` keys.

### 23.3 Shared tagging model

PYQ mappings use same weight semantics as `platform_question_mappings` (Assessment §5) for consistent concept attribution.

---

## 24. Integration with Revision Engine

### 24.1 Indirect integration

Revision Engine does **not** call PYQ Service directly. It reads `importance_score` from Learning Graph nodes (`REVISION_ENGINE_SPECIFICATION.md` §5).

### 24.2 Effects of PYQ-driven Importance

| Mechanism | Effect |
|---|---|
| Priority formula `imp_s = I/100` | Higher PYQ frequency → higher revision priority |
| Mandatory override `I≥80 ∧ R<60` | High-yield PYQ concepts forced into queue |
| Backlog compression | High-yield preserved (never compressed away) |

### 24.3 Trending topics

Rising trend (§10) surfaces in Mentor monthly plans → more study → eventual revision — no direct Revision Engine hook V1.

---

## 25. Integration with Preparation Twin

### 25.1 Twin rebuild

On `PYQDataChanged`:

```
PartialRebuild(prediction_profile)   // Readiness uses importance-weighted sub-scores
```

Knowledge profile rollups unchanged unless `LearningGraphUpdated` follows importance copy.

### 25.2 Readiness impact

Importance change alters:

- `KnowledgeSub` denominator weights
- `RetentionSub` weights
- `coverage` high-importance set

Twin recomputes Readiness after graph importance copy completes.

---

## 26. Read models

### 26.1 `student_pyq_insights` (Mentor tool backing)

PK: `(tenant_id, student_id)`

| Field | Source |
|---|---|
| `pyq_weak_concepts_json` | graph mastery + pyq_count + importance |
| `trending_topics_json` | concept_pyq_stats aggregated to topic |
| `high_yield_unrated_json` | importance ≥ 80, node_state=unrated |
| `as_of` | timestamptz |

### 26.2 `RebuildStudentPYQInsights`

```
INPUT: student_id
1.  rated = LearningGraphReadPort.list_nodes(student)
2.  pyq_weak = [ C WHERE pyq_count>=5 AND importance>=70 AND mastery<55 ]
3.  high_yield_unrated = [ C WHERE importance>=80 AND node_state=unrated ]
4.  trending_topics = TOP 5 topics BY avg(trend_norm) among concepts with pyq_count>=3
5.  UPSERT student_pyq_insights
```

Refresh: nightly + on `PYQDataChanged` + on `LearningGraphUpdated` (mastery changed).

### 26.3 `GetPYQInsightsTool` response (authoritative)

```json
{
  "schema_version": "pyq_tool_v1",
  "data": {
    "pyq_weak_concepts": [
      {
        "concept_id": "upsc.cse.economy.monetary_policy.repo_rate",
        "importance": 88,
        "pyq_count": 9,
        "student_mastery": 41.2,
        "error_rate_90d": 0.52
      }
    ],
    "trending_topics": [
      {
        "topic_id": "upsc.cse.environment.climate",
        "trend_norm": 0.85,
        "subject_id": "upsc.cse.environment",
        "label": "Climate Change"
      }
    ],
    "high_yield_unrated": [
      {
        "concept_id": "upsc.cse.polity.parliament.sessions",
        "importance": 95,
        "pyq_count": 12,
        "node_state": "unrated"
      }
    ],
    "as_of": "2026-06-18T02:00:00Z"
  }
}
```

### 26.4 `exam_pyq_coverage` (faculty analytics)

| Column | Purpose |
|---|---|
| `exam_id` | |
| `verified_question_count` | |
| `mapped_percentage` | |
| `quarantine_count` | |
| `unmapped_high_priority_count` | |

---

## 27. Database schemas

### 27.1 Additional tables

**`pyq_sources`** (provenance §30)

| Column | Type |
|---|---|
| `source_id` | UUID PK |
| `name` | string |
| `license_type` | enum |
| `license_expires_at` | date nullable |
| `attribution_text` | text |

**`pyq_mapping_events`** (audit)

Append-only mapping change log.

**`importance_recompute_runs`**

Checkpoint for batch jobs (started, completed, concepts_updated).

### 27.2 Indexing

| Index | Purpose |
|---|---|
| `(exam_id, year, paper)` on pyq_questions | Mock assembly |
| `(concept_id)` on pyq_mappings | Frequency compute |
| `(tenant_id, concept_id)` on faculty_concept_weights | Faculty lookup |
| `(exam_id, importance DESC)` on concepts | High-yield queries |

---

## 28. API contracts

### 28.1 Admin / faculty APIs

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/pyq/ingest` | Start batch ingest |
| GET | `/admin/pyq/batches/{id}` | Batch status |
| POST | `/admin/pyq/questions` | Create single question |
| PATCH | `/admin/pyq/questions/{id}` | Update / verify |
| PUT | `/admin/pyq/questions/{id}/mappings` | Replace mappings |
| GET | `/faculty/pyq/review-queue` | Mapping queue |
| POST | `/faculty/pyq/questions/{id}/verify` | Verify question |
| PUT | `/faculty/concept-weights/{concept_id}` | Faculty weight |

### 28.2 Read APIs

| Method | Path | Purpose |
|---|---|---|
| GET | `/pyq/questions/{id}` | Question detail (faculty+) |
| GET | `/pyq/concepts/{concept_id}/questions` | PYQs for concept |
| GET | `/internal/pyq/insights/{student_id}` | Mentor tool port |
| GET | `/internal/pyq/pool` | Assessment pool port |
| POST | `/internal/pyq/importance/recompute` | Trigger recompute (admin) |

### 28.3 Student-facing (V1 minimal)

Students do **not** browse raw PYQ bank in V1 (Assessment serves questions). Optional V1.1: "PYQ practice" links to Assessment drill with PYQ flag.

---

## 29. Ingestion tooling and batch jobs

### 29.1 Seed job (S7 exit criteria)

```
scripts/seed_pyq_upsc_cse_v1.py
  → load seeds/pyq_upsc_cse_v1.json
  → verify mappings bundled
  → publish catalog_version=1
  → emit PYQDataChanged
```

### 29.2 Scheduled jobs

| Job | Schedule | Action |
|---|---|---|
| `ImportanceNightlyRefresh` | 02:00 UTC | Full recompute (catch decay/trend window roll) |
| `MappingQualityScan` | 03:00 UTC | Quarantine QA (§7.3) |
| `PYQCoverageReport` | Weekly | Faculty analytics |
| `LicenseExpiryScan` | Daily | Quarantine expired sources |

### 29.3 Manual recompute

```
POST /internal/pyq/importance/recompute { exam_id, reason }
  → async job ImportanceRecomputeCompleted
```

---

## 30. Content licensing and provenance

### 30.1 Master Plan requirements (G8 / D12)

Every PYQ row MUST reference `source_id` with valid license before `verified` status.

### 30.2 License types

| Type | Use |
|---|---|
| `public_domain` | Government releases |
| `licensed_publisher` | Contracted content vendor |
| `institute_owned` | Faculty-authored |
| `fair_use_summary` | Stem summary only — not full reproduction |

### 30.3 Ingestion gate

```
IF source.license_expires_at < today:
  REJECT new verifies; quarantine existing if policy requires
```

### 30.4 Attribution

Student-facing explanation screens display `attribution_text` where required by license.

### 30.5 RAG boundary (V2)

Full question text in `knowledge_chunks` requires separate license flag — PYQ catalog does not auto-export to RAG.

---

## 31. Caching strategy

### 31.1 Redis keys

| Key | TTL | Content |
|---|---|---|
| `pyq:importance:{exam_id}` | 3600s | Serialized importance map |
| `pyq:insights:{tenant}:{student}` | 120s | GetPYQInsightsTool DTO |
| `pyq:pool:{exam}:{concept}:{v}` | 300s | Question id list |
| `pyq:stats:{exam_id}` | 3600s | concept_pyq_stats snapshot |

### 31.2 Invalidation

```
PYQDataChanged → DEL pyq:importance:*, pyq:pool:*, pyq:insights:* (tenant pattern)
FacultyWeightUpdated → DEL pyq:importance:{exam}, pyq:insights:{tenant}:*
```

---

## 32. Failure recovery

### 32.1 Partial batch ingest

Batch `status=partial`; rollback uncommitted draft questions; emit `PYQIngestionCompleted` with error manifest.

### 32.2 Importance recompute failure

Checkpoint in `importance_recompute_runs`; resume from last concept batch; previous `concepts.importance` remains until successful publish.

### 32.3 Event publish failure

Outbox sweeper retries; Learning Graph may temporarily serve stale Importance — acceptable eventual consistency (< 15 min SLO).

### 32.4 Mapping corruption

Admin tool `RebuildMappingsFromAudit(mapping_events)` — replay audit log to restore mappings snapshot.

### 32.5 Catalog rollback

```
RollbackCatalog(version=N):
  Restore pyq_questions + mappings snapshot from backup table
  catalog_version=N
  EMIT PYQDataChanged trigger=rollback
```

---

## 33. Performance requirements

### 33.1 Targets (10k students, ~500 concepts, ~5k PYQ questions)

| Operation | Target |
|---|---|
| Full Importance recompute | **≤ 5 min** |
| Student importance copy (LG) | **≤ 15 min** p95 batch |
| `GetPYQInsightsTool` cached | p95 **< 50ms** |
| `list_eligible_by_concept` | p95 **< 40ms** |
| Single question verify + publish | p95 **< 500ms** |
| Batch ingest 500 questions | **≤ 3 min** |

### 33.2 Storage estimates

| Entity | Rows (V1) |
|---|---|
| `pyq_questions` | ~5,000 |
| `pyq_mappings` | ~8,000 (multi-map) |
| `concept_pyq_stats` | ~500 |
| `student_pyq_insights` | 10k |

---

## 34. Observability

### 34.1 Metrics

| Metric | Type |
|---|---|
| `pyq_ingest_questions_total` | counter |
| `pyq_quarantine_total` | counter |
| `pyq_mapping_queue_depth` | gauge |
| `importance_recompute_duration_ms` | histogram |
| `pyq_unmapped_percentage` | gauge |
| `pyq_data_changed_events_total` | counter |

### 34.2 Alerts

- Unmapped verified questions > 5% → warn
- Importance recompute job failed → page
- License expiry within 30 days → notify admin

### 34.3 Explainability payload

Every `concepts.importance` update stores `components_json`:

```json
{ "F": 92, "T": 78, "E": 95, "W": 50, "raw": 83.65, "version": "importance_v1" }
```

Faculty UI renders breakdown — satisfies blueprint Rule 4.

---

## 35. Future AI-assisted mapping

### 35.1 V2 Mapping Assistant

- Input: question text + options
- Output: suggested `{concept_id, weight, confidence}`
- Auto-apply only if `confidence ≥ 0.85` AND concept `pyq_mappable`
- Else → `pyq_mapping_review_queue`

### 35.2 Eval harness

Mapping accuracy vs faculty gold set; target ≥ 90% primary concept match before auto-apply enabled.

### 35.3 Co-occurrence clustering (§15)

Unsupervised PYQ clusters to suggest `frequently_asked_with` edges — separate batch job.

---

## Appendix A — Importance component weight sensitivity

| Scenario | Adjustment |
|---|---|
| Pre-PYQ seed bootstrap | `IMP_WEIGHT_EXAM=0.60`, `IMP_WEIGHT_FACULTY=0.40`, others 0 |
| Institute-only mode | Increase `IMP_WEIGHT_FACULTY` via tenant config |
| Mains-focused batch | Mentor phase policy; optional boost `paper_weight(mains_*)` |

All adjustments via config — never code fork per tenant.

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `IMP_WEIGHT_FREQ` | 0.40 | §13 |
| `IMP_WEIGHT_TREND` | 0.20 | §13 |
| `IMP_WEIGHT_EXAM` | 0.25 | §13 |
| `IMP_WEIGHT_FACULTY` | 0.15 | §13 |
| `PYQ_RECENCY_LAMBDA` | 0.12 | §9 |
| `TRECENT_YEARS` | 5 | §10 |
| `TREND_FLOOR` | 0.5 | §10 |
| `TREND_CEIL` | 2.0 | §10 |
| `FACULTY_WEIGHT_NEUTRAL` | 50 | §12 |
| `NON_OPTIONAL_IMPORTANCE_FACTOR` | 0.9 | §14.3 |
| `IMPORTANCE_VERSION` | `importance_v1` | |
| `IMPORTANCE_FREQ_NORM` | `log` | §9.4 |
| `IMPORTANCE_FALLBACK_EXAM_REL` | true | §21.3 |
| `HIGH_IMPORTANCE_THRESHOLD` | 70 | aligns LG/Readiness |
| `PYQ_INSIGHTS_CACHE_TTL_SECONDS` | 120 | §31 |
| `PYQ_AUTO_MAP_CONFIDENCE_MIN` | 0.85 | §35 |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | §21 event handlers, importance copy, fallback |
| `MENTOR_AGENT_SPECIFICATION.md` | §26 GetPYQInsightsTool, planning signals |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | §23 PYQReadPort, pool invalidation |
| `REVISION_ENGINE_SPECIFICATION.md` | Indirect via importance on graph |
| `PREPARATION_TWIN_SPECIFICATION.md` | §25 Readiness recompute trigger |
| `EXAM_DOMAIN_SPECIFICATION.md` | §9 mapping model, PYQ_OF edges |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Exam Weight display bands R5 |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `EXAM_DOMAIN_SPECIFICATION.md` | PYQ entity §9; PYQ_OF §16; quarantine P6; pyq_mappable |
| `LEARNING_GRAPH_SPECIFICATION.md` | PYQ never writes graph scores; RefreshImportance on events §21 |
| `MENTOR_AGENT_SPECIFICATION.md` | GetPYQInsightsTool shape §26; pyq_high_yield_new; drill union |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | Read-only PYQ; PYQDataChanged cache invalidation |
| `REVISION_ENGINE_SPECIFICATION.md` | Priority uses importance from graph; mandatory high-yield |
| `PREPARATION_TWIN_SPECIFICATION.md` | PYQDataChanged partial rebuild |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | Importance = Exam Weight R5; not student gauge polarity |
| `MASTER_IMPLEMENTATION_PLAN.md` | S7 scope; D8 co-occurrence deferred; D12 licensing |
| Blueprint Rule 5 | Global Importance computed here; student copy via LG |
| Blueprint Rule 4 | components_json explainability §34.3 |
| Blueprint Rule 3 | AI mapping assistant V2 only with human verify V1 |

---

*End of PYQ Intelligence Specification v1.0*
