# PrepOS AI — Assessment Engine Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for Assessment bounded context
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`, `REVISION_ENGINE_SPECIFICATION.md` (v1.1), `PREPARATION_TWIN_SPECIFICATION.md`, `MENTOR_AGENT_SPECIFICATION.md`
Authoring lens: Principal Learning Scientist · Staff Backend Architect · Assessment Systems Designer · UPSC EdTech Domain Expert · Distributed Systems Architect

> **Scope.** This document defines the **Assessment Engine**: how assessments are created, attempted, scored, stored, and emitted as domain events that drive the Learning Graph, Preparation Twin, Mentor, and analytics. It covers MCQ drills, Prelims mocks, recall sessions (Revision integration), diagnostic onboarding, and the V2/V3 outline for Mains evaluation. It is the implementation contract for `assessments`, `assessment_attempts`, `assessment_responses`, `recall_sessions`, platform question bank tables, scoring pipeline, anti-gaming, read models, APIs, caching, and failure recovery.
>
> **Non-goals:** UI layout, marketing, sprint tasks, SQL DDL, LLM Mains rubric prompts (Assessment Agent), PYQ ingestion pipelines (PYQ Intelligence spec), payment/billing. Scoring **formulas** for Mastery components and Readiness sub-scores live in Scoring specs; **concept score columns** live in Learning Graph — Assessment **never writes graph scores directly**.
>
> **Core invariant:** the Assessment Engine is the **sole writer** of assessment evidence (attempts, responses, recall sessions). It **reads** Learning Graph state for question selection and **emits** `AssessmentCompleted` (and `AnswerEvaluated` for Mains) so the **Learning Graph Service alone** updates `student_concept_progress`.

---

## 0. Canonical requirements map

This document is the authoritative answer to the 32 required areas:

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and bounded context | §1 |
| 2 | Ownership boundaries | §2 |
| 3 | Assessment type taxonomy | §3 |
| 4 | Question bank architecture | §4 |
| 5 | Question–concept tagging model | §5 |
| 6 | MCQ drill question selection | §6 |
| 7 | Prelims mock assembly | §7 |
| 8 | Diagnostic / onboarding assessment | §8 |
| 9 | Assessment aggregate lifecycle | §9 |
| 10 | Attempt lifecycle | §10 |
| 11 | Response capture model | §11 |
| 12 | Recall session lifecycle (Revision) | §12 |
| 13 | Attempt-level scoring pipeline | §13 |
| 14 | Concept-level evidence aggregation | §14 |
| 15 | Anti-gaming architecture | §15 |
| 16 | Confidence marking model | §16 |
| 17 | Guessing detection | §17 |
| 18 | Question deduplication policy | §18 |
| 19 | Event-driven architecture | §19 |
| 20 | `AssessmentCompleted` event contract | §20 |
| 21 | `AnswerEvaluated` event (Mains V2+) | §21 |
| 22 | Integration with Learning Graph | §22 |
| 23 | Integration with Preparation Twin | §23 |
| 24 | Integration with Mentor Agent | §24 |
| 25 | Integration with Revision Engine | §25 |
| 26 | Integration with Scoring Engine | §26 |
| 27 | Mains evaluation architecture (V2/V3) | §27 |
| 28 | Read models | §28 |
| 29 | Database schemas | §29 |
| 30 | API contracts | §30 |
| 31 | Caching strategy | §31 |
| 32 | Failure recovery | §32 |
| 33 | Performance requirements | §33 |
| 34 | Observability | §34 |
| 35 | Future AI Assessment Agent | §35 |
| 36 | Consistency checklist | Appendix D |

---

## 1. Purpose and bounded context

### 1.1 What the Assessment Engine is

The Assessment Engine is PrepOS's **evidence capture and scoring system** for objective and descriptive practice. It transforms student answers into **auditable, concept-tagged evidence** that downstream engines consume to update knowledge state, readiness, and guidance.

```
Learning Graph (read)           Assessment Engine (this spec)          Downstream (event consumers)
─────────────────────           ───────────────────────────          ────────────────────────────
mastery, retention,      ──►    question selection                   Learning Graph (MCQ/Mains mastery)
importance, node_state          attempt + response storage           Preparation Twin (MCQSub, mocks)
weak frontier                   scoring + anti-gaming                  Mentor (GetAssessmentGapsTool)
catalog / PYQ mappings          recall sessions                        Revision (recall_session_id validation)
                                assessments / attempts tables        Analytics / WebSocket
                                      │
                                      ▼
                               AssessmentCompleted ──► Learning Graph Service (sole score writer)
                               AnswerEvaluated     ──► Learning Graph + Twin (Mains channel)
```

### 1.2 What the Assessment Engine is NOT

| Misconception | Reality |
|---|---|
| Learning Graph writer | **Never** updates `student_concept_progress`; emits events only |
| Revision scheduler | Creates **recall sessions**; Revision Engine owns `revisions` queue |
| Mentor recommender | Mentor **assigns** assessment tasks; Assessment **executes** them |
| PYQ Intelligence | Consumes `pyq_questions` / mappings; PYQ ingestion is a separate bounded context |
| Scoring formula owner | Invokes Scoring **pure functions**; formulas live in Scoring specs |
| Chat / explanation agent | Mains **evaluation** narration routes to Assessment Agent (V2+); not this engine's core |

### 1.3 Bounded context (DDD)

```
┌─────────────────────────────────────────────────────────────────┐
│              Assessment Context (this spec)                      │
│  AssessmentService · QuestionSelector · ScoringPipeline          │
│  RecallSessionService · AntiGamingGuard                          │
│  assessments · assessment_attempts · assessment_responses        │
│  recall_sessions · recall_prompts · platform_questions         │
└───────────────┬─────────────────────────────────────────────────┘
                │ read ports              │ domain events
    ┌───────────┼───────────┬─────────────┴──────────┬────────────┐
    ▼           ▼           ▼                        ▼            ▼
 Learning     Exam        PYQ catalog              Revision      Twin/Mentor
 Graph        Domain      (read-only)              (recall link) (read models)
```

**Anti-corruption:** graph access via `LearningGraphReadPort`; never import `ConceptProgressRepository` from Learning Graph module.

### 1.4 UPSC preparation model (domain logic embedded)

| Dimension | Assessment behavior |
|---|---|
| **Prelims GS Paper I** | Primary V1 surface: MCQ drills + full mocks (100 Q, negative marking semantics) |
| **CSAT Paper II** | Tracked separately; qualifying-only; lower weight in Readiness until configured |
| **Mains GS1–4 + Essay** | V2/V3: descriptive submission + async `AnswerEvaluated` |
| **Concept-first** | Every scored response maps to ≥1 `concept_id` with explicit weight (EXAM_DOMAIN P1) |
| **High-yield targeting** | Selection prioritizes `importance ≥ 70` weak concepts |
| **Negative marking awareness** | Guessing detection feeds Twin `guessing_rate`; Mentor reduces risky drill volume |
| **PYQ alignment** | Platform + PYQ questions share tagging model; PYQ-mapped weak concepts get drill priority |
| **Stage routing** | `prelims_relevance` / `mains_relevance` gate question–concept fit |

### 1.5 Success criteria

1. `POST /assessments` → `POST /assessments/{id}/submit` → `AssessmentCompleted` → Learning Graph mastery update within **p95 < 500ms** (MCQ sync path).
2. **Zero** Assessment service writes to `student_concept_progress`.
3. Same student + same selection config + same catalog version ⇒ **deterministic question multiset** (given fixed random seed in config).
4. `GetAssessmentGapsTool` backed by Assessment read models with **p95 < 100ms** (cached).
5. `CompleteRevision(recall_session_id=...)` succeeds only when recall session is **valid** per §12.
6. Repeated-question gaming reduces mastery contribution per Scoring dedupe rules (§18).

---

## 2. Ownership boundaries

### 2.1 Write ownership matrix

| Data | Sole writer | Assessment relationship |
|---|---|---|
| `assessments` | **Assessment Service** | Authoritative assessment aggregate |
| `assessment_attempts` | **Assessment Service** | One row per sitting |
| `assessment_responses` | **Assessment Service** | Per-question evidence |
| `recall_sessions` | **Assessment Service** | Revision recall sittings |
| `recall_prompts` / `recall_responses` | **Assessment Service** | Graded recall items |
| `platform_questions` | **Assessment Service** (V1) | Curated MCQ bank; PYQ rows owned by PYQ module |
| `student_concept_progress` | Learning Graph Service | **Read via port only** |
| `preparation_twins` | Twin Builder | **Never written** |
| `revisions` | Revision Engine | **Never written**; recall_session_id validated on read |
| `mentor_plans` | Mentor Service | **Never written** |
| `pyq_questions`, `pyq_mappings` | PYQ Intelligence (future) | **Read only** |

### 2.2 Forbidden operations

1. Assessment worker calling `ConceptProgressRepository.save_node()` or any graph mutation API.
2. Assessment patching `preparation_twins.assessment_profile` directly (Twin rebuilds from events).
3. Assessment creating/updating `revisions` rows or calling `CompleteRevision`.
4. Accepting submit without persisting all responses atomically with attempt row.
5. Emitting `AssessmentCompleted` before scoring pipeline completes and outbox row is durable.
6. Tagging responses to deprecated or quarantined concepts without explicit faculty override flag.

### 2.3 Evidence as source of truth

Assessment evidence stores (`assessment_responses`, `recall_responses`) are **authoritative** for replay and Learning Graph recompute (`LEARNING_GRAPH_SPECIFICATION.md` §14.3). Domain events are the **integration contract**; event log is audit + async fan-out.

---

## 3. Assessment type taxonomy

### 3.1 V1 assessment types

| `assessment_type` | Purpose | Question count | Scoring path | LG channel |
|---|---|---|---|---|
| `mcq_drill` | Targeted weak-concept practice | 20–30 (config) | Sync on submit | MCQ mastery + confidence |
| `prelims_mock` | Full GS Paper I simulation | 100 | Sync on submit | MCQ mastery; mock anchor for prediction |
| `recall_session` | Revision recall sitting | 1–20 prompts | Sync per prompt or batch | Indirect — via `RevisionCompleted` |
| `diagnostic` | Onboarding cold-start bootstrap | 40 | Sync on submit | MCQ mastery + initial rating |
| `ca_quiz` | CA-linked MCQ (V1.1 optional) | 10–15 | Sync | MCQ + CASub inputs |

### 3.2 V2/V3 assessment types (outline)

| `assessment_type` | Purpose | Scoring path | LG channel |
|---|---|---|---|
| `mains_descriptive` | GS answer writing | Async `AnswerEvaluated` | Mains mastery (30%) |
| `essay` | Essay paper practice | Async `AnswerEvaluated` | WritingSub |
| `csat_drill` | CSAT qualifying practice | Sync | MCQ (CSAT-weighted rollup) |

### 3.3 Type-specific flags

| Field | Applies to | Meaning |
|---|---|---|
| `is_timed` | mock, diagnostic | Enforces per-section or total timer |
| `negative_marking_enabled` | prelims_mock, mcq_drill | UPSC Prelims: −⅓ for wrong |
| `confidence_marking_required` | mcq_drill, diagnostic | Blocks submit if any response missing confidence |
| `allows_pause` | mcq_drill | Student may resume within TTL |
| `mock_anchor` | prelims_mock | Counts toward `PRELIMS_MOCK_THRESHOLD` (Scoring v1.1 §5.1) |
| `linked_revision_ids` | recall_session | Optional FK list to Revision rows |

### 3.4 Assessment status machine

```
                    ┌──────────┐
         create     │  draft   │  questions selected, not yet started
        ──────────► │          │
                    └────┬─────┘
                         │ start / first response
                         ▼
                    ┌──────────┐
                    │  active  │  student may answer
                    └────┬─────┘
                         │
           ┌─────────────┼─────────────┐
           │ all Q done  │ timeout     │
           ▼             ▼             │
    ┌──────────┐   ┌──────────┐       │
    │ submitted│   │ expired  │       │
    └────┬─────┘   └──────────┘       │
         │ scoring                     │
         ▼                             │
    ┌──────────┐                       │
    │ scoring  │                       │
    └────┬─────┘                       │
         │                             │
    ┌────┴────┐                        │
    ▼         ▼                        │
┌──────────┐ ┌────────┐              │
│ completed│ │ failed │◄─────────────┘
└──────────┘ └────────┘
```

| Status | Student-visible | Mutable |
|---|---|---|
| `draft` | No (or "preparing") | Yes — question list |
| `active` | Yes | Responses append-only |
| `submitted` | Yes (processing) | No |
| `scoring` | Yes (processing) | No |
| `completed` | Yes (results) | No |
| `failed` | Yes (retry offered) | No |
| `expired` | Yes | No |

---

## 4. Question bank architecture

### 4.1 Question sources (V1)

| Source | Table | Owner | Use |
|---|---|---|---|
| **Platform MCQ bank** | `platform_questions` | Assessment | Drills, diagnostic, mock filler |
| **PYQ bank** | `pyq_questions` | PYQ module (read) | High-fidelity mocks, PYQ-aligned drills |
| **Generated recall prompts** | `recall_prompts` | Assessment | Revision recall (not full MCQ) |

### 4.2 Platform question entity — `platform_questions`

| Column | Type | Description |
|---|---|---|
| `question_id` | UUID PK | |
| `tenant_id` | UUID | null = global catalog |
| `exam_id` | string | e.g. `upsc_cse` |
| `question_text` | text | Rich text / LaTeX safe |
| `question_type` | enum | `mcq` |
| `options_json` | JSONB | `[{id, text}]` length 4 typical |
| `correct_option_id` | string | |
| `explanation` | text nullable | Shown post-submit |
| `difficulty` | int 1–5 | Feeds recency-difficulty weighting |
| `source` | enum | `curated`, `faculty`, `imported` |
| `status` | enum | `active`, `deprecated`, `quarantined` |
| `catalog_version` | int | Invalidates selection cache |
| `created_at` | timestamptz | |

### 4.3 Question eligibility rules

```
EligibleQuestion(q, student, assessment_type):
  q.status == 'active'
  AND q.exam_id == student.exam_id
  AND EXISTS mapping(q, concept) WHERE concept.status == 'active'
  AND FOR ALL mapped concepts C:
        IF assessment_type IN ('mcq_drill','prelims_mock','diagnostic'):
           C.prelims_relevance > 0 OR mapping tagged 'csat_only'
        IF assessment_type == 'mains_descriptive':  // V2+
           C.mains_relevance > 0
  AND NOT IsQuestionBlocked(q, student)   // faculty block list
```

### 4.4 Quarantine policy

Questions failing automated or manual QA enter `quarantined`:

- Never selected by default algorithms.
- Faculty may force-include for batch assessments with audit flag.
- Quarantined PYQ rows remain in `pyq_questions` but excluded from `EligibleQuestion`.

---

## 5. Question–concept tagging model

### 5.1 Mapping tables

**Platform mappings — `platform_question_mappings`**

| Column | Type | Description |
|---|---|---|
| `question_id` | UUID FK | |
| `concept_id` | string FK | EXAM_DOMAIN slug |
| `weight` | decimal(4,3) | Share of question; Σ weights = 1.0 ±0.01 |
| `mapping_role` | enum | `primary`, `secondary` |

**PYQ mappings — `pyq_mappings`** (read-only for Assessment; defined in EXAM_DOMAIN §9)

Same shape; owned by PYQ Intelligence module.

### 5.2 Tagging invariants (EXAM_DOMAIN P6)

1. Every scorable question MUST map to ≥1 concept with Σ weights = 1.0.
2. **`primary`**: weight ≥ 0.50 typically; drives drill targeting labels.
3. Cross-subject mapping allowed (e.g. GST → economy + polity).
4. Mis-tagged questions detected by `prelims_relevance` / `mains_relevance` mismatch → auto-quarantine job.
5. Unmapped PYQ questions remain in quarantine pool — never silently guessed to nearest concept.

### 5.3 Response-level concept attribution

When a student answers question `q` mapped to concepts `{C_i, w_i}`:

```
FOR each concept C_i:
  attributed_correct_i = is_correct ? w_i : 0
  attributed_wrong_i   = is_correct ? 0 : w_i
  time_share_i         = w_i * response_time_sec
  confidence_i         = student_confidence * w_i   // if enabled
```

Partial credit on multi-concept questions uses weights only — no LLM inference in V1.

---

## 6. MCQ drill question selection

### 6.1 Inputs

| Input | Source | Purpose |
|---|---|---|
| `target_concepts[]` | Mentor plan / API request / gap tool | Primary filter |
| `question_count` | Config default 30 | Size |
| `exclude_question_ids` | Recent attempts (§18) | Dedupe |
| Graph weak frontier | `LearningGraphReadPort` | Fallback targets |
| PYQ weak high-yield | `PYQReadPort` (future) | Enrichment |
| `catalog_version` | Exam Domain | Cache key |

### 6.2 Algorithm `SelectMCQDrillQuestions`

```
INPUT:  tenant_id, student_id, exam_id, target_concepts[], question_count, seed
1.  IF target_concepts empty:
      target_concepts = GetAssessmentGaps(student).weak_concepts TOP 15 by (importance × error_rate)
2.  candidates = []
3.  FOR each concept C in target_concepts (sorted by priority DESC):
        pool_C = EligibleQuestions(C, types=[platform, pyq], limit=50)
        pool_C = filter pool_C by DedupePolicy(student, pool_C)
        pick = weighted_sample(pool_C, weight_fn = f(difficulty, pyq_flag, freshness))
        candidates.extend pick until question_count reached OR pools exhausted
4.  IF len(candidates) < question_count:
        backfill from high-importance rated concepts with error_rate > 0.3
5.  IF still short: backfill random eligible from student's weakest subject rollup
6.  Shuffle with deterministic seed; assign sequence_number 1..N
7.  Persist assessment row type=mcq_drill status=draft with selection_metadata_json
8.  RETURN assessment_id
```

### 6.3 Priority score for concept targeting

Aligns with Mentor §9.3:

```
concept_priority(C) = importance(C) × error_rate(C) × stage_boost(C)

error_rate(C) = wrong_weighted / max(1, total_weighted)   // rolling 90d window
stage_boost(C) = 1.15 IF days_to_exam < 90 AND C.prelims_relevance >= 85 ELSE 1.0
```

### 6.4 Subject diversity guard

When `target_concepts` not specified:

```
Ensure ≥3 subjects represented IF question_count >= 20
Cap per-subject questions at ceil(question_count / 4) unless single-subject drill requested
```

### 6.5 Difficulty mix (UPSC-realistic)

| Band | Share of drill |
|---|---|
| difficulty 1–2 | 20% |
| difficulty 3 | 50% |
| difficulty 4–5 | 30% |

Relax constraints if pool insufficient; log `selection_relaxation` in metadata.

---

## 7. Prelims mock assembly

### 7.1 Mock specification

| Property | Value |
|---|---|
| `assessment_type` | `prelims_mock` |
| `question_count` | 100 |
| `duration_minutes` | 120 |
| `negative_marking_enabled` | true |
| `mock_anchor` | true |
| `marks_per_question` | 2 |
| `negative_fraction` | 1/3 |

### 7.2 Algorithm `AssemblePrelimsMock`

```
INPUT:  student_id, exam_id, mock_template_id optional
1.  template = mock_template_id OR default upsc_cse_gs1_v1
2.  subject_quotas = template.subject_quotas   // e.g. Polity 14, History 14, ...
3.  FOR each subject S in quotas:
        pick quota[S] questions from PYQ pool (last 10 years preference)
        THEN platform pool if PYQ short
        enforce difficulty mix per subject (template)
4.  Apply global DedupePolicy vs student's last 2 mocks
5.  Validate 100 questions; persist assessment mock_anchor=true
6.  Set scoring_profile = prelims_mock_v1 (negative marking net score)
```

### 7.3 Mock score (attempt-level)

Net score for UPSC Prelims semantics:

```
raw_correct = count(is_correct)
raw_wrong   = count(NOT is_correct AND answered)
net_score   = 2 * raw_correct - (2/3) * raw_wrong
max_score   = 200
accuracy    = raw_correct / question_count
```

Stored on `assessment_attempts.score`, `accuracy`, `net_score`, `max_score`.

### 7.4 Prediction anchor

When `mock_anchor=true` AND attempt `status=completed`:

- Twin updates `academic.assessment.prelims_mocks` (`PREPARATION_TWIN_SPECIFICATION.md` §4).
- Scoring v1.1 §5.1 Prelims prediction display gate evaluates `count >= PRELIMS_MOCK_THRESHOLD` (default **1** full mock; config may require 2 for high trust).

---

## 8. Diagnostic / onboarding assessment

### 8.1 Purpose

Solve cold-start (`MASTER_IMPLEMENTATION_PLAN.md` G12 / D16): bootstrap initial mastery signal before Mentor plans have graph history.

### 8.2 Algorithm `CreateDiagnosticAssessment`

```
INPUT:  student_id on onboarding complete (optional flag diagnostic_enabled)
1.  Select 40 questions stratified across 8 core subjects (5 each)
2.  Prefer importance ≥ 70 concepts spanning syllabus breadth
3.  confidence_marking_required = true
4.  is_timed = false (reduces onboarding friction)
5.  Tag assessment metadata onboarding=true
```

### 8.3 Post-diagnostic behavior

On `AssessmentCompleted`:

- Learning Graph flips targeted concepts `unrated → rated` where evidence exists.
- Mentor first plan scheduled with `diagnostic_bootstrap=true` in reasoning.
- Twin `coverage` denominators become meaningful faster.

Student may skip diagnostic; system uses conservative defaults (Mentor empty-data policy).

---

## 9. Assessment aggregate lifecycle

### 9.1 Create flow

```
CreateAssessment(request):
1.  Authorize student + tenant
2.  Resolve assessment_type + parameters
3.  Invoke type-specific selector (§6–§8)
4.  INSERT assessments row status=draft
5.  INSERT assessment_questions join rows (ordered)
6.  RETURN assessment_id + question_count (no answers)
```

### 9.2 Start flow

```
StartAssessment(assessment_id):
1.  VALIDATE status IN (draft, active)
2.  IF draft: status=active, started_at=now
3.  CREATE assessment_attempt row status=in_progress (if not exists)
4.  RETURN attempt_id + questions (without correct_option_id)
```

### 9.3 Idempotency

- `POST /assessments` with `Idempotency-Key` header: return existing assessment if same key within 24h.
- One **active** attempt per assessment at a time; resume returns same attempt if `allows_pause`.

---

## 10. Attempt lifecycle

### 10.1 Attempt state machine

```
in_progress → submitted → scored → completed
                     ↘ failed
in_progress → abandoned (optional cleanup)
```

### 10.2 Attempt entity — `assessment_attempts`

| Column | Type | Description |
|---|---|---|
| `attempt_id` | UUID PK | |
| `assessment_id` | UUID FK | |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `status` | enum | see §10.1 |
| `started_at` | timestamptz | |
| `submitted_at` | timestamptz nullable | |
| `time_taken_sec` | int | Wall clock |
| `score` | decimal nullable | Type-specific |
| `accuracy` | decimal(5,4) nullable | 0–1 |
| `net_score` | decimal nullable | Mock net |
| `max_score` | decimal nullable | |
| `guessing_rate` | decimal(5,4) nullable | §17 |
| `avg_confidence` | decimal(5,2) nullable | 1–5 scale |
| `scoring_version` | string | e.g. `attempt_score_v1` |
| `selection_seed` | int | Reproducibility |

### 10.3 Submit flow

```
SubmitAssessment(assessment_id, attempt_id, responses[]):
1.  VALIDATE attempt.status == in_progress
2.  VALIDATE all required questions answered (or explicit skip policy)
3.  IF confidence_marking_required: VALIDATE all responses have confidence
4.  BEGIN TRANSACTION
5.  UPSERT assessment_responses (immutable after submit)
6.  attempt.status = submitted; submitted_at = now
7.  COMMIT
8.  ENQUEUE ScoringPipelineJob(attempt_id) OR run sync for MCQ
9.  RETURN 202 Accepted { attempt_id, status: submitted }
```

### 10.4 Abandon / expire

| Case | Handling |
|---|---|
| Pause TTL exceeded (7 days) | `attempt.status=abandoned`; assessment `expired` |
| Mock timer exceeded | Auto-submit answered questions; mark unanswered wrong |
| Client crash mid-attempt | Resume via `GET /assessments/{id}` in_progress attempt |

---

## 11. Response capture model

### 11.1 Response entity — `assessment_responses`

| Column | Type | Description |
|---|---|---|
| `response_id` | UUID PK | |
| `attempt_id` | UUID FK | |
| `question_id` | UUID | platform or pyq id |
| `question_source` | enum | `platform`, `pyq` |
| `sequence_number` | int | Order in assessment |
| `selected_option_id` | string nullable | |
| `is_correct` | bool | Computed at score time |
| `response_time_sec` | int | Per-question timer |
| `confidence` | int nullable | 1–5 self-rating |
| `is_guess_flag` | bool | System or student |
| `is_fast_wrong` | bool | §17 |
| `concept_attributions_json` | JSONB | `[{concept_id, weight, correct_share}]` |
| `scored_at` | timestamptz | |

### 11.2 Confidence scale

| Value | Label | Used in Confidence score |
|---|---|---|
| 1 | Not sure at all | Low |
| 2 | Somewhat unsure | |
| 3 | Neutral | |
| 4 | Fairly confident | |
| 5 | Very confident | High |

### 11.3 Immutable evidence

Post-submit responses are **append-only corrections forbidden** except admin audit replay tools. Corrections create new `assessment_attempt` with `supersedes_attempt_id` (faculty-only V2).

---

## 12. Recall session lifecycle (Revision integration)

### 12.1 Purpose

Revision Engine requires a validated `recall_session_id` on `CompleteRevision` (`REVISION_ENGINE_SPECIFICATION.md` §11.1). Assessment Engine owns recall evidence.

### 12.2 Recall session entity — `recall_sessions`

| Column | Type | Description |
|---|---|---|
| `recall_session_id` | UUID PK | |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `concept_id` | string | Single concept per session (V1) |
| `revision_id` | UUID nullable | Linked revision row |
| `session_type` | enum | `free_recall`, `cued_recall`, `mcq_recall` |
| `status` | enum | `active`, `completed`, `abandoned` |
| `started_at` | timestamptz | |
| `completed_at` | timestamptz nullable | |
| `prompt_count` | int | |
| `graded_prompt_count` | int | Must be ≥1 for valid completion |

### 12.3 Prompt / response tables

**`recall_prompts`**: `prompt_id`, `recall_session_id`, `prompt_text`, `sequence`, `concept_id`

**`recall_responses`**: `prompt_id`, `recall_grade` (`forgot|hard|good|easy`), `response_time_sec`, `optional_text`

### 12.4 Lifecycle

```
StartRecallSession(revision_id optional, concept_id):
1.  IF revision_id: VALIDATE revision.status IN (scheduled, in_progress)
2.  CREATE recall_session status=active
3.  Generate 1–3 prompts for concept (template bank or LLM-free cues from catalog)
4.  RETURN recall_session_id

GradeRecallPrompt(recall_session_id, prompt_id, recall_grade):
1.  UPSERT recall_response
2.  INCREMENT graded_prompt_count
3.  IF all prompts graded OR student finishes:
       recall_session.status = completed
       EMIT RecallSessionCompleted (internal)
4.  Student/UI calls Revision API CompleteRevision with recall_session_id + aggregate recall_grade
```

### 12.5 Aggregate recall grade for Revision

Revision completion accepts one `recall_grade`. Derive from prompts:

```
IF any prompt == 'forgot': aggregate = 'forgot'
ELIF majority 'hard': aggregate = 'hard'
ELIF any 'easy' AND none 'forgot': aggregate = 'easy'
ELSE: aggregate = 'good'
```

### 12.6 Validation contract (Revision Engine consumer)

```
ValidateRecallSession(recall_session_id, revision_id, concept_id):
  session = load(recall_session_id)
  RETURN session.status == 'completed'
     AND session.graded_prompt_count >= 1
     AND session.concept_id == concept_id
     AND (session.revision_id IS NULL OR session.revision_id == revision_id)
     AND session.completed_at >= now - 24 hours
```

### 12.7 MCQ recall variant

`session_type=mcq_recall`: single MCQ question on concept; grade mapped:

| Outcome | `recall_grade` |
|---|---|
| Wrong or confidence 1–2 | `forgot` or `hard` |
| Correct + slow | `good` |
| Correct + fast + confidence ≥4 | `easy` |

Emits `AssessmentCompleted` with `channel=recall` **only** for mastery analytics on optional config; default path is **`RevisionCompleted` only** (recall does not double-update MCQ mastery unless `RECALL_MCQ_UPDATES_MASTERY=true`).

---

## 13. Attempt-level scoring pipeline

### 13.1 Pipeline overview

```
SubmitAssessment
      │
      ▼
┌─────────────────┐
│ ScoreResponses  │  mark is_correct; concept attributions
└────────┬────────┘
         ▼
┌─────────────────┐
│ AntiGamingPass  │  guessing flags, fast-wrong, dedupe weights
└────────┬────────┘
         ▼
┌─────────────────┐
│ AggregateAttempt│  accuracy, net_score, guessing_rate
└────────┬────────┘
         ▼
┌─────────────────┐
│ BuildConcept    │  concept_scores[] for event payload
│ Evidence        │
└────────┬────────┘
         ▼
┌─────────────────┐
│ Outbox          │  AssessmentCompleted durable
└────────┬────────┘
         ▼
   Publish event → Learning Graph worker (sync MCQ)
                 → Twin debounced rebuild
                 → Mentor cache invalidation
                 → WebSocket assessment_complete
```

### 13.2 Scoring versions

| Profile | Used for |
|---|---|
| `mcq_simple_v1` | Drills — accuracy only |
| `prelims_mock_v1` | Negative marking net |
| `diagnostic_v1` | Same as mcq_simple + bootstrap flag |
| `mains_rubric_v1` | V2 async |

### 13.3 Sync vs async

| Channel | Path | SLA |
|---|---|---|
| MCQ drill / mock / diagnostic | **Sync** in API worker or immediate Celery | p95 < 300ms scoring |
| Mains descriptive | **Async** Celery + AI eval | p95 < 60s (V2 target) |
| Recall session | Sync on completion | p95 < 100ms |

---

## 14. Concept-level evidence aggregation

### 14.1 Purpose

Learning Graph `ApplyMasteryUpdate` loads evidence aggregates per concept from Assessment stores (`LEARNING_GRAPH_SPECIFICATION.md` §8.1). Assessment maintains rollups for fast reads.

### 14.2 Per-concept MCQ component inputs (Scoring v1.0 §2.3.1)

For each `(student, concept)`:

```
mcq_component = 100 · recency_difficulty_weighted_accuracy

WHERE for each response r attributed to concept C:
  w_recency(r) = exp(-λ · days_since(r))          // λ = MCQ_RECENCY_LAMBDA default 0.05
  w_diff(r)    = DIFFICULTY_WEIGHT[r.difficulty]   // {1:0.8, 2:0.9, 3:1.0, 4:1.1, 5:1.2}
  w_dedupe(r)  = DedupeWeight(student, r.question_id)   // §18
  w_guess(r)   = 1.0 IF NOT r.is_fast_wrong ELSE GUESS_WEIGHT  // default 0.5

  effective_weight(r) = w_recency · w_diff · w_dedupe · w_guess · r.concept_weight

numerator   = Σ effective_weight(r) · is_correct
denominator = Σ effective_weight(r)
mcq_component = 100 · numerator / max(denominator, ε)
```

### 14.3 Evidence counters persisted

Materialized in `student_concept_mcq_evidence` (read model, Assessment-owned):

| Column | Purpose |
|---|---|
| `weighted_correct` | Numerator term |
| `weighted_total` | Denominator term |
| `n_mcq` | Raw attempt count |
| `n_unique_questions` | Dedupe analytics |
| `last_mcq_at` | Recency |
| `error_rate_90d` | Gap tool |

Learning Graph may cache these values but **recomputes mastery** via Scoring functions on event apply.

### 14.4 `concept_scores[]` in event payload

Built at end of scoring pipeline:

```json
{
  "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
  "mcq_component": 68.5,
  "n_new_responses": 3,
  "weighted_correct_delta": 2.4,
  "weighted_total_delta": 3.1,
  "confidence_delta": 4.2,
  "overconfidence_signal": false
}
```

---

## 15. Anti-gaming architecture

### 15.1 Threat model

| Threat | Mitigation |
|---|---|
| Rapid random clicking | Fast-wrong detection (§17) |
| Re-answering same questions | Dedupe weights (§18) |
| Inflated self-confidence | Confidence feeds Weakness overconfidence; not displayed (v1.1 R4) |
| Mock score farming | Mock anchor limits + mock dedupe window |
| Recall click-through | Minimum graded prompts + time floor (§12) |
| Item harvesting | Explanation only post-submit; option shuffle per attempt |

### 15.2 Option shuffle

Each attempt stores `option_order_json` per question — correct answer position not leaked across students via static ordering.

### 15.3 Rate limits

| Action | Limit |
|---|---|
| `POST /assessments` | 20 / student / hour |
| Submit mock | 2 / student / day |
| Recall session start | 60 / student / hour |

### 15.4 Anomaly flags

`assessment_attempts.anomaly_flags_json`:

- `guessing_spike` — guessing_rate > 0.35
- `speed_anomaly` — avg time < 5s on drill
- `perfect_repeat` — same question bank repeated with 100% accuracy (investigate)

Flags do not block scoring V1; feed faculty analytics and optional Mentor intervention.

---

## 16. Confidence marking model

### 16.1 Engine role (Scoring v1.0 §13)

Confidence is computed per concept from:

| Signal | Weight |
|---|---|
| Self-assessment (1–5 mapped 0–100) | 0.50 |
| Response speed vs cohort median | 0.25 |
| Consistency (variance of confidence across attempts) | 0.25 |

Assessment supplies **self-assessment** and **speed** raw signals; Learning Graph applies formula on `AssessmentCompleted`.

### 16.2 Speed normalization

```
speed_score(r) = clamp(1 - (response_time_sec / cohort_median_sec[C.difficulty]), 0, 1) · 100
```

Cohort medians refreshed nightly per `(exam_id, difficulty)`.

### 16.3 Overconfidence linkage

Learning Graph sets `overconfidence_flag` when `confidence − mastery ≥ 25 AND mastery < 70` (Scoring v1.1 §2.4). Assessment does not compute flag — only supplies inputs.

---

## 17. Guessing detection

### 17.1 Fast-wrong heuristic

```
is_fast_wrong(r) =
  r.is_correct == false
  AND r.response_time_sec < GUESSING_TIME_THRESHOLD_SEC   // default 8
  AND r.confidence <= 2 OR r.is_guess_flag == true
```

### 17.2 Guessing rate (attempt-level)

```
guessing_rate = count(is_fast_wrong) / count(answered)
```

Stored on `assessment_attempts.guessing_rate`; rolled into Twin `academic.assessment.mcq.guessing_rate` (30d/90d weighted mean).

### 17.3 Negative marking risk (Twin)

```
negative_marking_risk = clamp(0.6 · guessing_rate + 0.4 · wrong_on_high_confidence_rate, 0, 1)

wrong_on_high_confidence = wrong responses WHERE confidence >= 4
```

Mentor `GetAssessmentGapsTool.guessing_rate_elevated = true` when `guessing_rate_30d > GUESSING_ELEVATED_THRESHOLD` (default **0.18**).

---

## 18. Question deduplication policy

### 18.1 Selection-time dedupe

Exclude questions answered correctly in last **`QUESTION_DEDUPE_WINDOW_DAYS`** (default **30**) from new drills unless pool exhausted.

```
DedupePolicy(student, pool):
  recent_mastered = question_ids WHERE last_correct_within(30d)
  RETURN pool - recent_mastered (unless backfill mode)
```

### 18.2 Scoring-time dedupe (Scoring v1.0 §2.3.1 anti-gaming)

Repeated attempts on same `question_id`:

| Occurrence within window | Weight multiplier |
|---|---|
| 1st | 1.0 |
| 2nd | 0.25 |
| 3rd+ | 0.10 |

Prevents mastery inflation from cycling known items.

### 18.3 Mock dedupe

Prelims mocks exclude questions appearing in student's last **2** completed mocks (question-level), not just last 30 days.

---

## 19. Event-driven architecture

### 19.1 Events emitted

| Event | When | Sync/async |
|---|---|---|
| **`AssessmentSubmitted`** | Attempt submitted (pre-score) | sync |
| **`AssessmentCompleted`** | Scoring done; outbox committed | sync (MCQ) |
| **`AssessmentScoringFailed`** | Pipeline error | async |
| **`RecallSessionCompleted`** | Recall session graded | sync |
| **`AnswerEvaluated`** | Mains AI/faculty eval done | async |
| **`DiagnosticCompleted`** | Diagnostic assessment completed | sync (subtype) |

### 19.2 Events consumed

| Event | Action |
|---|---|
| `StudentRegistered` | Pre-provision diagnostic offer flag |
| `DomainCatalogUpdated` | Invalidate question selection cache |
| `PYQDataChanged` | Invalidate PYQ pools |
| `RevisionStarted` | Optional link recall_session placeholder |

### 19.3 Outbox pattern

```
1.  Score attempt in transaction
2.  INSERT assessment_outbox(event_type, payload, status=pending)
3.  COMMIT
4.  Publisher delivers to bus + marks published
5.  Learning Graph consumer ACK with processed_events idempotency
```

### 19.4 Ordering

| Scope | Guarantee |
|---|---|
| Per `(student_id, attempt_id)` | Single `AssessmentCompleted` |
| Per `(student_id, concept_id)` | Events processed serially by Learning Graph (LG §7.4) |
| Cross-student | No ordering required |

---

## 20. `AssessmentCompleted` event contract

### 20.1 Payload schema (version 1)

```json
{
  "event_id": "uuid",
  "event_version": 1,
  "event_type": "AssessmentCompleted",
  "tenant_id": "uuid",
  "student_id": "uuid",
  "exam_id": "upsc_cse",
  "assessment_id": "uuid",
  "attempt_id": "uuid",
  "assessment_type": "mcq_drill",
  "channel": "mcq",
  "occurred_at": "2026-06-18T10:30:00Z",
  "correlation_id": "uuid",
  "scoring_version": "mcq_simple_v1",
  "attempt_summary": {
    "accuracy": 0.66,
    "net_score": null,
    "guessing_rate": 0.12,
    "time_taken_sec": 1840,
    "question_count": 30,
    "mock_anchor": false
  },
  "concept_scores": [
    {
      "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
      "mcq_component": 68.5,
      "n_new_responses": 3,
      "weighted_correct_delta": 2.4,
      "weighted_total_delta": 3.1,
      "confidence_delta": 4.2
    }
  ],
  "diagnostic_bootstrap": false
}
```

### 20.2 Channel enum

| `channel` | LG handler |
|---|---|
| `mcq` | MCQ mastery + confidence |
| `mains` | Mains mastery component |
| `recall` | Optional MCQ update if config enabled |
| `ca` | CASub inputs (V2) |

### 20.3 Idempotency

Consumers MUST dedupe on `event_id`. Assessment guarantees **at-most-once publish** with outbox retry; consumers MUST be idempotent.

### 20.4 Minimum concept coverage

Drill/mock events MUST include ≥1 `concept_scores` entry unless assessment_type is purely mock aggregate-only (then include top-20 concept deltas minimum for graph updates).

---

## 21. `AnswerEvaluated` event (Mains V2+)

### 21.1 Payload (outline)

```json
{
  "event_id": "uuid",
  "event_type": "AnswerEvaluated",
  "student_id": "uuid",
  "assessment_id": "uuid",
  "attempt_id": "uuid",
  "answer_id": "uuid",
  "paper": "mains_gs2",
  "evaluator": "ai_v1",
  "score_10": 6.5,
  "rubric_scores_json": { "structure": 7, "content": 6, "examples": 6, "flow": 7 },
  "concept_scores": [ { "concept_id": "...", "mains_component": 65.0 } ],
  "eval_confidence": 0.82,
  "occurred_at": "ISO8601"
}
```

### 21.2 Gating

Mains evaluations hidden from prediction until eval harness passes (`MASTER_IMPLEMENTATION_PLAN.md` D5). `eval_confidence` below threshold → faculty review queue, no `AnswerEvaluated` until approved.

---

## 22. Integration with Learning Graph

### 22.1 Read path (question selection)

| Operation | Port method |
|---|---|
| List rated nodes | `LearningGraphReadPort.list_rated_nodes` |
| Weak frontier | `list_nodes WHERE mastery < 60 AND importance >= 70` |
| Concept metadata | `ExamDomainReadPort.get_concept` |
| Prerequisite check | Optional — block questions on locked prereqs (Mentor policy) |

### 22.2 Write path (forbidden direct)

Assessment **NEVER** calls graph write APIs. Flow:

```
AssessmentCompleted → Learning Graph Service handler → ApplyMasteryUpdate + ApplyConfidenceUpdate → LearningGraphUpdated
```

### 22.3 Handler expectations (LG §7.1, §8.1)

On `AssessmentCompleted` (MCQ):

1. For each `concept_scores[]` entry: load node, merge evidence, compute mastery MCQ component.
2. Update `confidence_score` if confidence deltas present.
3. Set `last_assessment_at`, increment `n_mcq`.
4. Flip `node_state` to `rated` if first evidence.
5. Emit `LearningGraphUpdated`.

### 22.4 Nightly recency

Assessment evidence timestamps enable LG nightly mastery recency pass (`MASTERY_RECENCY_BATCH_DAYS=90`).

---

## 23. Integration with Preparation Twin

### 23.1 Twin rebuild triggers

| Event | Twin action |
|---|---|
| `AssessmentCompleted` (MCQ) | `RebuildAcademicAssessment.mcq`; `RebuildPredictionProfile` |
| `AssessmentCompleted` (prelims_mock) | Update `prelims_mocks`; Prelims prediction gate |
| `AnswerEvaluated` | `RebuildAcademicAssessment.mains`; Mains prediction |

### 23.2 Fields sourced from Assessment

Per `PREPARATION_TWIN_SPECIFICATION.md` §4.3:

| Twin field | Assessment source |
|---|---|
| `academic.assessment.mcq.accuracy_30d/90d` | `AssessmentReadPort.mcq_aggregate` |
| `guessing_rate` | weighted mean attempt.guessing_rate |
| `negative_marking_risk` | §17.3 formula |
| `prelims_mocks.count` | count mock_anchor attempts |
| `MCQSub input` | recency_difficulty_weighted_accuracy global |

### 23.3 Debounce

Twin coalesces `AssessmentCompleted` + subsequent `LearningGraphUpdated` within **5s** into single rebuild (`PREPARATION_TWIN_SPECIFICATION.md` §9.3).

---

## 24. Integration with Mentor Agent

### 24.1 Tools backed by Assessment read models

| Tool | Read model |
|---|---|
| `GetAssessmentHistoryTool` | `student_assessment_history` |
| `GetAssessmentGapsTool` | `student_assessment_gaps` |

### 24.2 `GetAssessmentGapsTool` contract (Mentor §9.2)

Assessment Engine maintains authoritative gap projection:

```json
{
  "weak_concepts": [
    {
      "concept_id": "upsc.cse.economy.monetary_policy.repo_rate",
      "error_rate": 0.45,
      "importance": 88,
      "last_attempt_at": "2026-06-17T18:00:00Z",
      "n_attempts_90d": 12
    }
  ],
  "mock_recommended": true,
  "mains_gap_subjects": ["upsc.cse.economy"],
  "guessing_rate_elevated": true,
  "last_mock_at": "2026-06-10T09:00:00Z",
  "as_of": "2026-06-18T02:00:00Z"
}
```

### 24.3 Gap computation

```
RebuildAssessmentGaps(student):
1.  FOR each rated concept C with n_mcq_90d >= 3:
        error_rate = 1 - weighted_accuracy_90d(C)
        IF error_rate >= 0.35 OR (importance >= 80 AND mastery < 55):
           add to weak_concepts
2.  mock_recommended = (days_to_exam < 120 AND mock_count < 1) OR (readiness > 65 AND days_to_exam < 120)
3.  mains_gap_subjects = subjects WHERE WritingSub proxy low (V2)
4.  guessing_rate_elevated = guessing_rate_30d > threshold
```

Refresh: on `AssessmentCompleted` + nightly.

### 24.4 Plan task execution

Mentor plan items with `task_type=mcq_drill` include `concept_ids[]`. Student app calls:

```
POST /assessments { type: mcq_drill, concept_ids: [...], plan_task_id: ... }
```

Assessment stores `mentor_plan_item_id` for attribution analytics.

---

## 25. Integration with Revision Engine

### 25.1 Contract summary

| Direction | Contract |
|---|---|
| Revision → Assessment | `StartRecallSession(revision_id)` creates session |
| Assessment → Revision | Valid `recall_session_id` for `CompleteRevision` |
| Revision → LG | `RevisionCompleted` — separate from Assessment MCQ path |

### 25.2 Session linking

When student opens revision item in UI:

```
1.  POST /recall-sessions { revision_id, concept_id }
2.  Student completes prompts
3.  POST /revisions/{id}/complete { recall_grade, recall_session_id }
4.  Revision Engine validates via Assessment read API ValidateRecallSession
5.  RevisionCompleted → LG (revision channel) — NOT AssessmentCompleted unless config §12.7
```

### 25.3 Fatigue signal

Revision session duration and grades may be correlated with Assessment attempt timestamps for behavioral analytics — no direct write to Revision Engine.

---

## 26. Integration with Scoring Engine

### 26.1 Pure function boundaries

| Computation | Owner | Invoked by |
|---|---|---|
| Mastery MCQ component | Scoring v1.0 §2 | LG on event; Assessment previews optional |
| Confidence | Scoring v1.0 §13 | LG on event |
| MCQSub (exam-wide) | Scoring v1.1 §4 | Twin builder reads Assessment aggregates |
| Mock net score | Assessment §7.3 | Attempt row (not a Scoring Engine score) |
| Readiness / Predictions | Scoring v1.1 | Twin — not Assessment |

### 26.2 MCQSub roll-up (exam-wide)

Assessment maintains global aggregate for Twin:

```
MCQSub_numerator = Σ attempts in window: recency_difficulty_weighted_correct
MCQSub_denominator = Σ attempts in window: recency_difficulty_weight
MCQSub = 100 · numerator / denominator
```

Window: rolling **90 days** default; aligns with Scoring v1.0 Readiness inputs.

### 26.3 Version pinning

`assessment_attempts.scoring_version` + `concept_mcq_evidence.formula_version` enable replay when Scoring migrates.

---

## 27. Mains evaluation architecture (V2/V3 outline)

### 27.1 V1 scope

**Out of scope for V1 implementation.** API stubs return `501 Not Implemented` for Mains submit except storage-only draft (optional).

### 27.2 V2 components

| Component | Responsibility |
|---|---|
| `MainsSubmissionService` | S3 answer storage, metadata |
| `MainsEvaluationOrchestrator` | Queue AI eval jobs |
| **Assessment Agent** | LLM rubric application (Part 5) |
| Faculty review queue | Low `eval_confidence` |

### 27.3 Rubric dimensions (Part 2 §25)

Structure, content depth, examples, keyword coverage, flow — map to `mains_component` per concept via answer tagging.

### 27.4 Prediction unlock

`MAINS_ANSWER_THRESHOLD` (default **10** evaluated answers) per Scoring v1.1 §5.2.

---

## 28. Read models

### 28.1 `student_assessment_gaps`

Denormalized projection for Mentor tool (§24.3). PK: `(tenant_id, student_id)`.

### 28.2 `student_assessment_history`

| Column | Purpose |
|---|---|
| `last_10_attempts_json` | Mentor history tool |
| `attempts_30d`, `attempts_90d` | Volume |
| `last_mock_at`, `mock_count` | Mock gating |

### 28.3 `student_concept_mcq_evidence`

Per `(tenant, student, concept)` — §14.3 counters.

### 28.4 `student_mcq_daily_stats`

Analytics: attempts/day, accuracy, guessing_rate — faculty batch heatmaps.

### 28.5 Refresh triggers

```
AssessmentCompleted → upsert gaps + history + concept evidence (async worker, idempotent)
Nightly → full gap recompute for active students
```

---

## 29. Database schemas

### 29.1 Core tables (logical)

**`assessments`**

| Column | Type | Notes |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `exam_id` | string | |
| `assessment_type` | enum | §3 |
| `status` | enum | §3.4 |
| `subject_id` | string nullable | Optional filter |
| `question_count` | int | |
| `config_json` | JSONB | timers, flags |
| `selection_metadata_json` | JSONB | algorithm trace |
| `mentor_plan_item_id` | UUID nullable | |
| `created_at` | timestamptz | |

**`assessment_questions`**

| Column | Type |
|---|---|
| `assessment_id` | UUID FK |
| `question_id` | UUID |
| `question_source` | enum |
| `sequence_number` | int |

**`assessment_attempts`** — §10.2

**`assessment_responses`** — §11.1

**`recall_sessions`** — §12.2

**`assessment_outbox`** — §19.3

**`assessment_processed_events`** — consumer idempotency audit (optional cross-ref)

### 29.2 Indexing strategy

| Index | Purpose |
|---|---|
| `(tenant_id, student_id, created_at DESC)` on assessments | History |
| `(attempt_id)` on responses | Score pipeline |
| `(tenant_id, student_id, concept_id)` on mcq_evidence | Gap tool |
| `(recall_session_id)` on recall_responses | Validation |

### 29.3 Partitioning (scale)

`assessment_responses` partition by `attempt_started_month` when rows > 50M.

---

## 30. API contracts

Aligned with `06-api-spec.md` §22; expanded for implementation.

### 30.1 `POST /assessments`

**Request:**

```json
{
  "assessment_type": "mcq_drill",
  "concept_ids": ["upsc.cse.polity.fundamental_rights.article_14"],
  "question_count": 30,
  "mentor_plan_item_id": "uuid-optional",
  "idempotency_key": "uuid-optional"
}
```

**Response `201`:**

```json
{
  "assessment_id": "uuid",
  "status": "draft",
  "question_count": 30,
  "assessment_type": "mcq_drill"
}
```

### 30.2 `GET /assessments/{id}`

Returns assessment metadata + questions (without answers) + active attempt if any.

### 30.3 `POST /assessments/{id}/start`

Creates/resumes attempt. Returns `attempt_id`.

### 30.4 `PATCH /assessments/{id}/responses`

Append/update in-progress responses (before submit). Body: array of `{ question_id, selected_option_id, response_time_sec, confidence }`.

### 30.5 `POST /assessments/{id}/submit`

**Request:**

```json
{
  "attempt_id": "uuid",
  "responses": [ ]
}
```

**Response `202`:**

```json
{
  "attempt_id": "uuid",
  "status": "submitted"
}
```

### 30.6 `GET /assessments/{id}/results`

Available when `status=completed`. Includes per-question explanations, concept breakdown, readiness impact summary (display layer).

### 30.7 Recall APIs

| Method | Path | Purpose |
|---|---|---|
| POST | `/recall-sessions` | Start session |
| POST | `/recall-sessions/{id}/grade` | Grade prompt |
| GET | `/recall-sessions/{id}` | Session status |
| GET | `/internal/recall-sessions/{id}/validate` | Revision Engine validation (service auth) |

### 30.8 Internal read ports (service-to-service)

| Port | Method | Consumer |
|---|---|---|
| `AssessmentReadPort` | `mcq_aggregate(student, windows)` | Twin |
| `AssessmentReadPort` | `get_gaps(student)` | Mentor |
| `AssessmentReadPort` | `validate_recall_session(...)` | Revision |
| `AssessmentReadPort` | `list_evidence(student, concept)` | Learning Graph replay |

### 30.9 WebSocket

On scoring complete, publish:

```json
{
  "type": "assessment_complete",
  "assessment_id": "uuid",
  "attempt_id": "uuid",
  "accuracy": 0.66
}
```

---

## 31. Caching strategy

### 31.1 Redis keys

| Key | TTL | Content |
|---|---|---|
| `assess:active:{tenant}:{student}` | 1h | Active attempt ids |
| `assess:gaps:{tenant}:{student}` | 120s | Serialized gaps DTO |
| `assess:questions:{assessment_id}` | 24h | Question payload sans answers |
| `assess:pool:{exam}:{concept}:{catalog_v}` | 300s | Eligible question id list |
| `assess:cohort_median:{exam}:{difficulty}` | 24h | Speed normalization |

### 31.2 Invalidation

```
AssessmentCompleted → DEL assess:gaps:{tenant}:{student}
DomainCatalogUpdated / PYQDataChanged → DEL assess:pool:*
```

### 31.3 Stampede protection

Gap tool uses single-flight lock `assess:gaps:lock:{student}` during rebuild.

---

## 32. Failure recovery

### 32.1 Scoring failure

```
IF ScoringPipelineJob fails after 3 retries:
  attempt.status = failed
  EMIT AssessmentScoringFailed
  Alert on-call
  Student sees retry button → creates new attempt with same questions (admin config)
```

### 32.2 Outbox stuck events

Background sweeper republishes `pending` outbox rows older than **5 minutes**.

### 32.3 Partial response submit

Transaction boundary prevents partial submits. Client retries submit with same idempotency key → no duplicate events.

### 32.4 Learning Graph consumer lag

Assessment marks attempt `completed` after outbox publish — **not** after LG ACK. LG eventual consistency acceptable; UI shows "scores updating" until `LearningGraphUpdated` propagates (typically < 2s).

### 32.5 Replay / backfill

```
RecomputeConceptEvidence(student, concept):
  SELECT all assessment_responses attributed to concept
  Reapply §14.2 formulas
  DO NOT re-emit AssessmentCompleted unless formula version migration approved
```

Full replay: regenerate `concept_scores` from evidence → synthetic migration events with new `event_id` (LG §14.3).

---

## 33. Performance requirements

Targets align with `MASTER_IMPLEMENTATION_PLAN.md` V1 (10k students, thousands of concurrent assessments).

### 33.1 Write path

| Operation | Target |
|---|---|
| `POST /assessments` (drill) | p95 < **400ms** including selection |
| `PATCH responses` (batch 5) | p95 < **80ms** |
| `POST submit` + sync score | p95 < **500ms** end-to-end |
| Prelims mock create | p95 < **2s** (async acceptable with polling) |
| Recall grade | p95 < **100ms** |

### 33.2 Read path

| Operation | Target |
|---|---|
| `GET /assessments/{id}` | p95 < **60ms** |
| `GET /assessments/{id}/results` | p95 < **120ms** |
| `GetAssessmentGaps` (cached) | p95 < **50ms** |
| Validate recall session (internal) | p95 < **30ms** |

### 33.3 Throughput

| Scenario | Target |
|---|---|
| Concurrent submits | **2,000** sustained |
| Celery assessment queue depth | alert > **10,000** |
| Outbox publish lag | p99 < **10s** |

### 33.4 Storage estimates (10k students)

| Entity | Approx rows |
|---|---|
| `assessment_attempts` | ~20/student/month → 2.4M/year |
| `assessment_responses` | ~30× attempts |
| `recall_sessions` | ~15/student/month |

---

## 34. Observability

### 34.1 Structured log fields

Every request: `request_id`, `tenant_id`, `student_id`, `assessment_id`, `attempt_id`, `assessment_type`.

### 34.2 Metrics

| Metric | Type |
|---|---|
| `assessment_create_total` | counter by type |
| `assessment_submit_total` | counter |
| `assessment_scoring_duration_ms` | histogram |
| `assessment_guessing_rate` | histogram |
| `assessment_scoring_failures` | counter |
| `recall_session_validation_failures` | counter |
| `outbox_lag_seconds` | gauge |

### 34.3 Traces

Span chain: `CreateAssessment` → `SelectQuestions` → `SubmitAttempt` → `ScorePipeline` → `PublishAssessmentCompleted`.

### 34.4 SLO alerts

- Scoring p95 > 800ms for 5 min → page
- Outbox pending > 500 rows → warn
- Guessing rate population mean spike > 0.25 → data quality review

---

## 35. Future AI Assessment Agent

### 35.1 Separation

Blueprint Part 5 **Assessment Agent** handles:

- Mains answer evaluation narration
- Rubric explanation to student
- Optional Socratic follow-up

**Scheduling, evidence storage, and event emission remain in Assessment Engine** (this spec).

### 35.2 Supervisor routing

| Intent | Route |
|---|---|
| "Evaluate my GS2 answer" | Assessment Agent |
| "Give me a polity drill" | Mentor → `POST /assessments` |
| "Explain this PYQ" | Knowledge Agent |

### 35.3 Eval harness

Mains AI evaluations gated behind eval harness (`MASTER_IMPLEMENTATION_PLAN.md` D5) before production `AnswerEvaluated` emission.

---

## Appendix A — Assessment type × event matrix

| assessment_type | Events emitted | LG update | Twin update |
|---|---|---|---|
| mcq_drill | AssessmentCompleted | MCQ mastery + confidence | mcq stats + prediction |
| prelims_mock | AssessmentCompleted | MCQ mastery (bulk) | prelims_mocks + prediction gate |
| diagnostic | AssessmentCompleted + DiagnosticCompleted | Bootstrap rating | coverage |
| recall_session | RecallSessionCompleted | via RevisionCompleted only* | behavior only |
| mains_descriptive | AnswerEvaluated | Mains mastery | WritingSub + prediction |
| ca_quiz | AssessmentCompleted | MCQ + CA | CASub (V2) |

*Unless `RECALL_MCQ_UPDATES_MASTERY=true`.

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `MCQ_DRILL_DEFAULT_COUNT` | 30 | §6 |
| `PRELIMS_MOCK_QUESTION_COUNT` | 100 | §7 |
| `DIAGNOSTIC_QUESTION_COUNT` | 40 | §8 |
| `GUESSING_TIME_THRESHOLD_SEC` | 8 | §17 |
| `GUESSING_ELEVATED_THRESHOLD` | 0.18 | §17.3 |
| `GUESS_WEIGHT` | 0.5 | §14.2 |
| `QUESTION_DEDUPE_WINDOW_DAYS` | 30 | §18 |
| `DEDUPE_REPEAT_WEIGHT_2ND` | 0.25 | §18.2 |
| `DEDUPE_REPEAT_WEIGHT_3RD_PLUS` | 0.10 | §18.2 |
| `MCQ_RECENCY_LAMBDA` | 0.05 | §14.2 |
| `ASSESSMENT_PAUSE_TTL_DAYS` | 7 | §10.4 |
| `ASSESS_GAPS_CACHE_TTL_SECONDS` | 120 | §31 |
| `RECALL_MCQ_UPDATES_MASTERY` | false | §12.7 |
| `RECALL_SESSION_MAX_AGE_HOURS` | 24 | §12.6 |
| `ASSESS_CREATE_RATE_LIMIT_HOUR` | 20 | §15.3 |
| `MOCK_SUBMIT_RATE_LIMIT_DAY` | 2 | §15.3 |
| `SCORING_VERSION_MCQ` | `mcq_simple_v1` | §13.2 |
| `SCORING_VERSION_MOCK` | `prelims_mock_v1` | §13.2 |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | §20 event payload, §14 evidence, §22 handler contract |
| `PREPARATION_TWIN_SPECIFICATION.md` | §23 aggregates, MCQSub inputs |
| `MENTOR_AGENT_SPECIFICATION.md` | §24 gaps/history tools, drill execution |
| `REVISION_ENGINE_SPECIFICATION.md` | §12 recall validation, §25 completion contract |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | §26 MCQSub, prediction anchors |
| `EXAM_DOMAIN_SPECIFICATION.md` | §5 tagging, stage relevance |
| API layer | §30 contracts |
| Analytics | §28.4 daily stats |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `LEARNING_GRAPH_SPECIFICATION.md` | Assessment never writes graph; `AssessmentCompleted` payload §20 matches LG §15.2; sync MCQ path |
| `PREPARATION_TWIN_SPECIFICATION.md` | Twin reads Assessment ports only; debounced rebuild; guessing_rate semantics |
| `REVISION_ENGINE_SPECIFICATION.md` | `recall_session_id` validation §12.6 matches RE §11.1; no revision writes |
| `MENTOR_AGENT_SPECIFICATION.md` | `GetAssessmentGapsTool` shape §24.2; negative marking guard; no graph writes |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | MCQSub single channel; mock/answer prediction gates; Confidence not student-facing |
| `EXAM_DOMAIN_SPECIFICATION.md` | Concept tagging §5; quarantine P6; prelims/mains relevance routing |
| `MASTER_IMPLEMENTATION_PLAN.md` | S9–S10 loop closure; MCQ V1 Mains V2/V3; diagnostic D16 |
| `06-api-spec.md` | Core routes §30; WebSocket `assessment_complete` |
| Blueprint Rule 5 | Scores owned by Learning Graph — §2, §22 |
| Blueprint Rule 3 | AI not source of truth — §35 Assessment Agent boundary |
| Blueprint Rule 4 | Post-test analysis explainable via concept_scores — §20 |

---

*End of Assessment Engine Specification v1.0*
