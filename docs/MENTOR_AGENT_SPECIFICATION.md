# PrepOS AI — Mentor Agent Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for Mentor Agent bounded context
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`, `REVISION_ENGINE_SPECIFICATION.md` (v1.1), `PREPARATION_TWIN_SPECIFICATION.md`
Authoring lens: Principal AI Systems Architect · Staff Software Architect · Learning Scientist · UPSC Domain Expert · Agentic Systems Designer · Distributed Systems Architect

> **Scope.** This document defines the **Mentor Agent**: the deterministic AI orchestration layer that converts student state into **actionable, explainable preparation guidance** — daily/weekly/monthly plans, interventions, and structured recommendations. It specifies agent architecture, tool contracts, planning engines, LLM augmentation boundaries, persistence, events, APIs, safety, and observability.
>
> **Non-goals:** UI layout, marketing, sprint tasks, SQL DDL, RAG ingestion pipelines (Knowledge Agent), Mains evaluation rubrics (Assessment Agent), payment/billing. Scoring **formulas** live in Scoring specs; **state** lives in Learning Graph, Revision Engine, Preparation Twin — Mentor **reads only via tools**.
>
> **Core invariant:** the Mentor Agent is **not a chatbot** and **not a source of truth**. It orchestrates reads from authoritative engines, applies **reproducible deterministic rules**, optionally **augments narration** via constrained LLM, and **persists plans and guidance artifacts** — never concept scores, revision schedules, or Twin profiles.

---

## 0. Canonical requirements map

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and bounded context | §1 |
| 2 | Ownership boundaries | §2 |
| 3 | Agent architecture | §3 |
| 4 | Agent memory model | §4 |
| 5 | Tool architecture | §5 |
| 6 | Preparation Twin integration | §6 |
| 7 | Learning Graph integration | §7 |
| 8 | Revision Engine integration | §8 |
| 9 | Assessment Engine integration | §9 |
| 10 | Current Affairs integration | §10 |
| 11 | PYQ Intelligence integration | §11 |
| 12 | Daily planning engine | §12 |
| 13 | Weekly planning engine | §13 |
| 14 | Monthly planning engine | §14 |
| 15 | Recommendation engine | §15 |
| 16 | Prioritization engine | §16 |
| 17 | Intervention engine | §17 |
| 18 | Motivation engine | §18 |
| 19 | Explainability model | §19 |
| 20 | Rule-based deterministic layer | §20 |
| 21 | LLM augmentation layer | §21 |
| 22 | Hallucination prevention architecture | §22 |
| 23 | Context assembly architecture | §23 |
| 24 | Agent workflows | §24 |
| 25 | Event-driven triggers | §25 |
| 26 | Read models | §26 |
| 27 | Database schemas | §27 |
| 28 | API contracts | §28 |
| 29 | Prompt architecture | §29 |
| 30 | Safety and governance | §30 |
| 31 | Observability | §31 |
| 32 | Performance requirements | §32 |
| 33 | Failure recovery | §33 |
| 34 | Multi-agent future architecture | §34 |
| 35 | Consistency checklist | Appendix D |

---

## 1. Purpose and bounded context

### 1.1 What the Mentor Agent is

The Mentor Agent is PrepOS's **senior-mentor-equivalent orchestration system**. It transforms consolidated student state into:

- **Structured plans** — revision, study, assessment, CA tasks with time budgets.
- **Interventions** — triggered when discipline, fatigue, or backlog signals cross thresholds.
- **Explainable guidance** — every task carries deterministic `reasoning_json` citing engine numbers.
- **Optional narrative** — LLM phrasing constrained to tool outputs; never inventing scores or tasks.

```
Authoritative engines (read-only via tools)     Mentor Agent (this spec)           Consumers
─────────────────────────────────────────     ────────────────────────           ───────────
Preparation Twin snapshot                  ──►  Planning + Intervention engines    Student app
Learning Graph (weak frontier, rollups)    ──►  Prioritization + Recommendation   WebSocket
Revision Queue                             ──►  Daily/Weekly/Monthly assembly     Faculty review
Assessment history + PYQ + CA signals      ──►  Explainability + Motivation       Analytics
                                              │
                                              ▼
                                         mentor_plans (write)
                                         mentor_interventions (write)
                                         MentorPlanGenerated (event)
```

### 1.2 What the Mentor Agent is NOT

| Misconception | Reality |
|---|---|
| Chatbot | Chat is an **optional interaction surface**; core product is **proactive plans** |
| Recommendation engine owning scores | Recommends **actions**; engines own **state** |
| Revision scheduler | Revision Engine owns queue; Mentor **consumes** it |
| Twin builder | Twin Builder owns `preparation_twins`; Mentor reads via tools |
| LLM-as-truth | LLM **narrates** deterministic plans; rules decide content |

Blueprint resolution (`MASTER_IMPLEMENTATION_PLAN.md` U3b): Revision Engine is fully deterministic; the blueprint "Revision Agent" is **narration/routing only** — scheduling stays in Revision Engine.

### 1.3 Bounded context (DDD)

```
┌────────────────────────────────────────────────────────────────┐
│                   Mentor Agent Context (this spec)              │
│  MentorOrchestrator · PlanningEngines · ToolGateway             │
│  mentor_plans · mentor_interventions · mentor_agent_events      │
└───────────────┬────────────────────────────────────────────────┘
                │ tools (read)          │ writes plans only
    ┌───────────┼───────────┬─────────┴────────┬──────────────┐
    ▼           ▼           ▼                  ▼              ▼
 Twin        Learning     Revision         Assessment      PYQ/CA
 Context     Graph        Engine           Context         Context
```

**Anti-corruption:** all upstream access through `ToolGateway` with typed DTOs — no cross-context repository imports.

### 1.4 UPSC preparation model (domain logic embedded)

The Mentor encodes **UPSC CSE preparation semantics**:

| Dimension | Mentor behavior |
|---|---|
| **Exam stages** | Prelims-heavy vs Mains-heavy task mix based on `days_to_exam` and student `target_stages` |
| **GS papers** | Map concepts to GS1–GS4 for Mains writing task selection |
| **High-yield first** | Importance ≥ 70 concepts prioritized in study slots (EXAM_DOMAIN) |
| **Retention loop** | Revision tasks sourced **only** from Revision Engine queue |
| **CA linkage** | Recent `CURRENT_AFFAIRS_OF` concepts get study/CA reading slots |
| **PYQ alignment** | PYQ-mapped weak concepts get assessment drill suggestions |
| **Optional subject** | Optional-subject concepts weighted ×1.0 vs ×0.9 (EXAM_DOMAIN §4.10) |
| **Negative marking** | High guessing rate → fewer risky MCQ drills, more revision |

### 1.5 Success criteria

1. `GET /mentor/today` returns a plan where **100% of tasks** have non-empty `reasoning_json` with engine refs.
2. Same tool outputs + config + date ⇒ **identical** `plan_json` (deterministic layer).
3. LLM unavailable ⇒ valid plan still generated (Rule layer only).
4. Zero Mentor writes to `student_concept_progress`, `revisions`, `preparation_twins`.
5. Eval harness: plan accuracy ≥ baseline; hallucination rate on cited numbers = **0%**.

---

## 2. Ownership boundaries

### 2.1 Write ownership matrix

| Data | Sole writer | Mentor relationship |
|---|---|---|
| `student_concept_progress` | Learning Graph Service | **Read via tools only** |
| `revisions`, `revision_sessions` | Revision Engine | **Read via tools only** |
| `preparation_twins` | Twin Builder | **Read via tools only** |
| `mentor_plans` | **Mentor Service** | Authoritative plan store |
| `mentor_plan_items` | **Mentor Service** | Denormalized items (optional) |
| `mentor_interventions` | **Mentor Service** | Intervention records |
| `mentor_session_memory` | **Mentor Service** | Conversation/workflow state |
| `mentor_agent_events` | **Mentor Service** | Append-only audit |
| `student_preferences` (goals, hours) | Student profile service | Mentor reads; student writes via profile API |
| Assessment attempts | Assessment Engine | Mentor reads via tools |

### 2.2 Forbidden operations

1. Mentor tool implementation calling `ConceptProgressRepository.save_node()`.
2. Mentor creating/updating `revisions` rows or calling `CompleteRevision` on behalf of scheduler logic.
3. Mentor patching `preparation_twins` JSONB.
4. LLM generating concept IDs not present in tool outputs.
5. Plan tasks without `reasoning_json.engine_refs`.
6. Student-facing text citing Weakness/Confidence numeric gauges (Scoring v1.1 R1/R4).

### 2.3 Determinism contract

| Layer | Reproducible? | Source of task multiset |
|---|---|---|
| **Rule layer (§20)** | **Yes** — byte-identical given inputs | Algorithms §12–§16 |
| **LLM layer (§21)** | **No** for prose; **Yes** for task set | Must not add/remove tasks |
| **Combined plan** | Task multiset deterministic; narrative may vary | Rule layer is authority |

---

## 3. Agent architecture

### 3.1 Layered architecture

```
┌─────────────────────────────────────────────────────────────┐
│  API / WebSocket / Supervisor Router                         │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│  MentorOrchestrator (LangGraph workflow)                     │
│  States: assemble_context → plan_deterministic → intervene   │
│          → motivate → narrate_optional → persist             │
└───────────────────────────┬─────────────────────────────────┘
                            ▼
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
  PlanningEngines      InterventionEngine    MotivationEngine
  (daily/weekly/month) (§17)                (§18)
        │                   │                   │
        └───────────────────┼───────────────────┘
                            ▼
                    ToolGateway (§5)
                            ▼
              Upstream engine HTTP/repository ports
```

### 3.2 LangGraph workflow graph

```
Entry: GeneratePlanRequest | ChatTurn | InterventionTrigger
  │
  ▼
[assemble_context]     ← ToolGateway parallel fetch (§23)
  │
  ▼
[run_interventions]    ← InterventionEngine (may prepend urgent tasks)
  │
  ▼
[plan_deterministic]   ← Daily|Weekly|Monthly engine by horizon
  │
  ▼
[apply_motivation]     ← MotivationEngine (messages, not task changes)
  │
  ▼
[narrate_llm]?         ← Optional if LLM enabled + chat mode
  │
  ▼
[validate_plan]        ← Hallucination guards (§22)
  │
  ▼
[persist_plan]         ← mentor_plans + event
  │
  ▼
Exit: PlanResponse | ChatResponse
```

**Checkpointing:** LangGraph persists `MentorGraphState` to `mentor_session_memory` for multi-turn chat within a planning session — not long-term knowledge.

### 3.3 Component boundaries (modular monolith)

```
domain/mentor/
  entities/           MentorPlan, PlanItem, Intervention, MentorGraphState
  services/           MentorOrchestrator, PlanningService
  engines/            DailyPlanEngine, WeeklyPlanEngine, MonthlyPlanEngine
                      PrioritizationEngine, RecommendationEngine
                      InterventionEngine, MotivationEngine
  policies/           UPSCPhasePolicy, CapacityPolicy, ExplainabilityPolicy
  tools/              ToolGateway, tool definitions (interfaces)

application/mentor/
  use_cases/          GenerateDailyPlan, GenerateWeeklyPlan, HandleChatTurn
  dto/

infrastructure/mentor/
  langgraph/          graph builder, checkpoints
  llm/                LLMClient, PromptRegistry
  persistence/        MentorPlanRepository
  observability/      tracing, eval hooks
```

### 3.4 Supervisor integration (V1)

Supervisor Agent routes intents (`05-agent-architecture.md` §4):

| Intent | Route |
|---|---|
| "What should I study today?" | Mentor `GenerateDailyPlan` |
| "Plan my week" | Mentor `GenerateWeeklyPlan` |
| "Evaluate my answer" | Assessment Agent (not Mentor) |
| "Explain federalism" | Knowledge Agent (not Mentor) |

Mentor **does not** implement Supervisor routing in V1 — exposes use cases Supervisor calls.

### 3.5 Human-in-the-loop (faculty override)

Faculty may override plans (`05-agent-architecture.md` §19):

```
POST /faculty/students/{id}/mentor/plans/{plan_id}/override
  → creates mentor_plan_overrides row
  → emits MentorPlanOverridden
  → original plan retained; override plan displayed to student
```

Overrides are **signals** for eval harness — not training data in V1.

---

## 4. Agent memory model

The Mentor has **no authoritative long-term memory** separate from platform state. Memory is tiered:

### 4.1 Memory tiers

| Tier | Name | Storage | TTL | Contents |
|---|---|---|---|---|
| **M0** | Platform truth | LG + Twin + Revision + Assessment | permanent | Scores, plans queue, history |
| **M1** | Session workflow | `mentor_session_memory` | 24h | LangGraph state, chat turns in session |
| **M2** | Plan artifact | `mentor_plans` | permanent | Immutable generated plans |
| **M3** | Student preferences | `students.settings` | permanent | daily hours, target exam, stage focus |
| **M4** | Ephemeral LLM context | in-request only | request | Assembled prompt; not persisted raw |

**Rule:** Mentor MUST NOT store derived scores in M1/M4 that duplicate M0 — always re-fetch via tools on new plan generation.

### 4.2 `mentor_session_memory` schema (logical)

| Field | Description |
|---|---|
| `session_id` | UUID |
| `tenant_id`, `student_id` | scope |
| `conversation_id` | optional chat thread |
| `graph_state_json` | LangGraph checkpoint |
| `last_plan_id` | FK mentor_plans |
| `tool_cache_hash` | invalidates on TwinUpdated |
| `expires_at` | 24h default |

### 4.3 Chat vs proactive planning

| Mode | Memory use |
|---|---|
| **Proactive** (daily 6am push) | No chat history; fresh tool fetch |
| **Interactive chat** | M1 holds last N turns (max 10); each plan-altering turn re-runs tools |

Chat history **cannot** override deterministic rules ("student says skip revision" → logged preference hint only; revision tasks remain unless explicit skip action via Revision API).

### 4.4 What Mentor remembers vs infers

| Remembered (persisted) | Inferred (recomputed each run) |
|---|---|
| Generated plans | Readiness, weak topics |
| Interventions fired | Revision queue |
| Faculty overrides | PYQ weak areas |
| Student hour budget prefs | CA priorities |

---

## 5. Tool architecture

Agents **never access databases directly** (`05-agent-architecture.md` §14). All reads through **ToolGateway**.

### 5.1 Tool design principles

| # | Principle |
|---|---|
| T1 | Tools return **structured JSON** with schema version |
| T2 | Tools enforce **tenant_id + student_id** scope |
| T3 | Tools are **read-only** in V1 (except `PersistMentorPlanTool` internal) |
| T4 | Tool outputs are **cached** 60s per `(tenant, student, tool_name)` |
| T5 | Every tool call logged with `request_id`, latency, row counts |

### 5.2 Tool registry

Central registry (`tool_registry` config):

```
mentor_tools:
  - GetPreparationTwinTool
  - GetTwinSnapshotTool
  - GetReadinessDriversTool
  - GetLearningGraphTool
  - GetPlanEligibleConceptsTool
  - GetWeakTopicsTool
  - GetRevisionBacklogTool
  - GetAssessmentHistoryTool
  - GetAssessmentGapsTool
  - GetCurrentAffairsPrioritiesTool
  - GetPYQInsightsTool
  - GetExamCalendarTool
  - GetStudentPreferencesTool
  - GetConceptMetadataTool
```

### 5.3 Tool catalog

#### `GetPreparationTwinTool`

| Attribute | Value |
|---|---|
| Source | Twin internal API (`PREPARATION_TWIN_SPECIFICATION.md` §26.4) |
| Returns | Full `academic_profile`, `behavioral_profile`, `prediction_profile` |
| Used by | All planning engines, InterventionEngine |

#### `GetTwinSnapshotTool`

| Attribute | Value |
|---|---|
| Source | `student_twin_snapshot` read model |
| Returns | Dashboard subset: readiness, drivers, health, fatigue, streak, coverage |
| Used by | MotivationEngine, fast daily plan path |

#### `GetReadinessDriversTool`

| Returns | Top-2 `prediction_profile.readiness.drivers` |
| Used by | Study slot subject focus, MotivationEngine |

#### `GetLearningGraphTool`

| Returns | Subject/topic rollups, optional concept drill-down |
| Params | `concept_ids[]` optional |
| Ref | `LEARNING_GRAPH_SPECIFICATION.md` §10.4 shape |

#### `GetPlanEligibleConceptsTool`

| Returns | `{ revisions[], study[], related[] }` with score snapshots |
| Implementation | **LearningGraphService.GetPlanEligibleConcepts** (LG §10.2) |
| Note | `revisions[]` IDs merged from Revision Engine — not recomputed |

#### `GetWeakTopicsTool`

| Returns | Top K weak topics by `importance × (100 - mastery)` |
| Params | `limit`, `subject_id` optional |

#### `GetRevisionBacklogTool`

| Returns | `{ today[], overdue[], upcoming[], active_session?, revision_health, revision_fatigue, streak }` |
| Source | Revision Engine API |
| Ref | `REVISION_ENGINE_SPECIFICATION.md` §14.2 |

#### `GetAssessmentHistoryTool`

| Returns | Recent attempts, accuracy trends, mock scores |
| Params | `window_days`, `assessment_type` |

#### `GetAssessmentGapsTool`

| Returns | Concepts with high error_rate or post-test weak flags |
| Used by | Assessment task slot in daily plan |

#### `GetCurrentAffairsPrioritiesTool`

| Returns | CA items + linked concepts with relevance scores (last 30d) |
| Used by | CA reading slots, study boost |

#### `GetPYQInsightsTool`

| Returns | High-yield concepts with PYQ frequency, student weakness on PYQ-mapped concepts |
| Used by | Assessment drill selection, monthly focus |

#### `GetExamCalendarTool`

| Returns | `target_exam_date`, `days_to_exam`, stage milestones |
| Used by | UPSCPhasePolicy |

#### `GetStudentPreferencesTool`

| Returns | `daily_study_minutes`, `daily_revision_slots`, `preferred_study_hours`, `target_stages[]` |

#### `GetConceptMetadataTool`

| Returns | Taxonomy labels, GS paper mapping, prelims/mains relevance |
| Source | EXAM_DOMAIN catalog |

### 5.4 Parallel tool fetch (context assembly)

```
assemble_context(student, plan_date):
  PARALLEL:
    twin_snapshot = GetTwinSnapshotTool()
    twin_full     = GetPreparationTwinTool()        // if weekly/monthly
    revision      = GetRevisionBacklogTool()
    eligible      = GetPlanEligibleConceptsTool()
    assess_gaps   = GetAssessmentGapsTool()
    ca            = GetCurrentAffairsPrioritiesTool()
    pyq           = GetPYQInsightsTool()
    calendar      = GetExamCalendarTool()
    prefs         = GetStudentPreferencesTool()
  RETURN MentorContext bundle
```

SLA: parallel wall clock p95 < **400ms** (§32).

### 5.5 ToolGateway error handling

| Error | Mentor behavior |
|---|---|
| Twin timeout | Retry 1×; fallback to cached snapshot ≤5min stale |
| Revision timeout | Daily plan: revision slots empty + intervention flag |
| Graph timeout | Study slots from Twin rollups only (degraded) |
| All tools fail | Return `503` + last persisted plan if `<24h` |

---

## 6. Preparation Twin integration

### 6.1 Twin as planning compass

Twin provides **headline signals** without per-concept authority:

| Twin field | Mentor use |
|---|---|
| `readiness.value` + `drivers` | Subject focus for study slots; motivation copy |
| `behavioral.revision.health` | Intervention triggers (§17) |
| `behavioral.revision.fatigue` | Capacity reduction (§12.4) |
| `behavioral.revision.streak` | Motivation + intervention |
| `academic.knowledge.weakest_subject` | Study prioritization |
| `academic.knowledge.most_forgotten_topic` | Weekly emphasis |
| `academic.assessment.mcq.negative_marking_risk` | MCQ drill intensity |
| `academic.ca.coverage_90d` | CA slot sizing |
| `prediction_profile` | Phase messaging; never recompute Readiness in Mentor |

### 6.2 Read path only

```
TwinBuilder ──writes──► preparation_twins
                              ▲
Mentor ToolGateway ──reads──┘ (HTTP internal / repository port)
```

### 6.3 Event subscription (Mentor as consumer)

| Event | Mentor action |
|---|---|
| `TwinUpdated` | Invalidate tool cache; optionally enqueue proactive replan if `changed_sections` includes readiness drivers |
| `RevisionBacklogIntervention` | Trigger InterventionEngine |
| `RevisionFatigueRecomputed` | Adjust next plan capacity |

Mentor **does not** subscribe with write-back.

### 6.4 Degraded mode without Twin

If Twin unavailable, Mentor MAY compose minimal context from direct graph + revision tools — log `twin_degraded=true`. Readiness drivers fallback to weakest subject from graph rollups only.

---

## 7. Learning Graph integration

### 7.1 Division of responsibility

| Concern | Learning Graph | Mentor |
|---|---|---|
| Per-concept scores | **Authoritative** | Reads via tools |
| Weak frontier algorithm | **LG §10.2** | Consumes `GetPlanEligibleConceptsTool` |
| Prerequisite gate | **LG §10.3** | Surfaces blocked concepts with reason in reasoning_json |
| Revision queue membership | **Not LG** | From Revision Engine |

### 7.2 Study task sourcing

```
study_candidates = GetPlanEligibleConceptsTool().study
// already filtered: rated, prerequisite gate, ordered by importance × (100-mastery)
```

Mentor **must not** implement alternate weak-frontier sort — ensures consistency with graph service.

### 7.3 Related concept expansion

Optional `related[]` from LG §10.2 — Mentor includes max **1 related concept/day** as low-priority study stretch task when capacity allows.

### 7.4 Overconfidence handling

When `overconfidence_flag=true` on a study candidate:

```
reason_codes append "overconfidence_warning"
motivation message_key = "mentor.overconfidence_focus"
// Scoring v1.1 R4: flag only, no Confidence number in student text
```

### 7.5 Forbidden

- Querying `student_concept_progress` from Mentor repository directly.
- Recomputing Mastery, Retention, Weakness locally.

---

## 8. Revision Engine integration

### 8.1 Division of responsibility

| Concern | Revision Engine | Mentor |
|---|---|---|
| Revision queue | **Authoritative** | Consumes `GetRevisionBacklogTool` |
| Priority formula | **RE §5** | Reads `priority_score` for explainability only |
| Revision completion | **RE §11** | Student action via Revision API — not Mentor |
| Revision Health compute | **RE §15** | Reads from Twin/backlog tool |

### 8.2 Daily revision tasks

```
revision_tasks = GetRevisionBacklogTool().today
  ORDER BY priority_score DESC (already ordered by engine)
  LIMIT effective_revision_capacity   // §12.4

FOR each task:
  reasoning_json = {
    engine_refs: revision.priority_factors,
    revision_id: task.id,
    message_key: derive_key(retention, importance)
  }
```

Mentor **never** inserts concepts into revision queue not present in `today[]` or `overdue[]`.

### 8.3 Overdue handling

Include `overdue[]` items **before** upcoming within revision capacity — matches RE recovery policy. Cap overdue at `MIN(overdue.count, capacity * 0.5)`.

### 8.4 Fatigue capacity modifier

From Twin/RE (`PREPARATION_TWIN_SPECIFICATION.md` §6, `REVISION_ENGINE_SPECIFICATION.md` §15.6):

```
effective_revision_capacity = base_revision_slots
IF fatigue.band == 'high':      capacity *= 0.80
IF fatigue.band == 'exhausted': capacity *= 0.60
IF backlog_intervention_active: capacity = min(capacity, 15)
```

### 8.5 Revision session awareness

If `active_session` in backlog tool response, plan groups revision tasks under single `revision_session` block — UI starts session via Revision API.

---

## 9. Assessment integration

### 9.1 Assessment task types in plans

| Type | Trigger | Default slot |
|---|---|---|
| **MCQ drill** | weak PYQ concepts OR post-mock gap | 30 questions / 45 min |
| **Prelims mock** | monthly plan OR readiness > 65 + exam < 120d | full mock |
| **Mains answer** | WritingSub low OR GS paper gap | 1 answer / 60 min |
| **Essay practice** | optional Essay profile | 1 essay / 90 min |

### 9.2 `GetAssessmentGapsTool` output shape

```json
{
  "weak_concepts": [
    { "concept_id": "...", "error_rate": 0.45, "importance": 88, "last_attempt_at": "..." }
  ],
  "mock_recommended": false,
  "mains_gap_subjects": ["upsc.cse.polity"],
  "guessing_rate_elevated": true
}
```

### 9.3 UPSC MCQ drill selection

```
SelectMCQDrillConcepts(gaps, pyq, limit=30 questions worth):
  candidates = union(gaps.weak_concepts, pyq.pyq_weak_high_yield)
  sort by importance × error_rate DESC
  take top concepts covering 30 questions (configurable)
```

### 9.4 Negative marking guard

If `guessing_rate_elevated`:

```
reduce MCQ drill to 20 questions
add reason_code "negative_marking_risk"
recommend revision over new MCQ (motivation copy)
```

### 9.5 Post-assessment replan

On `AssessmentCompleted` event (§25), Mentor may enqueue **optional** lightweight replan (assessment slot adjustment next day) — does not mutate graph.

---

## 10. Current Affairs integration

### 10.1 CA in daily plans

CA tasks are **reading + linkage**, not scoring:

| Task subtype | Content |
|---|---|
| `ca_reading` | 2–3 CA articles from last 7d high relevance |
| `ca_linked_study` | Study concept with `CURRENT_AFFAIRS_OF` edge to recent CA |

### 10.2 Priority algorithm

```
GetCurrentAffairsPrioritiesTool → items sorted by ca_relevance (RE §9 CARelevanceScore analog)

daily_ca_slots =
  IF days_to_exam < 90: 2 items
  ELIF ca_coverage_90d < 0.5: 2 items
  ELSE: 1 item

Select top daily_ca_slots not already covered in last 3 days (rotation)
```

### 10.3 CA + Prelims phase

When `UPSCPhasePolicy.phase == PRELIMS_SPRINT` (exam < 60d):

```
ca_slots min = 2
link each ca_reading to ≥1 concept drill or MCQ tag
```

### 10.4 Knowledge Agent boundary

Deep CA **explanation** routes to Knowledge/CA Agent on chat — Mentor plan only assigns **what to read/study**, not long-form explanation generation in plan JSON.

---

## 11. PYQ Intelligence integration

### 11.1 PYQ signals consumed

| Signal | Source | Mentor use |
|---|---|---|
| Concept `importance` (PYQ-driven) | Graph/Twin | Already in study/revision sort |
| PYQ weak concepts | `GetPYQInsightsTool` | MCQ drill target |
| Rising trend topics | PYQ trend factor | Monthly plan emphasis |
| Unmapped high-frequency gaps | PYQ admin flags | Faculty-only notes |

### 11.2 `GetPYQInsightsTool` response shape

```json
{
  "pyq_weak_concepts": [
    { "concept_id": "...", "importance": 92, "pyq_count": 14, "student_mastery": 38 }
  ],
  "trending_topics": [
    { "topic_id": "...", "trend_norm": 0.85, "subject_id": "..." }
  ],
  "high_yield_unrated": [
    { "concept_id": "...", "importance": 95, "node_state": "unrated" }
  ]
}
```

### 11.3 PYQ-driven study suggestion

`high_yield_unrated` concepts → **new study** tasks (not revision):

```
message_key = "mentor.pyq_high_yield_new"
reason: "Appears in 12 PYQs; not yet studied"
```

### 11.4 Monthly PYQ audit task

Monthly plan includes **1 PYQ mapping review session** (self-test: "attempt 20 PYQ-tagged MCQs across weakest high-yield topic") — deterministic template.

---

## 12. Daily planning engine

### 12.1 Purpose

Produce **`mentor_plans` row** for `plan_date=today` with ordered tasks fitting student time budget.

### 12.2 Inputs (mandatory)

1. Preparation Twin snapshot  
2. Learning Graph eligible concepts  
3. Revision queue (`today` + capped `overdue`)  
4. Assessment gaps + PYQ signals  
5. Current Affairs priorities  
6. Exam calendar + student preferences  

### 12.3 Time budget algorithm

```
total_minutes = prefs.daily_study_minutes OR tenant.default (180)

ALLOCATION BY PHASE (UPSCPhasePolicy):
  PRELIMS_FOCUS:   revision 35%, study 25%, mcq 25%, ca 10%, mains 5%
  BALANCED:        revision 30%, study 30%, mcq 20%, ca 10%, mains 10%
  MAINS_FOCUS:     revision 25%, study 25%, mcq 10%, ca 10%, mains 30%
  SPRINT (<60d):   revision 40%, study 20%, mcq 25%, ca 15%, mains 0%

Apply fatigue modifier to revision % only (shift excess to study)

Convert percentages → minute budgets → task counts using avg task durations:
  revision: 4 min/item (RE REVISION_AVG_MINUTES)
  study: 25 min/concept block
  mcq: 1.5 min/question
  mains: 60 min/answer
  ca: 15 min/article
```

### 12.4 Algorithm `GenerateDailyPlan`

```
INPUT:  MentorContext, plan_date, now
OUTPUT: MentorPlan

1.  phase = UPSCPhasePolicy.resolve(days_to_exam, target_stages)
2.  budgets = ComputeTimeBudgets(prefs, phase, fatigue)
3.  revision_tasks = SelectRevisionTasks(revision_backlog, budgets.revision)
4.  study_tasks    = SelectStudyTasks(eligible.study, drivers, budgets.study)
5.  ca_tasks        = SelectCATasks(ca_priorities, budgets.ca)
6.  assess_tasks   = SelectAssessmentTasks(gaps, pyq, budgets.mcq, budgets.mains)
7.  interventions  = InterventionEngine.evaluate(context)   // §17
8.  candidates = merge(revision_tasks, study_tasks, ca_tasks, assess_tasks, interventions)
9.  prioritized = PrioritizationEngine.rank(candidates)       // §16
10. recommended = RecommendationEngine.fill_slots(prioritized, budgets)  // §15
11. ordered = SequenceTasks(recommended)   // revision first AM, MCQ PM, etc.
12. plan = BuildPlanJson(ordered, reasoning for each)
13. motivation = MotivationEngine.select(context, plan)         // §18
14. RETURN plan with summary_message_key, reasoning_json root
```

### 12.5 Daily task sequencing (UPSC rhythm)

```
Default sequence (local time aware):
  06:00-09:00  revision_tasks (retention peak study science)
  09:00-12:00  study_tasks (new learning)
  12:00-12:30  ca_tasks (light reading)
  15:00-17:00  assess_tasks.mcq
  17:00-19:00  assess_tasks.mains (if any)
  Flexible     related/stretch study if underscheduled
```

Student `preferred_study_hours` shifts blocks — does not drop task types.

### 12.6 Plan JSON schema (core)

```json
{
  "plan_id": "uuid",
  "plan_date": "2026-06-18",
  "horizon": "daily",
  "phase": "BALANCED",
  "total_estimated_minutes": 175,
  "tasks": [
    {
      "task_id": "uuid",
      "sequence": 1,
      "task_type": "revision",
      "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
      "revision_id": "uuid",
      "title": "Revise: Article 14 — Equality before law",
      "estimated_minutes": 4,
      "scheduled_window": { "start_hour": 6, "end_hour": 9 },
      "reasoning": {
        "reason_codes": ["high_yield_fading", "revision_queue"],
        "engine_refs": {
          "importance": 92,
          "retention": 50,
          "priority_score": 64.6,
          "ca_relevance": 0
        },
        "message_key": "revision.high_yield_fading"
      }
    }
  ],
  "motivation": {
    "headline_key": "mentor.daily.headline.on_track",
    "body_key": "mentor.daily.body.streak_12",
    "params": { "streak_days": 12, "readiness": 71 }
  },
  "metadata": {
    "planner_version": "daily_planner_v1",
    "deterministic_hash": "sha256:...",
    "tool_snapshot_at": "ISO8601"
  }
}
```

### 12.7 Idempotency

```
UNIQUE (tenant_id, student_id, plan_date, horizon='daily', status='active')
Regenerate: supersedes prior active plan → status='superseded', new row active
```

---

## 13. Weekly planning engine

### 13.1 Purpose

Seven-day ** thematic outline** — not full daily duplication. Assigns subject emphasis, mock targets, CA themes.

### 13.2 Algorithm `GenerateWeeklyPlan`

```
INPUT:  MentorContext (full twin), week_start_date
1.  weak_subjects = bottom 3 subjects by mastery_avg from twin.academic.knowledge.subject_rollups
2.  driver_subjects = readiness.drivers subject_ids
3.  focus_subjects = unique(weak_subjects ∪ driver_subjects) take 3
4.  FOR each day d in Mon-Sun:
      assign primary_subject = rotate(focus_subjects)
      assign secondary = next in rotation
5.  mock_target = 1 prelims mock if phase in {PRELIMS_FOCUS, SPRINT} AND mocks/month < 4
6.  mains_target = 3 answers if phase in {MAINS_FOCUS, BALANCED} AND writing subscore < 65
7.  ca_theme = top CA cluster from GetCurrentAffairsPrioritiesTool (last 14d)
8.  pyq_theme = top trending topic from GetPYQInsightsTool
9.  EMIT weekly plan JSON with daily themes + targets (not item-level revision IDs)
```

### 13.3 Weekly output shape

```json
{
  "horizon": "weekly",
  "week_start": "2026-06-16",
  "daily_themes": [
    { "date": "2026-06-16", "primary_subject": "Economy", "focus": "Monetary Policy + Repo Rate CA link", "targets": { "revision_slots": 20, "study_blocks": 2, "mcq_questions": 40 } }
  ],
  "weekly_targets": { "prelims_mock": 1, "mains_answers": 3, "ca_articles": 10 },
  "reasoning": { "focus_rationale": "Readiness drivers: Economy, Ethics weak retention" }
}
```

Daily engine **still runs each morning** — weekly plan informs subject rotation weights (+20% priority boost for day's primary subject).

---

## 14. Monthly planning engine

### 14.1 Purpose

Exam-distance **strategic arc** — syllabus coverage milestones, mock cadence, Mains writing ramp.

### 14.2 UPSC monthly phases

| Months to exam | Phase name | Strategic emphasis |
|---|---|---|
| > 12 | FOUNDATION | Breadth coverage, low mock frequency |
| 6–12 | BALANCED | Revision loop stable, monthly mock |
| 3–6 | PRELIMS_FOCUS | MCQ volume, CA intensity, reduce new breadth |
| < 3 | SPRINT | Revision-heavy, full mocks biweekly |
| Post-prelims | MAINS_FOCUS | Writing 40%+ time |

### 14.3 Algorithm `GenerateMonthlyPlan`

```
1.  phase = UPSCPhasePolicy.from_days_to_exam(days_to_exam)
2.  coverage_gap = 1 - twin.academic.syllabus_engagement.coverage_high_importance
3.  subjects_behind = subjects where topic_coverage < 0.3 ordered by importance_mass
4.  milestones = []
    IF coverage_gap > 0.3: milestone "Complete {N} high-importance topics in {subjects_behind top 2}"
    IF phase >= PRELIMS_FOCUS: milestone "{4} Prelims mocks"
    IF phase >= MAINS_FOCUS OR writing subscore < 60: milestone "{12} Mains answers evaluated"
5.  revision_health_target = max(current_health, 75) if current < 70 else maintain
6.  OUTPUT monthly plan with milestones[], phase, subject_priority_ranking[]
```

### 14.4 Integration with daily/weekly

Monthly plan stored with `horizon=monthly`. Daily PrioritizationEngine adds **milestone alignment bonus** (+10 priority points) to tasks advancing active milestones.

---

## 15. Recommendation engine

### 15.1 Definition

The Recommendation Engine **selects which candidates fill time-budget slots** after prioritization — it does not compute scores or fetch data.

### 15.2 Algorithm `fill_slots`

```
INPUT:  prioritized_candidates[], budgets by task_type
OUTPUT: selected_tasks[]

FOR task_type IN [revision, study, ca_reading, mcq_drill, mains_write]:
  pool = candidates WHERE type = task_type ORDER BY priority DESC
  consumed_minutes = 0
  FOR c IN pool:
    IF consumed_minutes + c.estimated_minutes <= budgets[task_type]:
      selected.append(c)
      consumed_minutes += c.estimated_minutes
  // mandatory revision override: if high_yield_fading mandatory concepts in pool, force include even if slight budget exceed (≤10%)

RETURN selected
```

### 15.3 Diversity constraints

| Constraint | Rule |
|---|---|
| Max study concepts same topic/day | 2 |
| Max revision same subject/session | 8 consecutive |
| Min distinct subjects in revision set | 3 (if capacity ≥ 10) |
| CA articles same category/day | 1 |

### 15.4 Task type mapping

| Candidate source | task_type |
|---|---|
| Revision backlog item | `revision` |
| Plan eligible study concept | `study` |
| CA priority item | `ca_reading` |
| Assessment gap / PYQ weak | `mcq_drill` |
| Mains gap subject | `mains_write` |
| Intervention | `intervention` |

---

## 16. Prioritization engine

### 16.1 Definition

Assigns **numeric priority** to each task candidate for ordering within type pools. Distinct from Revision Engine priority (revision tasks use **engine priority_score** directly).

### 16.2 Study task priority (additive, aligned with RE v1.1 philosophy)

```
study_priority =
  0.35 · (importance / 100) +
  0.30 · ((100 - mastery) / 100) +
  0.20 · driver_boost(subject) +      // +0.2 if subject in readiness top-2 drivers
  0.10 · weekly_theme_boost(subject) +
  0.05 · ca_link_boost(concept)

Clamp to [0, 100]
```

### 16.3 Assessment task priority

```
mcq_priority = 0.5 · error_rate + 0.3 · (importance/100) + 0.2 · pyq_weak_flag
mains_priority = 0.4 · writing_gap + 0.3 · gs_paper_weight + 0.3 · (importance/100)
```

### 16.4 CA task priority

Uses CA relevance score from tool (0–100) directly as priority.

### 16.5 Revision tasks

```
revision_priority = revision_item.priority_score   // from Revision Engine — do not recompute
```

Tie-break: `concept_id` ASC (deterministic).

### 16.6 Intervention tasks

Fixed priority **100** — always first in merged list before sequencing policy reorders by time window.

---

## 17. Intervention engine

### 17.1 Purpose

Detect **risk states** requiring explicit mentor actions beyond normal planning — backlog, health collapse, streak break, overconfidence clusters.

### 17.2 Trigger matrix

| Trigger condition | Intervention type | Plan effect |
|---|---|---|
| `revision_health < 50` | `BACKLOG_RECOVERY` | Reduce load message + link to compressed backlog (RE §10.5) |
| `revision_fatigue ≥ 80` | `FATIGUE_RECOVERY` | Cut revision 40%; mandatory light CA only |
| `streak_at_risk && hour >= 20` | `STREAK_RESCUE` | Push notification task: "Complete 1 revision before midnight" |
| `RevisionBacklogIntervention` event | `BACKLOG_RECOVERY` | Same as row 1 |
| `overconfidence_count ≥ 5` in weak subjects | `OVERCONFIDENCE_AUDIT` | Add assessment drill on overconfident concepts |
| `days_to_exam < 30 && readiness < 50` | `EXAM_SPRINT_WARNING` | Escalate to faculty dashboard flag |
| `negative_marking_risk > 0.25` | `MCQ_DISCIPLINE` | Replace 1 MCQ block with revision |

### 17.3 Algorithm `InterventionEngine.evaluate`

```
INPUT:  MentorContext
OUTPUT: interventions[]

FOR rule IN TRIGGER_MATRIX ordered by severity DESC:
  IF rule.condition(context):
    interventions.append(build_intervention(rule))
    log mentor_interventions row (pending)

RETURN interventions
```

### 17.4 Intervention persistence

Each firing creates `mentor_interventions` row:

```json
{
  "intervention_type": "BACKLOG_RECOVERY",
  "severity": "high",
  "trigger_snapshot": { "revision_health": 48, "overdue_count": 12 },
  "recommended_actions": ["Reduce today's revision to 12 items", "Focus overdue high-yield only"],
  "status": "active|acknowledged|resolved"
}
```

### 17.5 Faculty escalation

`EXAM_SPRINT_WARNING` and persistent `revision_health < 40` for 7 days → emit `MentorFacultyEscalation` event for institute dashboard.

---

## 18. Motivation engine

### 18.1 Purpose

Select **template-based motivational copy** from deterministic state — not free-form LLM motivation in V1 core path.

### 18.2 Template selection

```
headline_key = f(readiness_band, revision_health_band, streak)
body_key     = f(primary_driver, streak, phase)

Examples:
  readiness >= 70 AND health >= 80 → mentor.daily.headline.strong_momentum
  streak_at_risk                   → mentor.daily.headline.streak_at_risk
  fatigue high                     → mentor.daily.headline.recovery_day
```

### 18.3 Params injection

Only numeric params from Twin snapshot — `{ streak_days, readiness, days_to_exam }`. LLM may **localize** template text but not change numbers.

### 18.4 Prohibited motivation

- Guaranteed selection promises ("You will clear prelims").
- Shaming language on low readiness.
- Comparison to other students (privacy).

### 18.5 Optional LLM polish (§21)

If enabled, LLM rewrites template with tone=supportive; **validator** ensures all numbers in output match params.

---

## 19. Explainability model

### 19.1 Principles (Blueprint Rule 4)

1. Every task has `reasoning.reason_codes[]` + `engine_refs`.
2. Every plan has root `reasoning_summary` citing Twin drivers.
3. Student never sees raw Weakness, Confidence, Revision Priority (Scoring v1.1).
4. Faculty sees intervention triggers with full snapshot.

### 19.2 Reason code catalog

| Code | Meaning | Typical engine_ref fields |
|---|---|---|
| `high_yield_fading` | Importance ≥80, retention <60 | importance, retention |
| `readiness_driver` | Subject in top-2 drivers | subject_id, driver_rank |
| `weakest_subject` | Weakest subject focus | mastery_avg |
| `revision_queue` | From Revision Engine | priority_score, revision_id |
| `pyq_high_yield_new` | PYQ concept unrated | pyq_count, importance |
| `ca_linked` | Recent CA link | ca_relevance |
| `assessment_gap` | High error rate | error_rate |
| `negative_marking_risk` | Guessing elevated | guessing_rate |
| `overconfidence_warning` | Flag set | overconfidence_flag |
| `intervention_backlog` | Health low | revision_health |
| `weekly_theme` | Weekly subject rotation | subject_id |
| `milestone_alignment` | Monthly milestone | milestone_id |

### 19.3 `reasoning_json` root on plan

```json
{
  "summary": "Today's plan prioritizes Economy retention (Readiness driver) and 12 scheduled revisions.",
  "top_factors": [
    { "label": "Low retention in Economy", "source": "twin.readiness.drivers[0]" },
    { "label": "8 overdue high-yield revisions", "source": "revision.overdue_count" }
  ],
  "planner_version": "daily_planner_v1",
  "deterministic_hash": "sha256:..."
}
```

### 19.4 "Why?" API

`GET /mentor/plans/{id}/why/{task_id}` returns expanded reasoning + taxonomy breadcrumb from `GetConceptMetadataTool`.

---

## 20. Rule-based deterministic layer

### 20.1 Authority

The rule layer is the **source of truth for plan content**. LLM is optional overlay.

### 20.2 Deterministic pipeline summary

```
Context → Interventions → Budgets → Candidate pools → Prioritize → Recommend → Sequence → Validate → Persist
```

Every step is a **pure function** of inputs + `MentorConfig` version.

### 20.3 `MentorConfig` version pins

| Key | Default | Affects |
|---|---|---|
| `DAILY_PLANNER_VERSION` | `daily_planner_v1` | §12 |
| `WEEKLY_PLANNER_VERSION` | `weekly_planner_v1` | §13 |
| `MONTHLY_PLANNER_VERSION` | `monthly_planner_v1` | §14 |
| `UPSC_PHASE_THRESHOLDS` | see §14.2 | phase selection |
| `TASK_DURATION_DEFAULTS` | revision 4, study 25, ... | budgets |

### 20.4 Deterministic hash

```
deterministic_hash = SHA256(
  canonical_json(tasks[].{task_type, concept_id, revision_id, sequence}) +
  planner_version +
  tool_snapshot_hashes
)
```

Stored on plan for replay verification.

### 20.5 Fallback when LLM disabled

`narrate_llm` node skipped; `summary_message` from template keys only — **full plan validity**.

---

## 21. LLM augmentation layer

### 21.1 Allowed LLM uses (V1)

| Use | Input | Output constraint |
|---|---|---|
| Plan summary narration | plan_json + motivation templates | Must not add tasks |
| Chat Q&A about **today's plan** | plan + twin snapshot | Cite only tool numbers |
| Task title polish | concept metadata + task_type | Same concept_id |
| Weekly theme description | weekly plan JSON | No new subjects |

### 21.2 Forbidden LLM uses

1. Selecting concepts not in tool outputs.
2. Computing Readiness, Mastery, Retention, Weakness.
3. Creating revision schedule or modifying priority.
4. Medical/legal/life advice beyond study guidance.
5. Answering exam questions without Knowledge Agent RAG (route to Knowledge Agent).

### 21.3 LLM call pattern

```
structured_context = build_llm_context(plan, twin_snapshot, allowed_concept_ids[])
response = LLM.generate(
  system=PromptRegistry.get("mentor_narration_v1"),
  user=structured_context,
  response_format=MentorNarrationSchema   // JSON schema constrained
)
validated = HallucinationGuard.validate(response, structured_context)
```

### 21.4 Model routing

| Scenario | Model tier |
|---|---|
| Daily narration | fast/cheap model |
| Chat complex | standard model |
| Faculty escalation summary | standard + higher max tokens |

Config: `MENTOR_LLM_ENABLED=true`, `MENTOR_LLM_MODEL` per environment.

---

## 22. Hallucination prevention architecture

### 22.1 Defense layers

```
Layer 1: Tool-only facts — LLM context lists allowed IDs and numbers
Layer 2: JSON schema — response_format enforces structure
Layer 3: HallucinationGuard — post-validation (§22.2)
Layer 4: Eval harness — offline regression (§31)
Layer 5: Human override — faculty correction loop
```

### 22.2 `HallucinationGuard.validate`

```
FOR each numeric claim in LLM output:
  IF claim not in engine_refs whitelist: REJECT → fallback template

FOR each concept_id in LLM output:
  IF concept_id not in allowed_set: REJECT

FOR each task added/removed vs deterministic plan:
  IF multiset mismatch: REJECT entire LLM overlay, use rule-only plan

IF rejection: log mentor_llm_validation_failures + use template
```

### 22.3 Citation whitelist

Only these numeric fields may appear in student-facing LLM text:

- `readiness`, `revision_health`, `retention`, `mastery`, `importance` (as "Exam Weight" band), `days_to_exam`, `streak_days`, `priority_score` (internal mentor view only — not student chat)

### 22.4 Zero-tolerance metric

**Hallucinated score citation rate** target: **0%** in production eval. Any non-whitelist number → incident alert.

---

## 23. Context assembly architecture

### 23.1 `MentorContext` bundle

```python
@dataclass
class MentorContext:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    plan_date: date
    now: datetime
    twin_snapshot: TwinSnapshotDTO
    twin_full: Optional[PreparationTwinDTO]
    revision_backlog: RevisionBacklogDTO
    plan_eligible: PlanEligibleDTO
    assessment_gaps: AssessmentGapsDTO
    ca_priorities: CAPrioritiesDTO
    pyq_insights: PYQInsightsDTO
    exam_calendar: ExamCalendarDTO
    preferences: StudentPreferencesDTO
    tool_snapshot_at: datetime
    snapshot_hashes: dict[str, str]
```

### 23.2 Token budget (LLM)

| Section | Max tokens |
|---|---|
| Twin snapshot | 800 |
| Plan JSON | 2000 |
| Chat history (M1) | 1500 |
| Concept metadata batch | 1000 |
| **Total cap** | 6000 |

Truncate weak topic lists to top 10; full data remains in deterministic layer.

### 23.3 Cache coherence

```
IF TwinUpdated OR RevisionPlanGenerated since tool_cache timestamp:
  bypass cache, refetch all tools
```

### 23.4 Context assembly diagram

```
         ┌─────────────┐
         │ ToolGateway │
         └──────┬──────┘
    ┌──────┼──────┬──────┬──────┐
    ▼      ▼      ▼      ▼      ▼
  Twin  Graph  Rev   Assess  PYQ/CA
    │      │      │      │      │
    └──────┴──────┴──────┴──────┘
                  │
                  ▼
           MentorContext
                  │
        ┌─────────┴─────────┐
        ▼                   ▼
  Deterministic         LLM Context
  Engines               (subset)
```

---

## 24. Agent workflows

### 24.1 Workflow: Proactive daily plan

```
Trigger: cron 05:30 student TZ OR StudentRegistered first day
Steps: assemble_context → intervene → GenerateDailyPlan → motivate → validate → persist
Output: mentor_plans + MentorPlanGenerated + WebSocket plan_generated
```

### 24.2 Workflow: On-demand daily plan

```
Trigger: GET /mentor/today (no active plan for date)
Same pipeline; cache result 120s
```

### 24.3 Workflow: Weekly plan

```
Trigger: Sunday 18:00 local OR GET /mentor/week
GenerateWeeklyPlan → persist horizon=weekly
Daily plans consume weekly themes via priority boost
```

### 24.4 Workflow: Monthly plan

```
Trigger: 1st of month 06:00 OR GET /mentor/month
GenerateMonthlyPlan → persist
```

### 24.5 Workflow: Chat turn (plan-aware)

```
Trigger: POST /mentor/chat (optional V1.1 surface)
1. Load M1 session
2. If intent = plan_question: answer from last plan + twin (LLM constrained)
3. If intent = replan_request: rerun GenerateDailyPlan with prefs override
4. If intent = knowledge: route Supervisor → Knowledge Agent
5. Update M1 checkpoint
```

### 24.6 Workflow: Post-assessment replan hint

```
Trigger: AssessmentCompleted
Lightweight: enqueue job to add assess_tasks suggestion to next day plan metadata (no same-day auto replan unless config enabled)
```

---

## 25. Event-driven triggers

### 25.1 Events consumed

| Event | Action |
|---|---|
| `StudentRegistered` | Provision; schedule first daily plan |
| `TwinUpdated` | Invalidate cache; replan if drivers changed materially (Δ readiness ≥ 3) |
| `RevisionPlanGenerated` | Invalidate revision tool cache |
| `RevisionBacklogIntervention` | Run InterventionEngine; optional immediate replan |
| `RevisionHealthRecomputed` | Check intervention thresholds |
| `AssessmentCompleted` | Optional next-day assess hint; invalidate assessment cache |
| `CurrentAffairsPublished` | Invalidate CA cache; next plan picks up |
| `MentorPlanOverridden` | Load override as display plan |
| `StudentPreferencesUpdated` | Replan next day |

### 25.2 Events emitted

| Event | Payload | Consumers |
|---|---|---|
| **`MentorPlanGenerated`** | plan_id, horizon, plan_date, task_count, deterministic_hash | WebSocket, Analytics, Dashboard |
| **`MentorInterventionTriggered`** | intervention_id, type, severity | Notifications, Faculty |
| **`MentorFacultyEscalation`** | student_id, reason | Institute dashboard |
| **`MentorLLMValidationFailed`** | plan_id, failure_reason | Observability |
| **`MentorPlanSuperseded`** | old_plan_id, new_plan_id | Audit |

### 25.3 Idempotency

Plan generation dedupe:

```
IF active plan exists for (student, plan_date, horizon) AND regenerate=false:
  RETURN existing
```

Event consumers use `mentor_processed_events(event_id)`.

---

## 26. Read models

### 26.1 `mentor_plan_summary` (denormalized)

| Column | Source |
|---|---|
| `student_id`, `plan_date`, `horizon` | PK |
| `plan_id` | FK |
| `task_count` | |
| `revision_count`, `study_count`, `assess_count` | |
| `total_minutes` | |
| `headline_key` | motivation |
| `deterministic_hash` | |
| `generated_at` | |

Refresh: synchronous on plan persist.

### 26.2 `mentor_active_plan_view`

Materialized view: latest `status=active` plan per `(student, horizon)`.

### 26.3 Redis cache

| Key | TTL |
|---|---|
| `mentor:today:{tenant}:{student}` | 120s |
| `mentor:week:{tenant}:{student}` | 300s |
| `mentor:tools:{tenant}:{student}` | 60s |

Invalidate on `MentorPlanGenerated`, `TwinUpdated`.

---

## 27. Database schemas

### 27.1 `mentor_plans`

| Column | Type | Nullable | Description |
|---|---|:---:|---|
| `id` | UUID | no | PK |
| `tenant_id` | UUID | no | |
| `student_id` | UUID | no | |
| `exam_id` | string | no | |
| `plan_date` | date | no | anchor date |
| `horizon` | enum | no | `daily\|weekly\|monthly` |
| `status` | enum | no | `active\|superseded\|archived` |
| `phase` | enum | no | UPSC phase at generation |
| `plan_json` | JSONB | no | §12.6 schema |
| `reasoning_json` | JSONB | no | §19.3 root |
| `motivation_json` | JSONB | no | §18 |
| `planner_version` | string | no | |
| `deterministic_hash` | string | no | |
| `tool_snapshot_at` | timestamptz | no | |
| `llm_narration` | JSONB | yes | optional overlay |
| `llm_validated` | bool | yes | |
| `generated_by` | enum | no | `scheduler\|on_demand\|chat\|faculty regen` |
| `row_version` | int | no | |
| `created_at` | timestamptz | no | |
| `updated_at` | timestamptz | no | |

**Unique:** `(tenant_id, student_id, plan_date, horizon) WHERE status='active'`

### 27.2 `mentor_plan_items` (optional normalization)

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `plan_id` | UUID FK | |
| `sequence` | int | |
| `task_type` | enum | |
| `concept_id` | string nullable | |
| `revision_id` | UUID nullable | |
| `estimated_minutes` | int | |
| `reasoning_json` | JSONB | per-task |
| `title` | string | |

V1 may use `plan_json.tasks[]` only; items table for analytics queries Phase 2.

### 27.3 `mentor_interventions`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `tenant_id`, `student_id` | UUID | |
| `intervention_type` | enum | §17.2 |
| `severity` | enum | low/medium/high |
| `trigger_snapshot` | JSONB | |
| `status` | enum | active/acknowledged/resolved |
| `plan_id` | UUID nullable | FK if plan linked |
| `created_at`, `resolved_at` | timestamptz | |

### 27.4 `mentor_session_memory`

See §4.2.

### 27.5 `mentor_agent_events`

| Column | Type | Description |
|---|---|---|
| `event_id` | UUID PK | |
| `tenant_id`, `student_id` | UUID | |
| `event_type` | enum | §25.2 |
| `payload` | JSONB | |
| `plan_id` | UUID nullable | |
| `occurred_at`, `recorded_at` | timestamptz | |

### 27.6 `mentor_plan_overrides`

| Column | Type | Description |
|---|---|---|
| `id` | UUID PK | |
| `plan_id` | UUID FK | original |
| `override_plan_json` | JSONB | faculty edited |
| `faculty_id` | UUID | |
| `reason` | text | |
| `created_at` | timestamptz | |

### 27.7 `mentor_processed_events`

Idempotency for inbound events — same pattern as Twin/LG.

### 27.8 ER diagram

```
students 1──* mentor_plans
students 1──* mentor_interventions
students 1──* mentor_session_memory
mentor_plans 1──* mentor_plan_items (optional)
mentor_plans 1──* mentor_plan_overrides
students 1──* mentor_agent_events

(read-only logical FKs to concepts, revisions via IDs in JSON — no DB FK to other contexts)
```

---

## 28. API contracts

Base: `/api/v1/mentor`. Auth: student JWT; tenant scoped.

### 28.1 `GET /api/v1/mentor/today`

Returns active daily plan; generates if missing.

**Response:**

```json
{
  "plan_id": "uuid",
  "plan_date": "2026-06-18",
  "phase": "BALANCED",
  "summary": "Today's plan prioritizes Economy retention and 12 revisions.",
  "tasks": [ "..." ],
  "motivation": { "headline": "...", "body": "..." },
  "meta": { "generated_at": "...", "planner_version": "daily_planner_v1" }
}
```

SLA: p95 < **200ms** cached; < **2s** cold generation.

### 28.2 `GET /api/v1/mentor/week`

Weekly thematic plan (§13).

### 28.3 `GET /api/v1/mentor/month`

Monthly strategic plan (§14).

### 28.4 `GET /api/v1/mentor/plans/{plan_id}`

Full plan + reasoning_json.

### 28.5 `GET /api/v1/mentor/plans/{plan_id}/why/{task_id}`

Expanded explainability (§19.4).

### 28.6 `POST /api/v1/mentor/plans/regenerate`

Body: `{ "horizon": "daily", "plan_date": "..." }`. Rate limit: 3/day/student. Emits supersede + new plan.

### 28.7 `POST /api/v1/mentor/chat` (optional)

Streaming via WebSocket `/ws` event `token`. Chat must not bypass tool layer.

### 28.8 Internal — `POST /api/v1/internal/mentor/generate`

Supervisor/cron invoker. RBAC: `system`, `mentor_scheduler`.

### 28.9 Presentation filtering

Student responses strip internal fields (`priority_score`, `weakness_internal`). Aligns with Scoring v1.1 §7.

---

## 29. Prompt architecture

### 29.1 Registry layout (`05-agent-architecture.md` §20)

```
prompts/
  mentor/
    narration_v1.yaml
    chat_plan_qa_v1.yaml
    intervention_copy_v1.yaml
  registry.yaml
```

### 29.2 Prompt file structure

```yaml
id: mentor_narration_v1
version: 1
model_min: gpt-4o-mini
system: |
  You are a UPSC preparation mentor narrator. You ONLY restate facts from CONTEXT.
  Never invent scores, concept IDs, or tasks not in PLAN.
  Never promise exam selection.
user_template: |
  CONTEXT: {{structured_context_json}}
  PLAN: {{plan_json}}
output_schema: MentorNarrationSchema
```

### 29.3 Versioning

- Prompt changes bump `prompt_version` on `llm_narration` metadata.
- Eval harness runs on prompt version change before deploy.
- Rollback: route traffic to previous prompt version via feature flag.

### 29.4 A/B testing (Phase 2)

Shadow traffic 5% to `narration_v2`; compare eval scores before promotion.

---

## 30. Safety and governance

### 30.1 Content safety

| Category | Policy |
|---|---|
| Exam integrity | No live exam paper leaks; refuse if detected |
| Harassment | Block toxic student inputs; standard moderation API |
| Medical advice | Redirect to professionals |
| Political neutrality | CA explanations factual; no partisan advocacy |

### 30.2 RBAC

| Role | Access |
|---|---|
| `student` | Own plans, chat |
| `faculty` | Batch student plans read; override |
| `institute_admin` | Institute analytics |
| `mentor_agent` | Internal tool service account |
| `system` | Scheduler generate |

### 30.3 Rate limits

| Endpoint | Limit |
|---|---|
| `/mentor/today` | 60/min/student |
| `/mentor/regenerate` | 3/day/student |
| `/mentor/chat` | 30/min/student |
| Internal generate | 1000/min/tenant |

### 30.4 Audit

All plan generations log: `{ request_id, student_id, deterministic_hash, planner_version, tool_snapshot_at, llm_used }`.

Faculty overrides immutable audit trail.

### 30.5 DPDP / privacy

- Plans contain `concept_id` only — no PII in plan JSON.
- Faculty batch views enforce min cohort = 5 for aggregates (Scoring v1.1).
- Student can export plans via data export API (future).

---

## 31. Observability

### 31.1 Metrics (Prometheus)

| Metric | Type |
|---|---|
| `mentor_plan_generation_duration_seconds` | histogram |
| `mentor_tool_call_duration_seconds` | histogram by tool |
| `mentor_llm_validation_failures_total` | counter |
| `mentor_interventions_triggered_total` | counter by type |
| `mentor_deterministic_hash_mismatch_total` | counter |
| `mentor_degraded_mode_total` | counter |

### 31.2 Tracing

OpenTelemetry span chain:

```
mentor.generate_daily → tool.batch → planning.engine → persist → llm.narrate
```

Propagate `request_id`, `tenant_id`, `student_id`, `plan_id`.

### 31.3 Eval harness (`05-agent-architecture.md` §18)

| Eval | Target |
|---|---|
| Plan accuracy (tasks match golden rule output) | **100%** on fixed fixtures |
| Hallucination rate (numeric) | **0%** |
| Recommendation quality (human rubric) | ≥ 4/5 |
| Explainability completeness | 100% tasks have reason_codes |

Store eval runs in `mentor_eval_runs` table.

### 31.4 Logging

Structured JSON logs; **never** log full LLM prompts with PII in production — hash context instead.

---

## 32. Performance requirements

V1 scale: **10,000 students** (`MASTER_IMPLEMENTATION_PLAN.md`).

### 32.1 Latency targets

| Operation | p95 |
|---|---|
| Tool batch (parallel) | **400ms** |
| Deterministic daily plan | **800ms** |
| LLM narration (optional) | **3s** additional |
| `GET /mentor/today` cached | **40ms** |
| `GET /mentor/today` cold generate | **2s** |
| Weekly plan generation | **1.5s** |
| Monthly plan generation | **2s** |

### 32.2 Throughput

| Workload | Target |
|---|---|
| Proactive daily batch (10k) | **≤25 min** (05:00–06:00 window) |
| Concurrent on-demand | 200 RPS tenant-wide |

### 32.3 Scheduler sharding

Celery queue `mentor.plan.daily` partition by `{tenant_id}:{shard}`; 20 workers default.

---

## 33. Failure recovery

### 33.1 Tool failure

| Scenario | Behavior |
|---|---|
| Single tool fail | Degraded plan per §5.5 |
| Twin down | Graph+Revision only; flag `twin_degraded` |
| Revision down | Study+assess only; critical alert |
| All tools down | Return last plan if <24h else 503 |

### 33.2 LLM failure

Skip narration; serve rule-only plan. Log `llm_unavailable`. **Never** block plan delivery.

### 33.3 Persist failure

Retry 3× optimistic lock. On failure: return computed plan without persist + queue async persist job — client receives plan with `persist_pending=true`.

### 33.4 Replay / backfill

```
RegeneratePlans(student, from_date, to_date):
  FOR each date: run deterministic pipeline with historical tool snapshots IF available
  ELSE skip with warning
```

Used after planner version bump — compare `deterministic_hash` distribution.

### 33.5 Disaster recovery

- `mentor_plans` restored from PostgreSQL PITR.
- Plans reproducible from upstream events + planner version (approximate if tool snapshots missing).

---

## 34. Multi-agent future architecture

### 34.1 V1 scope

Mentor Agent implements **planning orchestration** only. Supervisor routes other intents.

### 34.2 Agent interaction map (future)

```
Supervisor
  ├── Mentor Agent (plans, interventions)     ← this spec
  ├── Revision Agent (narration only)         ← RE owns schedule
  ├── Assessment Agent (evaluation)           ← separate spec
  ├── Knowledge Agent (RAG tutor)             ← separate spec
  ├── Current Affairs Agent (CA explain)      ← separate spec
  ├── Faculty Agent (batch insights)          ← institute
  └── Institute Agent (cohort ops)            ← B2B
```

### 34.3 Shared `GraphState` (`05-agent-architecture.md` §17)

Future: Supervisor populates `GraphState.tool_results` once; sub-agents read subset — reduces duplicate tool calls.

### 34.4 Conflict resolution

When Knowledge Agent suggests study topic conflicting with Mentor plan:

```
Supervisor policy: Revision queue + daily plan tasks WIN unless faculty override
Knowledge suggestion appended as optional "deep dive" — not replacing plan tasks
```

### 34.5 Revision Agent clarification

Blueprint "Revision Agent" in V1 = **Revision Engine narration hooks** inside Mentor intervention copy — **not** a separate scheduling agent.

---

## Appendix A — UPSCPhasePolicy detail

```
UPSCPhasePolicy.resolve(days_to_exam, target_stages, readiness):
  IF days_to_exam <= 60:  RETURN SPRINT
  IF days_to_exam <= 120 AND 'prelims' IN target_stages: RETURN PRELIMS_FOCUS
  IF days_to_exam <= 180 AND mains mock gap: RETURN MAINS_FOCUS
  IF days_to_exam > 365: RETURN FOUNDATION
  RETURN BALANCED
```

Time budgets from §12.3 keyed by phase enum.

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `DAILY_PLANNER_VERSION` | `daily_planner_v1` | |
| `DEFAULT_DAILY_STUDY_MINUTES` | 180 | |
| `MENTOR_LLM_ENABLED` | true | |
| `MENTOR_REGENERATE_DAILY_LIMIT` | 3 | |
| `MENTOR_TOOL_CACHE_TTL_SECONDS` | 60 | |
| `MENTOR_TODAY_CACHE_TTL_SECONDS` | 120 | |
| `MENTOR_REPLAN_READINESS_DELTA` | 3 | TwinUpdated trigger |
| `MENTOR_MAX_STUDY_SAME_TOPIC` | 2 | diversity |
| `MENTOR_FACULTY_ESCALATION_HEALTH` | 40 | 7-day sustained |
| `PROMPT_VERSION_NARRATION` | `mentor_narration_v1` | |

---

## Appendix C — Tool JSON schema version

All tools return `{ "schema_version": "mentor_tool_v1", "data": { ... } }` for forward compatibility.

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `PREPARATION_TWIN_SPECIFICATION.md` | Read-only tools §6; never write Twin; drivers, fatigue, streak |
| `REVISION_ENGINE_SPECIFICATION.md` (v1.1) | Queue authoritative §8; priority_factors in reasoning; no revision writes |
| `LEARNING_GRAPH_SPECIFICATION.md` | GetPlanEligibleConcepts §7; no graph writes; weak frontier |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | No Weakness/Confidence student exposure §19; Readiness drivers R8 |
| `SCORING_ENGINE_SPECIFICATION.md` | Readiness/prediction formulas computed in Twin, not Mentor |
| `EXAM_DOMAIN_SPECIFICATION.md` | Taxonomy labels; GS mapping; CA edges |
| `MASTER_IMPLEMENTATION_PLAN.md` | S8 Mentor sprint; Supervisor; eval harness; tool-only DB access |
| `05-agent-architecture.md` | Multi-agent; LangGraph; prompt registry; eval framework |
| Blueprint Rule 5 | Scores owned by engines — §2 |
| Blueprint Rule 4 | Explainability — §19 |
| Blueprint Rule 3 | AI never source of truth — §1, §20 |

---

*End of Mentor Agent Specification v1.0. Implement `MentorOrchestrator` as the sole writer of `mentor_plans` and `mentor_interventions`; all student state reads flow through `ToolGateway`; deterministic planning engines are authoritative over LLM narration.*
