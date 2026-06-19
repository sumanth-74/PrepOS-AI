# PrepOS AI — Current Affairs Engine Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for Current Affairs bounded context
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`, `EXAM_DOMAIN_SPECIFICATION.md`, `LEARNING_GRAPH_SPECIFICATION.md`, `REVISION_ENGINE_SPECIFICATION.md` (v1.1), `PREPARATION_TWIN_SPECIFICATION.md`, `MENTOR_AGENT_SPECIFICATION.md`, `ASSESSMENT_ENGINE_SPECIFICATION.md`, `PYQ_INTELLIGENCE_SPECIFICATION.md`
Authoring lens: Principal Knowledge Systems Architect · UPSC Domain Expert · Staff Backend Architect · Learning Scientist · News Intelligence Platform Architect

> **Scope.** This document defines the **Current Affairs Engine**: ingestion, normalization, concept linking, item-level importance scoring, student engagement tracking, read models, events, APIs, and integrations. It is the implementation contract for `current_affairs`, `current_affairs_mappings`, `CURRENT_AFFAIRS_OF` relationship sync, `GetCurrentAffairsPrioritiesTool` backing data, and **CASub** inputs for Readiness (V2).
>
> **Non-goals:** UI layout, marketing, sprint tasks, SQL DDL, long-form CA explanation (Current Affairs Agent), RAG chunk ingestion (Knowledge Agent), PYQ mapping, concept Importance (PYQ Intelligence). Mastery/Retention formulas live in Scoring specs; **concept score columns** on `student_concept_progress` are updated by **Learning Graph Service** via `StudySessionLogged` — CA never writes mastery/retention directly.
>
> **Core invariant:** the Current Affairs Engine is the **sole writer** of CA catalog data and mappings. It emits `CurrentAffairsPublished` and `CurrentAffairsEngaged`; downstream engines consume read ports and events — never cross-context repository imports.

---

## 0. Canonical requirements map

This document is the authoritative answer to the 32 required areas:

| # | Requirement | Primary section |
|---|---|---|
| 1 | Purpose and bounded context | §1 |
| 2 | Ownership boundaries | §2 |
| 3 | V1 vs V2 scope matrix | §3 |
| 4 | CA data model | §4 |
| 5 | Ingestion pipeline architecture | §5 |
| 6 | Normalization and deduplication | §6 |
| 7 | Verification and publish workflow | §7 |
| 8 | CA item importance scoring | §8 |
| 9 | Concept linking workflow | §9 |
| 10 | Mapping validation rules | §10 |
| 11 | `CURRENT_AFFAIRS_OF` relationship sync | §11 |
| 12 | Student engagement model | §12 |
| 13 | Study session bridge | §13 |
| 14 | CASub computation (Readiness inputs) | §14 |
| 15 | CA relevance data contract (Revision) | §15 |
| 16 | Event-driven architecture | §16 |
| 17 | `CurrentAffairsPublished` event contract | §17 |
| 18 | `CurrentAffairsEngaged` event contract | §18 |
| 19 | Integration with Learning Graph | §19 |
| 20 | Integration with Mentor Agent | §20 |
| 21 | Integration with Revision Engine | §21 |
| 22 | Integration with Preparation Twin | §22 |
| 23 | Integration with Assessment Engine | §23 |
| 24 | Integration with Knowledge / CA Agent | §24 |
| 25 | Read models | §25 |
| 26 | Database schemas | §26 |
| 27 | API contracts | §27 |
| 28 | Batch jobs and archival | §28 |
| 29 | Content licensing and provenance | §29 |
| 30 | Caching strategy | §30 |
| 31 | Failure recovery | §31 |
| 32 | Performance requirements | §32 |
| 33 | Observability | §33 |
| 34 | Future AI-assisted linking and RAG | §34 |
| 35 | Consistency checklist | Appendix D |

---

## 1. Purpose and bounded context

### 1.1 What the Current Affairs Engine is

The Current Affairs Engine transforms **time-stamped news and government releases** into **concept-linked, prioritizable study artifacts** that feed Mentor daily plans, Revision urgency, Twin CA coverage, and (V2) Readiness `CASub`.

```
News / gov sources              Current Affairs Engine (this spec)        Downstream (read/events)
──────────────────              ────────────────────────────────          ─────────────────────────
PIB, Hindu, ES, faculty    ──►  ingest → normalize → link → score   ──►  Mentor (CA reading tasks)
                                 current_affairs / mappings              Revision (CARelevanceScore)
                                 engagement tracking                     Twin (academic.ca)
                                 CURRENT_AFFAIRS_OF edges                Assessment (ca_quiz V2)
                                       │
                                       ▼
                          CurrentAffairsPublished / CurrentAffairsEngaged
                          → StudySessionLogged (via bridge) → Learning Graph
```

### 1.2 What the Current Affairs Engine is NOT

| Misconception | Reality |
|---|---|
| Permanent syllabus node | CA items are **events**; concepts are permanent (EXAM_DOMAIN P5) |
| Concept Importance owner | **Exam Weight** = PYQ Intelligence; CA has **item-level** `importance_score` |
| Chat / explainer | **Current Affairs Agent** narrates; this engine owns **catalog + links** |
| Learning Graph writer | Never updates `mastery_score` / `retention_score`; bridges via `StudySessionLogged` |
| RAG corpus owner | Knowledge Agent ingests chunks separately (optional cross-ref by `ca_id`) |
| Duplicate concept creator | Links to existing `concept_id` only — never forks syllabus |

### 1.3 Bounded context (DDD)

```
┌──────────────────────────────────────────────────────────────────┐
│            Current Affairs Context (this spec)                      │
│  CAIngestionService · CALinkingService · CAImportanceEngine        │
│  CAEngagementService · CAReadModelProjector                        │
│  current_affairs · current_affairs_mappings · student_ca_engagement│
└───────────────┬──────────────────────────────────────────────────┘
                │ read catalog              │ events
    ┌───────────┼───────────┐               ▼
    ▼           ▼           ▼        Mentor / Revision / Twin / Assessment
 Exam Domain  Learning     Study
 (concepts)   Graph read   (session bridge)
```

**Anti-corruption:** all concept metadata via `ExamDomainReadPort`; graph reads via `LearningGraphReadPort`.

### 1.4 UPSC domain semantics

| Dimension | CA behavior |
|---|---|
| **Cross-cutting** | CA links across GS papers via `current_affairs_linkable` concepts |
| **Prelims sprint** | Higher daily CA slots when `days_to_exam < 90` (Mentor §10) |
| **Mains linkage** | `link_type=direct` on mains-relevant concepts → Mains writing prompts (V2) |
| **PIB priority** | Official releases score higher in item importance (§8) |
| **Decay** | Published items lose plan priority after 30d; archived after 180d |
| **No guessing links** | Unmapped items stay in review queue — never auto-linked below confidence threshold |

### 1.5 Success criteria

1. Every **published** CA item has ≥1 verified mapping OR explicit `publish_unmapped=false` block.
2. Auto-published mappings have `confidence ≥ 0.85` (EXAM_DOMAIN §8.3).
3. `GET /current-affairs` p95 **< 80ms** (cached feed).
4. `GetCurrentAffairsPrioritiesTool` p95 **< 50ms** (cached).
5. `CurrentAffairsEngaged` → Twin CA subsection updated within **p95 < 2s**.
6. Zero CA service writes to `student_concept_progress` score columns (architectural test).

---

## 2. Ownership boundaries

### 2.1 Write ownership matrix

| Data | Sole writer | CA Engine relationship |
|---|---|---|
| `current_affairs` | **CA Service** | Authoritative CA catalog |
| `current_affairs_mappings` | **CA Service** | Concept links |
| `ca_sources` | **CA Service** | Provenance / license |
| `ca_ingestion_batches` | **CA Service** | Batch audit |
| `ca_mapping_review_queue` | **CA Service** | Faculty workflow |
| `student_ca_engagement` | **CA Service** | Per-student read/complete tracking |
| `concept_ca_stats` | **CA Service** | Denormalized link counts |
| `concept_relationships` (`CURRENT_AFFAIRS_OF`) | **CA Service** | Synced from mappings |
| `student_concept_progress` | Learning Graph | **Never written** |
| `StudySessionLogged` event | Study module OR CA bridge | CA triggers via port |
| `concepts.importance` | PYQ Intelligence | **Never written** |

### 2.2 Forbidden operations

1. CA worker calling `ConceptProgressRepository.save_node()`.
2. Creating new `concept_id` rows for news topics (use `meta_current_affairs` bridge concepts from catalog only).
3. Publishing CA with mappings to `current_affairs_linkable=false` concepts.
4. Emitting `CurrentAffairsPublished` before mappings verified (unless admin override with audit).
5. Link weights summing to > 1.0 per `ca_id`.
6. Using archived CA items in Mentor priority feed.

---

## 3. V1 vs V2 scope matrix

Master Plan **S17 / P7** is V2; V1 runs with **degraded CA** (Mentor empty feed OK; Readiness redistributes absent `CASub`).

| Capability | V1 (minimal) | V2 (full S17) |
|---|---|---|
| Manual CA publish + faculty mapping | ✓ | ✓ |
| Automated ingestion (PIB RSS, etc.) | Optional seed | ✓ |
| AI-suggested linking | Queue only | Auto at ≥0.85 confidence |
| `GetCurrentAffairsPrioritiesTool` | Manual seed items | Full feed |
| `CurrentAffairsEngaged` | ✓ | ✓ |
| Twin `coverage_90d` | Basic counts | Full |
| `CASub` in Readiness | **Absent** (null) | ✓ |
| `ca_quiz` assessments | Stub | ✓ |
| CA Agent explanation | Stub 501 | ✓ |
| RAG cross-link | — | Optional `ca_id` in chunks |

**V1 bootstrap:** seed 30–50 curated CA items with verified mappings so Mentor CA slots are non-empty in demos.

---

## 4. CA data model

### 4.1 CA item entity — `current_affairs`

| Column | Type | Description |
|---|---|---|
| `ca_id` | UUID PK | |
| `tenant_id` | UUID nullable | null = platform-global |
| `exam_id` | string | e.g. `upsc_cse` |
| `title` | string | Headline (max 500) |
| `summary` | text | Structured summary (markdown safe) |
| `body` | text nullable | Full text if licensed |
| `published_date` | date | UTC date of event |
| `published_at` | timestamptz | Precise publish time for recency |
| `source_id` | UUID FK | `ca_sources` |
| `source_url` | string nullable | Original link |
| `category` | enum | `national`, `international`, `economy`, `science_env`, `polity_governance`, `reports` |
| `exam_stages` | JSONB | `["prelims","mains"]` subset |
| `importance_score` | decimal(5,2) | Item priority 0–100 (§8) |
| `status` | enum | `draft`, `published`, `archived` |
| `mapping_status` | enum | `unmapped`, `partial`, `mapped`, `review_required` |
| `catalog_version` | int | Bumps on publish |
| `ingestion_batch_id` | UUID nullable | |
| `created_at` | timestamptz | |
| `published_by` | UUID nullable | |

### 4.2 Mapping entity — `current_affairs_mappings`

Per EXAM_DOMAIN §8.3:

| Column | Type | Description |
|---|---|---|
| `mapping_id` | UUID PK | |
| `ca_id` | UUID FK | |
| `concept_id` | string FK | `current_affairs_linkable=true` |
| `link_weight` | decimal(4,3) | 0.0–1.0 |
| `link_type` | enum | `direct`, `contextual`, `background` |
| `mapped_by` | enum | `system`, `faculty`, `admin` |
| `confidence` | decimal(3,2) | AI suggestions; ≥0.85 auto-publish |
| `verified` | bool | Production feed requires true |
| `mapping_rationale` | text nullable | Faculty note / AI explanation |
| `created_at` | timestamptz | |

**Invariant:** `SUM(link_weight) GROUP BY ca_id` ≤ **1.0** (SHOULD = 1.0 for published items).

### 4.3 Engagement entity — `student_ca_engagement`

| Column | Type | Description |
|---|---|---|
| `tenant_id` | UUID | |
| `student_id` | UUID | |
| `ca_id` | UUID | |
| `engaged_at` | timestamptz | First open |
| `completed_at` | timestamptz nullable | Marked done |
| `dwell_seconds` | int nullable | Reading time |
| `source` | enum | `mentor_task`, `feed`, `search` |
| `mentor_plan_item_id` | UUID nullable | |

PK: `(tenant_id, student_id, ca_id)`.

### 4.4 Category → domain subject map

| `category` | Primary catalog anchor |
|---|---|
| `national` | `upsc.cse.current_affairs.national` |
| `international` | `upsc.cse.current_affairs.international` |
| `economy` | `upsc.cse.current_affairs.economy` |
| `science_env` | `upsc.cse.current_affairs.science_env` |
| `polity_governance` | `upsc.cse.current_affairs.polity_governance` |
| `reports` | `upsc.cse.current_affairs.reports_indices` |

Used for feed filtering and importance category boost.

---

## 5. Ingestion pipeline architecture

### 5.1 Pipeline stages

```
Source (RSS / API / manual)
      │
      ▼
┌─────────────┐
│ Fetch       │  rate-limited per source; respect robots/license
└──────┬──────┘
       ▼
┌─────────────┐
│ Parse       │  extract title, date, body/summary
└──────┬──────┘
       ▼
┌─────────────┐
│ Dedupe      │  §6
└──────┬──────┘
       ▼
┌─────────────┐
│ License chk │  §29
└──────┬──────┘
       ▼
┌─────────────┐
│ Persist     │  status=draft; mapping_status=unmapped
└──────┬──────┘
       ▼
┌─────────────┐
│ Link        │  §9 (AI suggest → review OR faculty)
└──────┬──────┘
       ▼
┌─────────────┐
│ Score       │  §8 importance_score
└──────┬──────┘
       ▼
┌─────────────┐
│ Publish     │  status=published; emit CurrentAffairsPublished
└─────────────┘
```

### 5.2 V2 source connectors (planned)

| Source | Method | Frequency |
|---|---|---|
| PIB press releases | RSS / API | Hourly |
| PRS Legislative | RSS | Daily |
| The Hindu (licensed) | Licensed feed | Daily |
| Economic Survey excerpts | Manual batch | Annual |
| Faculty upload | Admin API | Ad hoc |

### 5.3 Ingestion batch — `ca_ingestion_batches`

Same pattern as PYQ (`PYQ_INTELLIGENCE_SPECIFICATION.md` §4.4): `batch_id`, `source_id`, `stats_json`, `status`.

---

## 6. Normalization and deduplication

### 6.1 Dedupe key

```
dedupe_key = hash(normalize(title), published_date, source_id)
```

Near-duplicate body similarity (V2): cosine > 0.92 on embedding → merge as `duplicate_of_ca_id`.

### 6.2 Title normalization

- Lowercase, strip punctuation, collapse whitespace.
- Remove source-specific suffixes ("| PIB", "- The Hindu").

### 6.3 Date handling

- Prefer official release date over crawl time.
- `published_at` defaults to noon UTC on `published_date` if time unknown.

---

## 7. Verification and publish workflow

### 7.1 Publish prerequisites

```
PublishCA(ca_id):
  VALIDATE status == draft OR republish
  VALIDATE source license active
  VALIDATE importance_score computed
  IF mapping_status != 'mapped':
     REQUIRE admin force_publish=true WITH audit reason
  FOR each mapping: verified == true OR mapped_by == admin
  VALIDATE sum(link_weight) <= 1.0
  status = published
  catalog_version++
  EMIT CurrentAffairsPublished
```

### 7.2 Mapping status machine

```
unmapped → review_required → partial → mapped
                ↑                    │
                └── AI low conf ─────┘
```

### 7.3 Archival

```
ArchiveCA(ca_id):
  status = archived
  Remove from active feeds (not deleted)
  CARelevanceScore naturally drops (Revision §9.5)
  EMIT CurrentAffairsArchived (optional analytics)
```

Default auto-archive: `published_at < now - CA_ARCHIVE_DAYS` (default **180**).

---

## 8. CA item importance scoring

### 8.1 Purpose

**Item-level** `importance_score` ranks CA in daily feeds — **separate** from concept Exam Weight (PYQ-driven `concepts.importance`).

### 8.2 Components

| Component | Weight | Description |
|---|---:|---|
| Source tier | 0.30 | PIB > PRS > licensed press > faculty |
| Recency | 0.25 | Decay from `published_at` |
| Category exam salience | 0.20 | Category × stage weights |
| Mapping quality | 0.15 | Avg mapping confidence × link coverage |
| Faculty boost | 0.10 | Tenant faculty flag (optional) |

### 8.3 Source tier scores

| Source tier | Score |
|---|---:|
| `pib_official` | 100 |
| `prs_legislative` | 95 |
| `economic_survey` | 95 |
| `licensed_press` | 85 |
| `institute_curated` | 80 |
| `faculty_upload` | 75 |

### 8.4 Recency score

```
days = days_since(published_at)
recency = 100 * exp(-CA_ITEM_RECENCY_LAMBDA * days)    // default λ=0.08
```

### 8.5 Category salience

```
cat_score = weighted_mean(concept.prelims_relevance, concept.mains_relevance)
            over mapped concepts, weighted by link_weight
IF no mappings: use category default from §4.4 topic prelims/mains relevance
```

### 8.6 Final formula

```
importance_raw = 0.30*source_tier + 0.25*recency + 0.20*cat_score
               + 0.15*mapping_quality + 0.10*faculty_boost
importance_score = round(clamp(importance_raw, 0, 100), 2)
```

Recomputed on mapping change and nightly for recency decay.

---

## 9. Concept linking workflow

### 9.1 Linking modes

| Mode | V1 | V2 |
|---|---|---|
| Faculty manual | Primary | Primary |
| Admin bulk | Seed | ✓ |
| AI-suggested | Review queue | Auto if confidence ≥ 0.85 |
| Rule-based keyword | Bootstrap | Assist only |

### 9.2 Algorithm `SubmitCALinks`

```
INPUT: ca_id, links[{concept_id, link_weight, link_type, confidence?}]
1.  VALIDATE concepts current_affairs_linkable=true, active
2.  VALIDATE sum(link_weight) <= 1.0
3.  IF any confidence < CA_AUTO_PUBLISH_CONFIDENCE(0.85):
       verified=false; mapping_status=review_required
4.  ELSE IF mapped_by=faculty: verified=true on confirm
5.  UPSERT current_affairs_mappings
6.  Sync CURRENT_AFFAIRS_OF edges (§11)
7.  Recompute importance_score
8.  IF ca.status==published: EMIT CurrentAffairsPublished (mapping_updated)
```

### 9.3 Review queue — `ca_mapping_review_queue`

Mirror PYQ review queue: `ca_id`, `priority`, `assigned_faculty_id`, `sla_due_at`, `status`.

**Priority:** high `importance_score` draft items, exam season, unmapped backlog age.

### 9.4 Typical mapping cardinality

| link_type | Typical weight |
|---|---|
| `direct` | 0.30–0.50 each (1–2 concepts) |
| `contextual` | 0.15–0.25 |
| `background` | 0.10–0.20 |

Target **2–4 concepts** per CA item (EXAM_DOMAIN §8.3).

### 9.5 Worked example (EXAM_DOMAIN §8.4)

**CA:** Digital Personal Data Protection Act, 2023

| concept_id | link_weight | link_type |
|---|---:|---|
| `...fundamental_rights.article_21` | 0.35 | direct |
| `...fundamental_rights.overview` | 0.20 | contextual |
| `...governance.e_governance.digital_india` | 0.25 | direct |
| `...economy.it_digital.data_localization` | 0.20 | contextual |

Sum = 1.0 ✓

---

## 10. Mapping validation rules

### 10.1 Hard reject

1. `link_weight` sum > 1.0.
2. Concept not `current_affairs_linkable`.
3. Deprecated concept.
4. More than **6** concepts per CA item.
5. `direct` link to concept with both prelims and mains relevance = 0.

### 10.2 Soft warnings

1. Single `background`-only mapping (no direct).
2. Cross-subject split with no primary direct on highest-weight concept.
3. Low confidence cluster (all < 0.70) — force review.

### 10.3 Nightly QA `ValidateCALinkQuality`

Flags published items where primary concept stage relevance mismatches `exam_stages` on CA row.

---

## 11. `CURRENT_AFFAIRS_OF` relationship sync

> **Note:** Edge type enum is `CURRENT_AFFAIRS_OF` (EXAM_DOMAIN §10.2). Section title uses canonical name.

### 11.1 Sync algorithm

```
SyncCAEdges(ca_id):
1.  DELETE concept_relationships
      WHERE source_id=ca_id AND source_type=current_affair
        AND relationship_type=CURRENT_AFFAIRS_OF
2.  FOR each verified mapping (ca, C, link_weight):
      INSERT concept_relationships
        source_id=ca_id, source_type=current_affair,
        target_id=C, target_type=concept,
        relationship_type=CURRENT_AFFAIRS_OF,
        weight=link_weight,
        metadata_json={ link_type, confidence },
        status=active
```

Runs on publish and mapping update.

### 11.2 Revision Engine consumption

Revision `CARelevanceScore` (`REVISION_ENGINE_SPECIFICATION.md` §9.1) reads:

- `concept_relationships` (`CURRENT_AFFAIRS_OF`)
- `current_affairs_mappings` (confidence)
- `current_affairs` (`status=published`, `published_at`)

CA Engine **does not** compute priority — supplies authoritative data.

---

## 12. Student engagement model

### 12.1 Engagement types

| Action | API | Effect |
|---|---|---|
| **Open** | `POST .../engage` | Upsert `student_ca_engagement.engaged_at` |
| **Complete** | `POST .../complete` | Set `completed_at`; emit `CurrentAffairsEngaged` |
| **Dwell heartbeat** | `PATCH .../dwell` | Update `dwell_seconds` |

### 12.2 Completion criteria

```
MarkComplete(student, ca_id):
  VALIDATE engaged_at exists
  VALIDATE dwell_seconds >= CA_MIN_DWELL_SECONDS (default 45) OR explicit student confirm
  completed_at = now
  EMIT CurrentAffairsEngaged
  Invoke StudySessionBridge (§13)
```

Anti-gaming: completion without minimum dwell requires explicit "I've read this" confirm flag (logged).

### 12.3 Engagement aggregates

Per student rolling windows:

| Metric | Window |
|---|---|
| `items_completed_7d` | 7 days |
| `items_completed_30d` | 30 days |
| `linked_concepts_engaged_30d` | distinct concepts via completed CA |
| `last_ca_activity_at` | max(completed_at) |

Stored in `student_ca_engagement_stats` read model (§25).

---

## 13. Study session bridge

### 13.1 Purpose

CA reading updates **Mastery (study channel 10%)** and **Retention** via `StudySessionLogged` — owned by Study module / Learning Graph path.

### 13.2 Bridge algorithm

```
StudySessionBridge(student, ca_id, dwell_seconds):
  mappings = verified mappings for ca_id ORDER BY link_weight DESC
  primary = mappings[0]
  engaged_minutes = max(1, round(dwell_seconds / 60))
  FOR each mapping M in mappings WHERE M.link_weight >= 0.15:
    CALL StudySessionService.log(
      student_id,
      concept_id=M.concept_id,
      engaged_minutes=engaged_minutes * M.link_weight,
      activity_type='ca_reading',
      source_ref={ type: 'ca', ca_id }
    )
  // StudySessionService emits StudySessionLogged → Learning Graph
```

CA Engine **calls port** — does not write graph rows.

### 13.3 V1 simplification

Single `StudySessionLogged` on **primary concept only** with full `engaged_minutes` if multi-concept split disabled (`CA_MULTI_CONCEPT_SESSION=false` default V1).

---

## 14. CASub computation (Readiness inputs)

### 14.1 Scoring reference

Scoring v1.1 §4.3:

```
CASub = 100 · ca_coverage_accuracy
```

When absent, Readiness redistributes weights (`SCORING_ENGINE_SPECIFICATION_V1_1.md`).

### 14.2 `ca_coverage_accuracy` formula (canonical)

```
coverage_90d = |{ C : C high-importance CA-linked AND student engaged C via CA in 90d }|
               / |{ C : C high-importance CA-linked }|

accuracy_90d = CA-tagged MCQ weighted correct / total    // from Assessment ca_quiz (V2)
               OR null if no ca_quiz attempts

IF accuracy_90d IS NULL:
  ca_coverage_accuracy = coverage_90d
ELSE:
  ca_coverage_accuracy = CA_COVERAGE_WEIGHT * coverage_90d
                       + CA_ACCURACY_WEIGHT * accuracy_90d
  // defaults: 0.60 coverage, 0.40 accuracy
```

**High-importance CA-linked concept:** `importance_score ≥ 70` on graph node AND ≥1 `CURRENT_AFFAIRS_OF` edge to CA published in last 90d.

### 14.3 V1 behavior

- Compute `coverage_90d` only.
- `CASub` **not exposed** in Readiness until `CA_SUB_MIN_ENGAGEMENTS` met (default **5** completed CA items) — Twin stores `subscores.ca: null`.

### 14.4 Port `CurrentAffairsReadPort.coverage_aggregate(student, window)`

Returns `{ coverage_90d, accuracy_90d, ca_sub_inputs }` for Twin builder.

---

## 15. CA relevance data contract (Revision)

### 15.1 Algorithm ownership

`CARelevanceScore` is implemented in **Revision Engine** (`REVISION_ENGINE_SPECIFICATION.md` §9.1). CA Engine guarantees data freshness and fields:

| Field | Source table |
|---|---|
| `published_at` | `current_affairs` |
| `status` | `current_affairs` |
| `mapping_confidence` | `current_affairs_mappings.confidence` |
| `exam_stage` | `current_affairs.exam_stages` |
| `relationship_weight` | `concept_relationships.weight` |

### 15.2 Relevance refresh trigger

On `CurrentAffairsPublished`:

```
RevisionEngine.enqueue CARelevanceRefresh(linked_concept_ids)
```

Debounced 30s per concept.

### 15.3 Config constants (owned by Revision; documented here)

| Key | Default |
|---|---|
| `CA_RELEVANCE_WINDOW_DAYS` | 30 |
| `CA_RECENCY_HALFLIFE_DAYS` | 7 |
| `CA_RELEVANCE_NORM` | 1.0 |
| `PRIORITY_W_CA` | 0.10 |

---

## 16. Event-driven architecture

### 16.1 Events emitted

| Event | When | Consumers |
|---|---|---|
| **`CurrentAffairsPublished`** | CA published or mapping updated on published item | Revision, Mentor cache, Assessment |
| **`CurrentAffairsEngaged`** | Student completes CA item | Twin, Analytics |
| **`CurrentAffairsArchived`** | Item archived | Revision (relevance decay), feeds |
| **`CAMappingReviewRequired`** | Low-confidence link queued | Faculty notifications |
| **`CAIngestionCompleted`** | Batch done | Admin |

### 16.2 Events consumed

| Event | Action |
|---|---|
| `DomainCatalogUpdated` | Revalidate mappings; deprecate links to deprecated concepts |
| `StudentRegistered` | Init empty engagement stats |

### 16.3 Outbox

Durable outbox before bus publish — same pattern as Assessment/PYQ specs.

---

## 17. `CurrentAffairsPublished` event contract

### 17.1 Payload schema (version 1)

```json
{
  "event_id": "uuid",
  "event_version": 1,
  "event_type": "CurrentAffairsPublished",
  "tenant_id": "uuid",
  "exam_id": "upsc_cse",
  "ca_id": "uuid",
  "occurred_at": "2026-06-18T06:00:00Z",
  "correlation_id": "uuid",
  "catalog_version": 12,
  "trigger": "initial_publish|mapping_update|importance_refresh",
  "item_summary": {
    "title": "RBI holds repo rate at 6.5%",
    "published_date": "2026-06-17",
    "importance_score": 88.5,
    "category": "economy",
    "exam_stages": ["prelims", "mains"]
  },
  "linked_concepts": [
    {
      "concept_id": "upsc.cse.economy.monetary_policy.repo_rate",
      "link_weight": 0.55,
      "link_type": "direct",
      "confidence": 0.92
    }
  ]
}
```

### 17.2 Idempotency

Consumers dedupe on `event_id`. At-most-once publish with outbox retry.

---

## 18. `CurrentAffairsEngaged` event contract

```json
{
  "event_id": "uuid",
  "event_type": "CurrentAffairsEngaged",
  "tenant_id": "uuid",
  "student_id": "uuid",
  "ca_id": "uuid",
  "occurred_at": "2026-06-18T07:30:00Z",
  "dwell_seconds": 180,
  "linked_concepts": ["upsc.cse.economy.monetary_policy.repo_rate"],
  "mentor_plan_item_id": "uuid-optional",
  "study_sessions_emitted": ["uuid"]
}
```

Twin handler: `RebuildCA` on `academic.current_affairs` subsection (`PREPARATION_TWIN_SPECIFICATION.md` §11).

---

## 19. Integration with Learning Graph

### 19.1 Write path

CA Engine **never** writes graph scores. Path:

```
CurrentAffairsEngaged → StudySessionBridge → StudySessionLogged → Learning Graph ApplyMasteryUpdate + ApplyRetentionStateUpdate
```

### 19.2 Read path

| Use | Port |
|---|---|
| Node state for linked concepts | `LearningGraphReadPort.get_node` |
| High-importance set for coverage denom | `list_nodes WHERE importance >= 70` |

### 19.3 CASub

Graph supplies `importance_score` for coverage denominator; CA supplies engagement evidence.

---

## 20. Integration with Mentor Agent

### 20.1 `GetCurrentAffairsPrioritiesTool` (authoritative backing)

Mentor §10 consumes this tool — **not** live SQL in Mentor service.

### 20.2 Response schema

```json
{
  "schema_version": "ca_tool_v1",
  "data": {
    "items": [
      {
        "ca_id": "uuid",
        "title": "RBI holds repo rate at 6.5%",
        "summary": "...",
        "published_date": "2026-06-17",
        "importance_score": 88.5,
        "ca_relevance": 91.2,
        "category": "economy",
        "linked_concepts": [
          {
            "concept_id": "upsc.cse.economy.monetary_policy.repo_rate",
            "link_type": "direct",
            "link_weight": 0.55,
            "concept_label": "Repo Rate"
          }
        ],
        "student_completed": false
      }
    ],
    "clusters": [
      {
        "topic_id": "upsc.cse.economy.monetary_policy",
        "item_count_7d": 4,
        "avg_importance": 86.0
      }
    ],
    "coverage_90d": 0.48,
    "as_of": "2026-06-18T02:00:00Z"
  }
}
```

### 20.3 Priority ranking algorithm `BuildCAPrioritiesFeed`

```
INPUT: student_id, exam_id, now
1.  items = published CA WHERE published_at >= now - 30d
2.  FOR each item:
       ca_relevance = CARelevanceScore(primary_linked_concept, student)  // call Revision port OR replicate pure fn
       sort_key = 0.6*item.importance_score + 0.4*ca_relevance
3.  Exclude items student completed in last 3 days (rotation, Mentor §10.2)
4.  Boost items linked to weak concepts (mastery < 55, importance >= 70)
5.  RETURN top N sorted by sort_key DESC
```

### 20.4 Daily slot sizing (Mentor §10.2)

Mentor reads `coverage_90d` from tool response:

```
daily_ca_slots = 2 IF days_to_exam < 90 OR coverage_90d < 0.5 ELSE 1
```

### 20.5 Task types emitted in plans

| Task | Content |
|---|---|
| `ca_reading` | Item from priorities feed |
| `ca_linked_study` | Study block on top linked concept after reading |

---

## 21. Integration with Revision Engine

### 21.1 Consumption summary

| Direction | Contract |
|---|---|
| CA → Revision | `CurrentAffairsPublished` triggers relevance refresh |
| Revision → CA | Reads mappings + edges only (read port) |

### 21.2 Priority impact

CA component contributes **0–10 points** on 0–100 priority scale (`PRIORITY_W_CA=0.10` × `ca_relevance`).

Does **not** override mandatory high-yield set (Revision §9.3).

### 21.3 Stability lock break

When `CARelevanceScore` jumps ≥ `CA_LOCK_BREAK_DELTA` (15) since lock, Revision recomputes priority (Revision §9.4).

---

## 22. Integration with Preparation Twin

### 22.1 Twin fields (`academic.current_affairs`)

Per `PREPARATION_TWIN_SPECIFICATION.md` §4.1:

```json
"current_affairs": {
  "coverage_90d": 0.55,
  "accuracy_90d": 0.62,
  "linked_concepts_engaged_30d": 18,
  "last_ca_activity_at": "2026-06-17T07:00:00Z"
}
```

### 22.2 Rebuild triggers

| Event | Action |
|---|---|
| `CurrentAffairsEngaged` | `RebuildCA` + maybe `RebuildPrediction` if CASub active |
| `CurrentAffairsPublished` | No immediate full rebuild (Revision handles urgency) |
| Nightly | Refresh `coverage_90d` for all active students |

### 22.3 CASub in prediction profile

When V2 active and threshold met, Twin stores `readiness.subscores.ca`; else `null`.

---

## 23. Integration with Assessment Engine

### 23.1 `ca_quiz` assessment type (V2)

Assessment Engine (`ASSESSMENT_ENGINE_SPECIFICATION.md` §3.1):

- Select MCQ questions tagged to concepts linked to recent CA items.
- `AssessmentCompleted` with `channel=ca` feeds `accuracy_90d`.

### 23.2 Question tagging

Platform questions MAY include `ca_id` reference in metadata for drill assembly.

### 23.3 Cache invalidation

`CurrentAffairsPublished` → Assessment invalidates CA-tagged question pools (if configured).

---

## 24. Integration with Knowledge / CA Agent

### 24.1 Boundary

| Component | Responsibility |
|---|---|
| **Current Affairs Engine** | Catalog, mappings, feeds, engagement, events |
| **Current Affairs Agent** (Part 5) | Explain headline, link to syllabus, answer "why it matters" |
| **Knowledge Agent** | RAG over books + optional CA chunks |

### 24.2 Supervisor routing (Mentor §10.4)

| Intent | Route |
|---|---|
| "Explain today's RBI news" | Current Affairs Agent (reads `ca_id` context) |
| "What should I read today?" | Mentor plan (`ca_reading` tasks) |
| "Deep dive on GST law" | Knowledge Agent |

### 24.3 Agent tools (V2)

CA Agent read tools:

- `GetCADetailTool(ca_id)`
- `GetCALinkedConceptsTool(ca_id)`
- `SearchCATool(query, window_days)`

Agent **must not** create mappings without human verify in V1.

### 24.4 RAG cross-reference (V2 optional)

Knowledge ingestion MAY set `metadata.ca_id` pointing to CA Engine row — separate license check per chunk.

---

## 25. Read models

### 25.1 `ca_daily_feed` (platform)

Denormalized published items last 30d sorted by `importance_score` — powers `GET /current-affairs`.

### 25.2 `student_ca_priorities` (Mentor tool)

PK `(tenant_id, student_id)` — serialized `GetCurrentAffairsPrioritiesTool` DTO.

Refresh: on `CurrentAffairsPublished`, `CurrentAffairsEngaged`, `LearningGraphUpdated` (mastery shift), nightly.

### 25.3 `student_ca_engagement_stats`

Rolling counters for Twin and Mentor slot sizing.

### 25.4 `concept_ca_stats`

| Column | Purpose |
|---|---|
| `concept_id` | |
| `active_ca_links_30d` | Count published CA in window |
| `last_ca_published_at` | Recency signal |

### 25.5 Rebuild `RebuildStudentCAPriorities`

```
INPUT: student_id
1.  feed = BuildCAPrioritiesFeed(student)
2.  clusters = group feed by topic_id (top 5)
3.  coverage = coverage_aggregate(student, 90d)
4.  UPSERT student_ca_priorities
```

---

## 26. Database schemas

### 26.1 Additional tables

**`ca_sources`** — provenance (§29)

**`ca_mapping_events`** — append-only audit

**`ca_outbox`** — event outbox

### 26.2 Indexing

| Index | Purpose |
|---|---|
| `(exam_id, status, published_at DESC)` on current_affairs | Feed |
| `(ca_id)` on current_affairs_mappings | Link lookup |
| `(concept_id)` on current_affairs_mappings | Revision CARelevance |
| `(tenant_id, student_id, completed_at DESC)` on engagement | Twin stats |

### 26.3 Partitioning

`student_ca_engagement` partition by month when > 10M rows.

---

## 27. API contracts

Aligned with `06-api-spec.md`; expanded for implementation.

### 27.1 Public student APIs

**`GET /current-affairs`**

Query: `?window_days=30&category=economy&limit=20&cursor=`

Response:

```json
{
  "items": [
    {
      "ca_id": "uuid",
      "title": "...",
      "summary": "...",
      "published_date": "2026-06-17",
      "importance_score": 88.5,
      "category": "economy",
      "linked_concepts": [{ "concept_id": "...", "link_type": "direct" }]
    }
  ],
  "next_cursor": null
}
```

**`GET /current-affairs/{ca_id}`** — detail view

**`POST /current-affairs/{ca_id}/engage`** — start reading

**`POST /current-affairs/{ca_id}/complete`** — mark done → `CurrentAffairsEngaged`

### 27.2 Admin / faculty APIs

| Method | Path | Purpose |
|---|---|---|
| POST | `/admin/ca/ingest` | Batch ingest |
| POST | `/admin/ca/items` | Create draft |
| PUT | `/admin/ca/items/{id}/mappings` | Replace links |
| POST | `/admin/ca/items/{id}/publish` | Publish |
| GET | `/faculty/ca/review-queue` | Mapping queue |
| POST | `/faculty/ca/items/{id}/verify` | Verify mappings |

### 27.3 Internal service ports

| Port | Method | Consumer |
|---|---|---|
| `CurrentAffairsReadPort` | `get_priorities(student)` | Mentor |
| `CurrentAffairsReadPort` | `coverage_aggregate(student, window)` | Twin |
| `CurrentAffairsReadPort` | `list_mappings(concept_id)` | Revision |
| `CurrentAffairsReadPort` | `get_item(ca_id)` | CA Agent |

---

## 28. Batch jobs and archival

| Job | Schedule | Action |
|---|---|---|
| `CAIngestionPoll` | Hourly (V2) | Fetch RSS sources |
| `CAImportanceDecayRefresh` | Daily 01:00 UTC | Recompute item importance recency |
| `CAAutoArchive` | Daily 02:00 UTC | Archive items > 180d |
| `CAMappingQualityScan` | Daily 03:00 UTC | QA flags |
| `CAEngagementRollup` | Nightly | Engagement stats + priorities rebuild |
| `CACoverageRollup` | Nightly | Twin CASub inputs |

---

## 29. Content licensing and provenance

### 29.1 Master Plan (G8 / D12)

Every CA item MUST reference licensed `source_id` before publish.

### 29.2 License types

| Type | Use |
|---|---|
| `public_domain_gov` | PIB, official gazette excerpts |
| `licensed_press` | Contracted newspaper feed |
| `summary_only` | Headline + summary; no full body reproduction |
| `institute_owned` | Faculty original summary |

### 29.3 Ingestion gate

```
IF source.license_expires_at < today: block publish; archive affected items
```

### 29.4 Attribution

Student UI shows source name + link per license requirements.

### 29.5 Summary-only mode

When full body not licensed, store `summary` (platform-written or licensed abstract) only — sufficient for Mentor `ca_reading` tasks.

---

## 30. Caching strategy

### 30.1 Redis keys

| Key | TTL | Content |
|---|---|---|
| `ca:feed:{exam_id}:{window}` | 300s | Public feed page |
| `ca:priorities:{tenant}:{student}` | 120s | Mentor tool DTO |
| `ca:item:{ca_id}` | 3600s | Item detail |
| `ca:mappings:{ca_id}` | 3600s | Mapping list |

### 30.2 Invalidation

```
CurrentAffairsPublished → DEL ca:feed:*, ca:priorities:*, ca:item:{id}
CurrentAffairsEngaged → DEL ca:priorities:{tenant}:{student}
DomainCatalogUpdated → DEL ca:mappings:* (validation refresh)
```

### 30.3 Stampede protection

Single-flight lock on `ca:priorities:lock:{student}` during rebuild.

---

## 31. Failure recovery

### 31.1 Ingestion partial failure

Batch `status=partial`; failed rows in `stats_json.errors`; no publish of incomplete drafts.

### 31.2 Outbox stuck events

Sweeper republishes pending > 5 min.

### 31.3 Mapping corruption

Replay from `ca_mapping_events` audit log.

### 31.4 Study session bridge failure

If `StudySessionLogged` fails after `CurrentAffairsEngaged`:

- Engagement still recorded (Twin CA counters).
- Retry job `CAStudyBridgeRetry` with idempotency on `ca_id+student_id`.

### 31.5 Catalog rollback

Admin restore snapshot → re-emit `CurrentAffairsPublished` bulk refresh.

---

## 32. Performance requirements

### 32.1 Targets (10k students, ~50 new CA items/week)

| Operation | Target |
|---|---|
| `GET /current-affairs` | p95 **< 80ms** |
| `GetCurrentAffairsPriorities` cached | p95 **< 50ms** |
| `POST .../complete` + event | p95 **< 300ms** |
| `CurrentAffairsPublished` → Revision refresh enqueue | p95 **< 200ms** |
| Nightly engagement rollup (10k students) | **≤ 20 min** |

### 32.2 Storage estimates

| Entity | V2 steady-state |
|---|---|
| `current_affairs` | ~5k active + 20k archived/year |
| `current_affairs_mappings` | ~15k |
| `student_ca_engagement` | ~30/student/month |

---

## 33. Observability

### 33.1 Metrics

| Metric | Type |
|---|---|
| `ca_ingest_items_total` | counter by source |
| `ca_publish_total` | counter |
| `ca_mapping_queue_depth` | gauge |
| `ca_engagement_complete_total` | counter |
| `ca_study_bridge_failures` | counter |
| `ca_feed_latency_ms` | histogram |

### 33.2 Alerts

- Mapping queue > 200 open > 48h → warn
- Ingestion failure rate > 10% → page
- Study bridge failure rate > 1% → warn

### 33.3 Structured logs

`request_id`, `tenant_id`, `student_id`, `ca_id`, `event_type`.

---

## 34. Future AI-assisted linking and RAG

### 34.1 V2 Linking Assistant

- Embedding similarity: CA summary ↔ concept catalog descriptions
- Output: ranked concepts + confidence
- Auto-apply at ≥ 0.85; else review queue
- Eval harness: ≥ 88% primary concept match vs faculty gold set before production

### 34.2 Cluster detection

Weekly job groups CA items by embedding cluster → `clusters` in priorities tool → Mentor monthly theme (`MENTOR_AGENT_SPECIFICATION.md` §12 monthly).

### 34.3 RAG pipeline (Knowledge Agent)

Optional export: `{ ca_id, title, summary, concept_ids[] }` to `knowledge_chunks` with separate ingestion job — **not** inline in CA publish path.

---

## Appendix A — V1 seed bootstrap

Minimum demo corpus:

- **40 CA items** covering last 90 days
- **≥2 items per category** (§4.4)
- **100% mapped** with faculty-verified links
- Publish batch → `CurrentAffairsPublished` → Mentor shows CA slots

Script: `scripts/seed_ca_upsc_cse_v1.py` → `seeds/ca_upsc_cse_v1.json`

---

## Appendix B — Configuration keys

| Key | Default | Purpose |
|---|---|---|
| `CA_AUTO_PUBLISH_CONFIDENCE` | 0.85 | §9 |
| `CA_ARCHIVE_DAYS` | 180 | §7.3 |
| `CA_ITEM_RECENCY_LAMBDA` | 0.08 | §8.4 |
| `CA_MIN_DWELL_SECONDS` | 45 | §12.2 |
| `CA_MULTI_CONCEPT_SESSION` | false | §13.3 V1 |
| `CA_COVERAGE_WEIGHT` | 0.60 | §14.2 |
| `CA_ACCURACY_WEIGHT` | 0.40 | §14.2 |
| `CA_SUB_MIN_ENGAGEMENTS` | 5 | §14.3 |
| `CA_PRIORITIES_CACHE_TTL_SECONDS` | 120 | §30 |
| `CA_FEED_DEFAULT_WINDOW_DAYS` | 30 | §27.1 |
| `CA_ROTATION_DAYS` | 3 | Mentor rotation §20.3 |
| `CA_RELEVANCE_WINDOW_DAYS` | 30 | Revision §15.3 |
| `CA_RECENCY_HALFLIFE_DAYS` | 7 | Revision §15.3 |

---

## Appendix C — Handoff to downstream specs

| Consumer | Uses from this spec |
|---|---|
| `MENTOR_AGENT_SPECIFICATION.md` | §20 GetCurrentAffairsPrioritiesTool, ca_reading tasks |
| `REVISION_ENGINE_SPECIFICATION.md` | §15 data contract, CARelevanceScore inputs |
| `PREPARATION_TWIN_SPECIFICATION.md` | §22 CASub, CurrentAffairsEngaged |
| `LEARNING_GRAPH_SPECIFICATION.md` | §19 StudySessionLogged bridge |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | §23 ca_quiz |
| `EXAM_DOMAIN_SPECIFICATION.md` | §8 mapping model, CURRENT_AFFAIRS_OF |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | §14 CASub inputs |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | Parallel ingestion/mapping pattern |
| API layer | §27 contracts |

---

## Appendix D — Consistency checklist

| Source doc | Alignment |
|---|---|
| `EXAM_DOMAIN_SPECIFICATION.md` | §8 entity/mappings; P5 linkability; confidence ≥0.85 |
| `REVISION_ENGINE_SPECIFICATION.md` | CARelevanceScore §9; CurrentAffairsPublished consumer §12.2 |
| `MENTOR_AGENT_SPECIFICATION.md` | §20 tool shape; daily slots §10.2; CA Agent boundary §24 |
| `PREPARATION_TWIN_SPECIFICATION.md` | CurrentAffairsEngaged; coverage_90d; CASub null V1 |
| `LEARNING_GRAPH_SPECIFICATION.md` | No direct graph writes; StudySessionLogged path |
| `ASSESSMENT_ENGINE_SPECIFICATION.md` | ca_quiz V2; channel=ca |
| `SCORING_ENGINE_SPECIFICATION_V1_1.md` | CASub formula §14; absent redistribution |
| `PYQ_INTELLIGENCE_SPECIFICATION.md` | Parallel ingestion/quarantine/outbox patterns |
| `MASTER_IMPLEMENTATION_PLAN.md` | S17 V2 scope; G8/D12 licensing |
| Blueprint Rule 5 | CA never writes mastery/retention — §2, §19 |
| Blueprint Rule 3 | CA Agent separate from catalog engine — §24 |
| Blueprint Rule 4 | mapping_rationale + item importance explainable — §8 |

---

*End of Current Affairs Engine Specification v1.0*
