# PrepOS AI — Exam Domain Specification

Version: 1.0
Status: Implementation-Ready · Canonical source of truth for UPSC knowledge hierarchy
Supersedes: informal syllabus references in `02-domain-model.md` (Part 2 §7–§9) for hierarchy, IDs, and relationships
Consistent with: `MASTER_IMPLEMENTATION_PLAN.md`, `SCORING_ENGINE_SPECIFICATION_V1_1.md`
Authoring lens: UPSC Domain Expert · Learning Scientist · Knowledge Graph Architect · Principal Software Architect · EdTech Product Architect

> **Scope.** This document defines the **deterministic UPSC knowledge domain**: exam stages, subject/topic/concept taxonomy, identifiers, metadata, relationships, and the exact fields consumed by the Learning Graph, Scoring Engine, Revision Engine, Preparation Twin, Mentor Agent, PYQ Mapping Engine, Current Affairs Linking Engine, and Question Generation Engine.
>
> **Non-goals:** business positioning, UI copy, SQL DDL, or LLM prompt design. Those layers consume this spec; they do not redefine it.
>
> **Learning Graph contract:** every row in `concepts` is a **future Learning Graph node**. There is exactly one Learning Graph node per concept per student (`student_concept_progress.concept_id`). Subjects and topics are **organizational nodes only** — they aggregate concept scores; they do not receive Mastery/Retention directly unless explicitly defined as pseudo-concepts (they are not, in V1).

---

## 0. Document map

| § | Title | Primary consumer |
|---|---|---|
| 1 | Purpose | All teams |
| 2 | Design principles | Architects |
| 3 | UPSC exam hierarchy | Scoring, Mentor, Assessment |
| 4 | Subject taxonomy | Ingestion, UI navigation |
| 5 | Topic taxonomy | Ingestion, PYQ/CA mapping |
| 6 | Concept taxonomy & rules | Learning Graph, all engines |
| 7 | Concept metadata model | Database, APIs |
| 8 | Current Affairs mapping | CA Linking Engine |
| 9 | PYQ mapping | PYQ Intelligence Engine |
| 10 | Learning Graph requirements | LEARNING_GRAPH_SPECIFICATION (next doc) |
| 11 | Scoring Engine dependencies | Scoring Engine |
| 12 | Revision Engine dependencies | Revision Engine |
| 13 | Preparation Twin dependencies | Twin builder |
| 14 | Database representation | Backend |
| 15 | Future extensibility | Multi-exam roadmap |

---

## 1. Purpose

### 1.1 Why this domain model exists

UPSC preparation is not a linear course catalog. It is a **high-dimensional, overlapping knowledge graph** where:
- the same concept appears in Prelims MCQs, Mains answers, Essays, and Current Affairs;
- PYQ frequency drives prioritization;
- forgetting and revision are time-dependent;
- readiness is a function of **concept-level** evidence aggregated upward.

PrepOS engines cannot operate on PDFs or free-text syllabus bullets. They require a **canonical, versioned, machine-readable hierarchy** where every assessable unit of knowledge is a **Concept** with stable identifiers, exam-stage relevance, relationship edges, and PYQ/CA linkability.

### 1.2 Systems that consume this specification

| System | What it reads from this spec |
|---|---|
| **Learning Graph Engine** | `concept_id`, relationships (`PREREQUISITE`, etc.), `exam_stages`, `is_active` |
| **Scoring Engine** | `concept_id`, `importance` inputs (`exam_relevance`, PYQ hooks), `exam_stages`, subject/topic rollups |
| **Revision Engine** | `concept_id`, `importance`, retention inputs, `exam_stages`, `D_exam` (from student, not domain) |
| **Mentor Agent** | full hierarchy for plan assembly, `concept_name`, Exam Weight badge source, overconfidence flags (via scores) |
| **Preparation Twin** | subject/topic/concept aggregations, `exam_stages`, coverage denominators |
| **Question Generation Engine** | `concept_id`, `concept_type`, `difficulty`, `exam_stages`, `child_concepts` for distractor generation |
| **PYQ Mapping Engine** | `concept_id`, mapping weights, `pyq_mappable`, multi-concept rules |
| **Current Affairs Linking Engine** | `current_affairs_linkable`, `concept_id`, CA relationship rules |

### 1.3 Canonical hierarchy (V1)

```
Exam (upsc_cse)
 └── Subject  (e.g., polity)
      └── Topic  (e.g., fundamental_rights)
           └── Concept  (e.g., article_14)   ← Learning Graph leaf node
                └── [optional] Sub-concept children (same table, parent_concept_id)
```

**Four levels, fixed.** The legacy blueprint term `Subtopic` (Part 2 §7) maps to **Topic** in this spec. Do not introduce a fifth organizational level in V1.

### 1.4 Versioning

- Domain catalog version: `domain_catalog_version` (semver, e.g., `1.0.0`).
- Every `concept_id`, `topic_id`, `subject_id` is **immutable once published**. Renames change `concept_name` display fields only; IDs never change.
- Additions (new concepts) increment minor version; breaking relationship changes increment major version and require Learning Graph backfill plan.

---

## 2. Design Principles

| # | Principle | Implementation rule |
|---|---|---|
| P1 | **Concept-first architecture** | All scoring, revision, assessment, PYQ, and CA links attach to `concept_id`. Subjects/topics are rollups only. |
| P2 | **Graph-friendly structure** | Concepts connect via typed edges in `concept_relationships`. No implicit hierarchy beyond parent pointer. |
| P3 | **Exam-agnostic extensibility** | IDs namespaced by `exam_code`. UPSC is `upsc_cse`; APPSC reuses the same table shapes with different `exam_code`. |
| P4 | **Deterministic hierarchy** | Every concept has exactly one `subject_id` and one `topic_id`. No concept belongs to two topics (use `RELATED_TO` edges instead). |
| P5 | **Current Affairs linkability** | `current_affairs_linkable=true` concepts declare CA eligibility; CA items link via `current_affairs_mappings`, never by duplicating concepts. |
| P6 | **PYQ traceability** | Every Prelims/Mains question maps to ≥1 concept via `pyq_mappings` with explicit weight. Unmapped questions are quarantined, not guessed. |
| P7 | **Stage-aware relevance** | Each concept declares `prelims_relevance` and `mains_relevance` (0–100). Used by Importance `exam_relevance` and assessment routing. |
| P8 | **Stable identifiers** | Human-readable slugs (`upsc.cse.polity.fr.article_14`), not sequential integers, for debuggability and cross-environment parity. |
| P9 | **Incremental catalog seeding** | Topics are complete in V1; concepts within a topic may be `status=draft` until content team validates. Engines ignore `draft` concepts. |
| P10 | **No duplicate knowledge nodes** | One canonical concept per assessable idea. Overlaps expressed as graph edges, not duplicate rows. |

---

## 3. UPSC Exam Hierarchy

### 3.1 Exam entity

| Field | Value (V1 canonical) |
|---|---|
| `exam_id` | `upsc_cse` |
| `exam_code` | `upsc_cse` |
| `exam_name` | Union Public Service Commission — Civil Services Examination |
| `exam_type` | `competitive_civil_services` |
| `domain_catalog_version` | `1.0.0` |
| `prelims_weight` | 0.25 (selection gate; not final rank) |
| `mains_weight` | 0.55 |
| `interview_weight` | 0.20 |
| `essay_included` | true (Mains Paper I — Essay) |

### 3.2 Exam stages

| Stage | Code | Papers / components | In V1 scope | Participates in scoring |
|---|---|---|---|---|
| **Prelims** | `prelims` | GS Paper I (200 MCQ), CSAT Paper II (qualifying) | GS Paper I fully; CSAT tracking only | **Mastery** (MCQ), **Retention**, **Importance**, **Readiness** (`MCQSub`), **Predicted Prelims** |
| **Mains** | `mains` | GS I–IV, Essay, Optional (optional out of V1 catalog) | GS I–IV + Essay | **Mastery** (Mains/Rev/Study), **Retention**, **Importance**, **Readiness** (`WritingSub`, `MasteryNonMCQ`), **Predicted Mains** |
| **Essay** | `essay` | Mains Paper I — Essay (250 marks) | Yes (as subject + topics) | **Readiness** (`WritingSub`), Essay assessments; no separate Prelims path |
| **Interview** | `interview` | Personality Test (275 marks) | Catalog stub only (V2+) | **Not in V1 scoring**; `interview_relevance` reserved |

### 3.3 Stage participation matrix

| Engine / Score | Prelims | Mains | Essay | Interview |
|---|---|---|---|---|
| Mastery (MCQ channel) | Yes | No | No | No |
| Mastery (Mains channel) | No | Yes | Yes | No |
| Mastery (Revision/Study) | Yes | Yes | Yes | No |
| Retention | Yes | Yes | Yes | No |
| Importance (Exam Weight) | Yes | Yes | Yes | Stub |
| Readiness | Yes (via MCQSub) | Yes (via WritingSub, KnowledgeSub) | Yes | No |
| Predicted Prelims | Yes (gated) | No | No | No |
| Predicted Mains | No | Yes (gated) | Partial | No |
| Revision Priority | Yes | Yes | Yes | No |

### 3.4 Mains GS paper → subject mapping

Mains papers aggregate subjects for reporting; **scoring remains concept-level**.

| Mains paper | Code | Primary subjects (from §4) |
|---|---|---|
| GS Paper I | `mains_gs1` | History, Art & Culture, Geography, Society |
| GS Paper II | `mains_gs2` | Polity, Governance, Social Justice, International Relations |
| GS Paper III | `mains_gs3` | Economy, Agriculture, Environment, Science & Technology, Internal Security, Disaster Management |
| GS Paper IV | `mains_gs4` | Ethics |
| Essay | `mains_essay` | Essay |
| Prelims GS I | `prelims_gs1` | History, Geography, Polity, Economy, Environment, Science & Technology, Current Affairs |

### 3.5 CSAT (Prelims Paper II)

| Field | Rule |
|---|---|
| `exam_stage` | `prelims` |
| `subject_id` | `upsc.cse.csat` |
| Scoring | Qualifying only; **excluded from Readiness and Predicted Prelims** in V1 |
| Learning Graph | Optional V2; not seeded in V1 catalog |

---

## 4. Subject Taxonomy

### 4.1 Subject identifier rules

```
subject_id = {exam_code}.{subject_slug}
Example: upsc.cse.polity
```

| Field | Required | Description |
|---|---|---|
| `subject_id` | yes | Immutable slug |
| `subject_name` | yes | Display name |
| `subject_slug` | yes | URL-safe short name |
| `exam_id` | yes | Always `upsc_cse` in V1 |
| `prelims_applicable` | yes | bool |
| `mains_applicable` | yes | bool |
| `sort_order` | yes | int, UI navigation |
| `status` | yes | `active` \| `draft` \| `deprecated` |

### 4.2 Complete subject registry (V1)

| subject_id | subject_name | Prelims | Mains | Primary paper(s) |
|---|---|:---:|:---:|---|
| `upsc.cse.history` | History | ✓ | ✓ | Prelims GS1, Mains GS1 |
| `upsc.cse.art_culture` | Art & Culture | ✓ | ✓ | Prelims GS1, Mains GS1 |
| `upsc.cse.geography` | Geography | ✓ | ✓ | Prelims GS1, Mains GS1 |
| `upsc.cse.polity` | Polity | ✓ | ✓ | Prelims GS1, Mains GS2 |
| `upsc.cse.economy` | Economy | ✓ | ✓ | Prelims GS1, Mains GS3 |
| `upsc.cse.environment` | Environment & Ecology | ✓ | ✓ | Prelims GS1, Mains GS3 |
| `upsc.cse.science_technology` | Science & Technology | ✓ | ✓ | Prelims GS1, Mains GS3 |
| `upsc.cse.international_relations` | International Relations | — | ✓ | Mains GS2 |
| `upsc.cse.governance` | Governance | — | ✓ | Mains GS2 |
| `upsc.cse.social_justice` | Social Justice | — | ✓ | Mains GS2 |
| `upsc.cse.society` | Society | — | ✓ | Mains GS1 |
| `upsc.cse.internal_security` | Internal Security | — | ✓ | Mains GS3 |
| `upsc.cse.disaster_management` | Disaster Management | — | ✓ | Mains GS3 |
| `upsc.cse.agriculture` | Agriculture | — | ✓ | Mains GS3 |
| `upsc.cse.ethics` | Ethics | — | ✓ | Mains GS4 |
| `upsc.cse.essay` | Essay | — | ✓ | Mains Essay |
| `upsc.cse.current_affairs` | Current Affairs | ✓ | ✓ | Cross-cutting (all papers) |

**Total: 17 subjects** (16 scored + CSAT excluded from §4.2, tracked separately in §3.5).

---

## 5. Topic Taxonomy

### 5.1 Topic identifier rules

```
topic_id = {subject_id}.{topic_slug}
Example: upsc.cse.polity.fundamental_rights
```

| Field | Required | Description |
|---|---|---|
| `topic_id` | yes | Immutable slug |
| `topic_name` | yes | Display name |
| `subject_id` | yes | FK to subjects |
| `prelims_relevance` | yes | 0–100 default structural weight for Importance |
| `mains_relevance` | yes | 0–100 |
| `sort_order` | yes | int |
| `status` | yes | `active` \| `draft` \| `deprecated` |

### 5.2 Complete topic registry by subject

#### `upsc.cse.history`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.history.ancient` | Ancient History | 70 | 75 |
| `upsc.cse.history.medieval` | Medieval History | 60 | 65 |
| `upsc.cse.history.modern` | Modern History | 95 | 95 |
| `upsc.cse.history.freedom_struggle` | Freedom Struggle | 90 | 95 |
| `upsc.cse.history.post_independence` | Post-Independence India | 50 | 80 |
| `upsc.cse.history.world_history` | World History | 40 | 70 |

#### `upsc.cse.art_culture`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.art_culture.architecture` | Architecture | 75 | 80 |
| `upsc.cse.art_culture.sculpture_painting` | Sculpture & Painting | 65 | 75 |
| `upsc.cse.art_culture.literature` | Literature & Philosophy | 55 | 70 |
| `upsc.cse.art_culture.performing_arts` | Performing Arts | 60 | 65 |
| `upsc.cse.art_culture.heritage_conservation` | Heritage & Conservation | 70 | 85 |

#### `upsc.cse.geography`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.geography.physical` | Physical Geography | 85 | 70 |
| `upsc.cse.geography.indian_geography` | Indian Geography | 90 | 85 |
| `upsc.cse.geography.world_geography` | World Geography | 70 | 60 |
| `upsc.cse.geography.human_economic` | Human & Economic Geography | 75 | 75 |
| `upsc.cse.geography.climatology` | Climatology | 80 | 65 |
| `upsc.cse.geography.geomorphology` | Geomorphology | 75 | 60 |
| `upsc.cse.geography.oceanography` | Oceanography | 65 | 55 |
| `upsc.cse.geography.resources` | Resources & Industries | 70 | 70 |

#### `upsc.cse.polity`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.polity.constitution_basics` | Constitution — Basics & Making | 85 | 80 |
| `upsc.cse.polity.fundamental_rights` | Fundamental Rights | 95 | 95 |
| `upsc.cse.polity.dpsp` | Directive Principles (DPSP) | 80 | 90 |
| `upsc.cse.polity.fundamental_duties` | Fundamental Duties | 60 | 70 |
| `upsc.cse.polity.union_executive` | Union Executive | 85 | 85 |
| `upsc.cse.polity.parliament` | Parliament | 90 | 90 |
| `upsc.cse.polity.judiciary` | Judiciary | 90 | 90 |
| `upsc.cse.polity.federalism` | Federalism | 85 | 90 |
| `upsc.cse.polity.local_government` | Local Government | 75 | 80 |
| `upsc.cse.polity.constitutional_bodies` | Constitutional Bodies | 80 | 75 |
| `upsc.cse.polity.non_constitutional_bodies` | Non-Constitutional Bodies | 75 | 70 |
| `upsc.cse.polity.amendments` | Constitutional Amendments | 80 | 75 |
| `upsc.cse.polity.emergency` | Emergency Provisions | 70 | 80 |
| `upsc.cse.polity.center_state_relations` | Centre–State Relations | 80 | 85 |

#### `upsc.cse.economy`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.economy.national_income` | National Income & Growth | 80 | 85 |
| `upsc.cse.economy.inflation` | Inflation | 85 | 85 |
| `upsc.cse.economy.fiscal_policy` | Fiscal Policy | 85 | 90 |
| `upsc.cse.economy.monetary_policy` | Monetary Policy | 90 | 90 |
| `upsc.cse.economy.banking` | Banking & Financial System | 90 | 85 |
| `upsc.cse.economy.budget` | Budget & Taxation | 85 | 90 |
| `upsc.cse.economy.external_sector` | External Sector | 80 | 85 |
| `upsc.cse.economy.planning` | Planning & Development | 70 | 75 |
| `upsc.cse.economy.agriculture_economics` | Agriculture Economics | 75 | 85 |
| `upsc.cse.economy.industry_services` | Industry & Services | 70 | 80 |
| `upsc.cse.economy.inclusive_growth` | Inclusive Growth & Employment | 65 | 85 |
| `upsc.cse.economy.international_economics` | International Economics | 60 | 70 |

#### `upsc.cse.environment`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.environment.ecology_basics` | Ecology Basics | 85 | 75 |
| `upsc.cse.environment.biodiversity` | Biodiversity | 90 | 85 |
| `upsc.cse.environment.climate_change` | Climate Change | 90 | 90 |
| `upsc.cse.environment.pollution` | Pollution & Waste | 85 | 80 |
| `upsc.cse.environment.conservation` | Conservation & Protected Areas | 85 | 85 |
| `upsc.cse.environment.environmental_laws` | Environmental Laws & Institutions | 80 | 85 |
| `upsc.cse.environment.sustainable_development` | Sustainable Development | 75 | 85 |

#### `upsc.cse.science_technology`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.science_technology.space` | Space Technology | 80 | 75 |
| `upsc.cse.science_technology.it_digital` | IT & Digital Technology | 85 | 80 |
| `upsc.cse.science_technology.biotechnology` | Biotechnology & Health | 80 | 75 |
| `upsc.cse.science_technology.energy` | Energy Science | 75 | 80 |
| `upsc.cse.science_technology.defence` | Defence Technology | 70 | 70 |
| `upsc.cse.science_technology.materials_nano` | Materials & Nanotechnology | 60 | 60 |
| `upsc.cse.science_technology.general_science` | General Science (Physics/Chem/Bio) | 90 | 50 |

#### `upsc.cse.international_relations`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.international_relations.india_foreign_policy` | India Foreign Policy | 40 | 90 |
| `upsc.cse.international_relations.bilateral` | Bilateral Relations | 35 | 85 |
| `upsc.cse.international_relations.regional` | Regional Groupings | 40 | 80 |
| `upsc.cse.international_relations.global_institutions` | Global Institutions | 50 | 85 |
| `upsc.cse.international_relations.conflicts` | Conflicts & Geopolitics | 45 | 80 |

#### `upsc.cse.governance`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.governance.civil_services` | Civil Services & Reforms | 30 | 85 |
| `upsc.cse.governance.e_governance` | E-Governance | 40 | 85 |
| `upsc.cse.governance.transparency_accountability` | Transparency & Accountability | 35 | 90 |
| `upsc.cse.governance.citizen_charters` | Citizen Charters & RTI | 50 | 85 |
| `upsc.cse.governance.public_policy` | Public Policy | 30 | 90 |

#### `upsc.cse.social_justice`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.social_justice.welfare_schemes` | Welfare Schemes | 60 | 90 |
| `upsc.cse.social_justice.vulnerable_sections` | Vulnerable Sections | 55 | 90 |
| `upsc.cse.social_justice.education_health` | Education & Health | 50 | 85 |
| `upsc.cse.social_justice.poverty_hunger` | Poverty & Hunger | 55 | 85 |

#### `upsc.cse.society`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.society.indian_society_structure` | Indian Society Structure | 30 | 85 |
| `upsc.cse.society.population_urbanization` | Population & Urbanization | 45 | 80 |
| `upsc.cse.society.women_children` | Women & Children | 40 | 85 |
| `upsc.cse.society.globalization_society` | Globalization & Society | 35 | 80 |
| `upsc.cse.society.social_movements` | Social Movements | 40 | 85 |

#### `upsc.cse.internal_security`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.internal_security.extremism` | Extremism & Left-Wing Extremism | 40 | 85 |
| `upsc.cse.internal_security.terrorism` | Terrorism & Radicalization | 45 | 90 |
| `upsc.cse.internal_security.cyber_security` | Cyber Security | 50 | 85 |
| `upsc.cse.internal_security.border_management` | Border Management | 40 | 80 |
| `upsc.cse.internal_security.organized_crime` | Organized Crime & Money Laundering | 35 | 75 |
| `upsc.cse.internal_security.security_forces` | Security Forces & Agencies | 50 | 80 |

#### `upsc.cse.disaster_management`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.disaster_management.framework` | Disaster Management Framework | 45 | 85 |
| `upsc.cse.disaster_management.types_mitigation` | Disaster Types & Mitigation | 50 | 85 |
| `upsc.cse.disaster_management.institutions` | Institutions (NDMA/NDRF) | 45 | 80 |

#### `upsc.cse.agriculture`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.agriculture.crops_cropping` | Crops & Cropping Systems | 55 | 80 |
| `upsc.cse.agriculture.irrigation` | Irrigation & Water Use | 50 | 75 |
| `upsc.cse.agriculture.subsidies_food` | Subsidies & Food Security | 55 | 85 |
| `upsc.cse.agriculture.agri_technology` | Agricultural Technology | 45 | 75 |
| `upsc.cse.agriculture.rural_development` | Rural Development | 40 | 80 |

#### `upsc.cse.ethics`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.ethics.theories` | Ethical Theories | 0 | 90 |
| `upsc.cse.ethics.integrity_aptitude` | Integrity & Aptitude | 0 | 95 |
| `upsc.cse.ethics.attitude` | Attitude | 0 | 85 |
| `upsc.cse.ethics.emotional_intelligence` | Emotional Intelligence | 0 | 80 |
| `upsc.cse.ethics.public_service_values` | Public Service Values | 0 | 95 |
| `upsc.cse.ethics.probity_governance` | Probity in Governance | 0 | 90 |
| `upsc.cse.ethics.case_studies` | Case Studies | 0 | 95 |

#### `upsc.cse.essay`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.essay.philosophical` | Philosophical Essays | 0 | 90 |
| `upsc.cse.essay.society_development` | Society & Development | 0 | 90 |
| `upsc.cse.essay.polity_governance` | Polity & Governance | 0 | 85 |
| `upsc.cse.essay.economy_environment` | Economy & Environment | 0 | 85 |
| `upsc.cse.essay.ethics_humanity` | Ethics & Humanity | 0 | 90 |

#### `upsc.cse.current_affairs`

| topic_id | topic_name | Prelims rel | Mains rel |
|---|---|:---:|:---:|
| `upsc.cse.current_affairs.national` | National Affairs | 90 | 85 |
| `upsc.cse.current_affairs.international` | International Affairs | 85 | 85 |
| `upsc.cse.current_affairs.economy` | Economic Affairs | 85 | 85 |
| `upsc.cse.current_affairs.science_env` | Science, Environment & Tech Affairs | 80 | 80 |
| `upsc.cse.current_affairs.polity_governance` | Polity & Governance Affairs | 85 | 90 |
| `upsc.cse.current_affairs.reports_indices` | Reports, Indices & Summits | 75 | 75 |

**Total: 98 topics across 17 subjects.**

---

## 6. Concept Taxonomy

### 6.1 Concept identifier rules

```
concept_id = {topic_id}.{concept_slug}
Example: upsc.cse.polity.fundamental_rights.article_14
```

**Every `concept_id` is a Learning Graph node candidate.** When `status=active`, the platform MUST be able to create `student_concept_progress` rows for it.

### 6.2 Concept required fields (minimum)

| Field | Type | Required | Description |
|---|---|:---:|---|
| `concept_id` | string | yes | Immutable slug (Learning Graph node key) |
| `topic_id` | string | yes | FK to topics |
| `subject_id` | string | yes | Denormalized from topic (validation constraint) |
| `concept_name` | string | yes | Display name |
| `concept_slug` | string | yes | Short slug |
| `concept_type` | enum | yes | See §6.3 |
| `prelims_relevance` | int 0–100 | yes | Stage weight for Importance / assessment routing |
| `mains_relevance` | int 0–100 | yes | Stage weight |
| `current_affairs_linkable` | bool | yes | CA engine may link to this concept |
| `pyq_mappable` | bool | yes | PYQ engine may map questions here |
| `parent_concept_id` | string | no | For hierarchical sub-concepts (same table) |
| `status` | enum | yes | `active` \| `draft` \| `deprecated` |

### 6.3 `concept_type` enum

| Value | Definition | Example |
|---|---|---|
| `definition` | Term, article, principle, index | Article 14, GDP, Monsoon |
| `process` | Mechanism, procedure, cycle | Law-making process, Carbon cycle |
| `institution` | Body, organization, treaty | RBI, UN, NDMA |
| `event` | Historical/geopolitical event | Revolt of 1857, Green Revolution |
| `policy_scheme` | Government policy/program | MGNREGA, PM-KISAN |
| `case_study` | Judgment, ethical scenario | Kesavananda Bharati case |
| `skill` | Essay/ethics skill node | Essay structure, moral reasoning |
| `meta_current_affairs` | CA bridge node (optional) | Used when CA topic needs anchor |

**Rule:** Question Generation Engine uses `concept_type` to select template (MCQ vs Mains vs case-study prompt).

### 6.4 Concept granularity rules

1. **One assessable idea per concept.** If an MCQ or Mains answer can be scored independently, it warrants its own `concept_id`.
2. **Parent/child allowed** via `parent_concept_id`. Parent concepts MAY aggregate child scores (Learning Graph rollup); children are the default assessment targets.
3. **Maximum depth:** 2 levels (topic → parent concept → child concept). No deeper nesting in V1.
4. **Minimum concepts per active topic:** ≥3 `active` concepts before topic appears in student plans.
5. **High-yield topics** (Prelims rel ≥85): target 8–15 concepts (e.g., Fundamental Rights, Parliament, Monetary Policy).
6. **Low-yield topics:** target 3–6 concepts minimum.
7. **Draft concepts** are invisible to Mentor, Revision, and Readiness coverage denominators.

### 6.5 Canonical example — Fundamental Rights (full concept tree)

**Topic:** `upsc.cse.polity.fundamental_rights`

| concept_id | concept_name | concept_type | Prelims | Mains | CA link | PYQ map | parent |
|---|---|---|:---:|:---:|:---:|:---:|---|
| `...fundamental_rights.overview` | Fundamental Rights — Overview | definition | 90 | 90 | ✓ | ✓ | — |
| `...fundamental_rights.article_14` | Article 14 — Equality Before Law | definition | 95 | 95 | ✓ | ✓ | overview |
| `...fundamental_rights.article_19` | Article 19 — Six Freedoms | definition | 95 | 95 | ✓ | ✓ | overview |
| `...fundamental_rights.article_21` | Article 21 — Life & Liberty | definition | 98 | 98 | ✓ | ✓ | overview |
| `...fundamental_rights.article_21a` | Article 21A — Right to Education | definition | 80 | 85 | ✓ | ✓ | article_21 |
| `...fundamental_rights.article_32` | Article 32 — Constitutional Remedies | definition | 90 | 90 | ✓ | ✓ | overview |
| `...fundamental_rights.reasonable_restrictions` | Reasonable Restrictions | process | 85 | 90 | ✓ | ✓ | overview |
| `...fundamental_rights.writ_jurisdiction` | Writ Jurisdiction (32 & 226) | process | 90 | 90 | ✓ | ✓ | article_32 |
| `...fundamental_rights.habeas_corpus` | Habeas Corpus | definition | 75 | 80 | ✓ | ✓ | writ_jurisdiction |
| `...fundamental_rights.mandal_kesavananda` | Landmark Cases (Kesavananda, Maneka, etc.) | case_study | 80 | 95 | ✓ | ✓ | overview |

**Required relationships (§10):**
- `article_14` **PREREQUISITE** → `overview`
- `article_19` **PREREQUISITE** → `overview`
- `writ_jurisdiction` **BUILDS_ON** → `article_32`
- `overview` **RELATED_TO** → `upsc.cse.polity.dpsp.overview` (cross-topic edge)
- `article_21` **CURRENT_AFFAIRS_OF** → (CA items about privacy/data protection link here)

### 6.6 Concept seed catalog (V1 targets)

V1 ships **≥450 active concepts** across 98 topics (avg ~4.6/topic; high-yield topics carry more). Below: **representative concept slugs** per topic (implementers expand to full rows using §6.2 schema).

#### Polity (sample — full Polity tree prioritized in seed sprint)

| topic_id | concept slugs (representative) |
|---|---|
| `...constitution_basics` | `making_of_constitution`, `sources_of_constitution`, `preamble`, `citizenship` |
| `...fundamental_rights` | *(see §6.5 full tree)* |
| `...dpsp` | `overview`, `socialistic_principles`, `gandhian_principles`, `implementation_dpsp` |
| `...fundamental_duties` | `overview`, `list_of_duties`, `enforceability` |
| `...parliament` | `structure`, `sessions`, `legislative_process`, `budget_process`, `committees`, `privileges` |
| `...judiciary` | `supreme_court`, `high_courts`, `judicial_review`, `collegium`, `tribunals` |
| `...federalism` | `federal_features`, `quasi_federal`, `interstate_council`, `interstate_disputes` |
| `...local_government` | `panchayati_raj`, `municipalities`, `73rd_74th_amendments` |
| `...constitutional_bodies` | `cag`, `ec`, `upsc`, `finance_commission`, `ncsc_ncst` |
| `...non_constitutional_bodies` | `nhrc`, `ncw`, `ncpcr`, `niti_aayog`, `rbi_as_non_constitutional` |
| `...amendments` | `amendment_process`, `basic_structure`, `landmark_amendments` |
| `...emergency` | `national_emergency`, `state_emergency`, `financial_emergency` |
| `...center_state_relations` | `legislative_relations`, `administrative_relations`, `financial_relations` |
| `...union_executive` | `president`, `vice_president`, `pm_council`, `cabinet` |

#### Economy (sample)

| topic_id | concept slugs |
|---|---|
| `...inflation` | `cpi_wpi`, `demand_pull_cost_push`, `core_inflation`, `phillips_curve` |
| `...monetary_policy` | `repo_reverse_repo`, `crr_slr`, `mpc`, `transmission_mechanism`, `quantitative_easing` |
| `...fiscal_policy` | `fiscal_deficit`, `primary_deficit`, `frbm`, `capital_revenue_expenditure` |
| `...banking` | `commercial_banks`, `npas`, `basel_norms`, `payment_systems`, `nbfc` |
| `...budget` | `budget_process`, `finance_bill`, `gst`, `direct_indirect_tax` |
| `...external_sector` | `balance_of_payments`, `forex_reserves`, `exchange_rate`, `fdi_fpi` |
| `...national_income` | `gdp_gnp`, `gva`, `growth_measurement`, `human_development_index` |
| `...agriculture_economics` | `crop_insurance`, `msp`, `agri_credit`, `land_reforms` |

#### History (sample)

| topic_id | concept slugs |
|---|---|
| `...modern` | `revolt_1857`, `socio_religious_reforms`, `early_nationalists`, `partition_bengal`, `swadeshi` |
| `...freedom_struggle` | `non_cooperation`, `civil_disobedience`, `quit_india`, `revolutionary_movement`, `subhash_chandra_bose` |
| `...ancient` | `indus_valley`, `vedic_period`, `mauryan_empire`, `gupta_period` |
| `...medieval` | `delhi_sultanate`, `mughal_administration`, `bhakti_sufi` |
| `...post_independence` | `integration_princely_states`, `planning_era`, `liberalization_1991` |

#### Environment, Geography, S&T, IR, Governance, Society, Security, Disaster, Agriculture, Ethics, Essay, CA

Each remaining topic follows the same pattern: 3–15 `active` concepts with slugs `{topic_id}.{descriptive_slug}`. Full machine-readable seed file: `seeds/upsc_cse_concepts_v1_0.json` (to be generated from this spec during Sprint S2; not part of this document body).

### 6.7 Concept count targets by subject (V1)

| subject_id | target active concepts |
|---|---:|
| history | 45 |
| art_culture | 30 |
| geography | 40 |
| polity | 65 |
| economy | 50 |
| environment | 35 |
| science_technology | 40 |
| international_relations | 25 |
| governance | 20 |
| social_justice | 20 |
| society | 20 |
| internal_security | 25 |
| disaster_management | 12 |
| agriculture | 20 |
| ethics | 25 |
| essay | 15 |
| current_affairs | 30 |
| **Total** | **≥497** |

---

## 7. Concept Metadata Model

### 7.1 Full metadata schema

Every concept row MUST support the following fields (stored in `concepts` table + JSONB extension `metadata` for rarely-used attrs).

```json
{
  "concept_id": "upsc.cse.polity.fundamental_rights.article_14",
  "concept_name": "Article 14 — Equality Before Law",
  "concept_slug": "article_14",
  "subject_id": "upsc.cse.polity",
  "topic_id": "upsc.cse.polity.fundamental_rights",
  "exam_id": "upsc_cse",
  "parent_concept_id": "upsc.cse.polity.fundamental_rights.overview",
  "concept_type": "definition",
  "exam_stages": ["prelims", "mains"],
  "prelims_relevance": 95,
  "mains_relevance": 95,
  "interview_relevance": 40,
  "difficulty": 3,
  "importance": null,
  "importance_version": null,
  "current_affairs_linkable": true,
  "pyq_mappable": true,
  "pyq_count": 0,
  "pyq_count_cached_at": null,
  "parent_concepts": [],
  "child_concepts": [],
  "prerequisite_concept_ids": ["upsc.cse.polity.fundamental_rights.overview"],
  "related_concept_ids": ["upsc.cse.polity.dpsp.socialistic_principles"],
  "tags": ["constitution", "part_iii", "equality"],
  "source_books": ["Laxmikanth Ch.6"],
  "status": "active",
  "domain_catalog_version": "1.0.0",
  "created_at": "ISO8601",
  "updated_at": "ISO8601"
}
```

### 7.2 Field definitions

| Field | Owner | Mutable | Notes |
|---|---|---|---|
| `concept_id` | Domain | never | PK; Learning Graph node key |
| `importance` | Scoring Engine | yes (computed) | Cached Importance score 0–100; null until PYQ seed runs |
| `importance_version` | Scoring Engine | yes | e.g., `importance_v1` |
| `pyq_count` | PYQ Engine | yes (cached) | Denormalized count; recompute on `PYQDataChanged` |
| `difficulty` | Domain (default) + Assessment (refined) | yes | 1–5 scale; default from domain; refined by student performance later |
| `exam_stages` | Domain | rarely | Derived array: include `prelims` if `prelims_relevance>0`, etc. |
| `prerequisite_concept_ids` | Domain | versioned | Mirror of `PREREQUISITE` edges for fast reads |
| `parent_concepts` / `child_concepts` | Domain | versioned | Tree pointers; must match `parent_concept_id` consistency |
| `tags` | Domain | yes | Faceted search, Question Generation |
| `source_books` | Domain | yes | RAG anchor hints (V2) |

### 7.3 Derived fields (not stored on concept; computed at read time)

| Field | Derived from |
|---|---|
| `exam_relevance` (for Importance) | `max(prelims_relevance, mains_relevance)` normalized × stage weights for student's target stage |
| `exam_weight_band` (display) | `importance` → High/Medium/Low per Scoring v1.1 R5 |
| `is_high_importance` (Readiness coverage) | `importance ≥ 70` OR `prelims_relevance ≥ 85` (config `HIGH_IMPORTANCE_THRESHOLD`) |

---

## 8. Current Affairs Mapping Model

### 8.1 Purpose

Current Affairs are **time-stamped events**, not permanent syllabus nodes. They **link to permanent concepts** so CA study updates Retention/Mastery on the underlying knowledge.

### 8.2 CA entity (summary)

| Field | Description |
|---|---|
| `ca_id` | UUID |
| `title` | Headline |
| `summary` | Structured summary |
| `published_date` | UTC date |
| `source` | PIB, The Hindu, Economic Survey, etc. |
| `category` | national \| international \| economy \| science_env \| polity_governance \| reports |
| `importance_score` | 0–100 (CA team's deterministic rules; separate from concept Importance) |
| `status` | draft \| published \| archived |

### 8.3 Mapping rules

```
current_affairs_mappings:
  ca_id          → FK current_affairs
  concept_id     → FK concepts WHERE current_affairs_linkable = true
  link_weight    → float 0.0–1.0 (sum per ca_id SHOULD = 1.0; MUST NOT exceed 1.0)
  link_type      → enum (see below)
  mapped_by      → system | faculty | admin
  confidence     → 0.0–1.0 (for AI-suggested links; ≥0.85 to auto-publish)
```

| `link_type` | Meaning |
|---|---|
| `direct` | CA item is primarily about this concept |
| `contextual` | CA provides example/evidence for concept |
| `background` | Concept needed to understand CA |

**Cardinality rules:**
1. **One CA → many concepts** (typical 1–5 concepts).
2. **One concept → many CA items** (unbounded; indexed by date).
3. **Only link to `current_affairs_linkable=true` concepts.**
4. **Cross-subject linking allowed** (e.g., RBI policy → monetary_policy + inflation + current_affairs.economy).
5. **Auto-links require `confidence ≥ 0.85`**; otherwise queue for faculty review.

### 8.4 Worked example

**CA item:** `ca_id=ca_2026_0142` — *Digital Personal Data Protection Act, 2023*

| concept_id | link_weight | link_type |
|---|---:|---|
| `...fundamental_rights.article_21` | 0.35 | direct |
| `...fundamental_rights.overview` | 0.20 | contextual |
| `...governance.e_governance.digital_india` | 0.25 | direct |
| `...economy.it_digital.data_localization` | 0.20 | contextual |

**Engine effects:**
- Reading this CA item can trigger `StudySessionLogged` on linked concepts.
- CA-subject `CASub` in Readiness aggregates accuracy/coverage of CA-linked assessments.
- Revision Engine may boost priority when high-importance concept has recent CA link (`CURRENT_AFFAIRS_OF` edge, §10).

---

## 9. PYQ Mapping Model

### 9.1 PYQ question entity (summary)

| Field | Description |
|---|---|
| `question_id` | UUID |
| `exam_id` | `upsc_cse` |
| `year` | int |
| `paper` | `prelims_gs1` \| `mains_gs1` … `mains_gs4` \| `mains_essay` |
| `question_text` | text |
| `question_type` | mcq \| mains_descriptive \| essay |
| `difficulty` | 1–5 |
| `marks` | numeric |
| `status` | draft \| verified |

### 9.2 Mapping entity

```
pyq_mappings:
  question_id    → FK pyq_questions
  concept_id     → FK concepts WHERE pyq_mappable = true
  weight         → float 0.0–1.0
  mapping_type   → primary | secondary | distractor
  mapped_by      → system | faculty | admin
  verified       → bool
```

**Weight rules:**
- Sum of weights per `question_id` MUST equal `1.0` (±0.01 tolerance).
- **`primary`**: concept the question mainly tests (weight ≥0.50 typically).
- **`secondary`**: supporting concept (0.20–0.40).
- **`distractor`**: MCQ wrong-option concept (optional; used for misconception analytics).

### 9.3 Mapping patterns

| Pattern | Rule | Example |
|---|---|---|
| **Single concept** | one `primary` weight=1.0 | "Article 14 equality" MCQ → `article_14` |
| **Multi concept** | primary + secondary weights sum to 1.0 | Parliament committee MCQ → `parliament.committees` 0.7 + `parliament.overview` 0.3 |
| **Cross-subject** | allowed; each concept retains its subject | GST question → `economy.budget.gst` 0.6 + `polity.center_state_relations.financial_relations` 0.4 |
| **Unmapped** | `status=quarantine`; excluded from Importance computation | Pending faculty review queue |

### 9.4 Worked example

**Question:** Prelims 2022 GS1 Q18 (hypothetical) — Parliament joint session

| concept_id | weight | mapping_type |
|---|---:|---|
| `upsc.cse.polity.parliament.sessions` | 0.65 | primary |
| `upsc.cse.polity.parliament.structure` | 0.25 | secondary |
| `upsc.cse.polity.federalism.quasi_federal` | 0.10 | secondary |

**Engine effects:**
- Feeds `pyq_hits[]` for Importance (Scoring v1.0 §4).
- Increments `pyq_count` cache on concept.
- Creates `PYQ_OF` relationship edge (§10) for graph traversal.

---

## 10. Learning Graph Requirements

This section defines constraints the **LEARNING_GRAPH_SPECIFICATION.md** (next document) MUST inherit without re-deciding.

### 10.1 Node set

| Graph node type | Source table | Student state table |
|---|---|---|
| **Concept node** | `concepts` WHERE `status=active` | `student_concept_progress` |
| Subject node | `subjects` | aggregated from concepts (no direct row in V1) |
| Topic node | `topics` | aggregated from concepts (no direct row in V1) |

**Invariant:** `|Learning Graph nodes for student S| = |active concepts|`. No orphan nodes without domain rows.

### 10.2 Relationship types (canonical enum)

| Type | Direction | Semantics | Example |
|---|---|---|---|
| `PREREQUISITE` | A → B | A must be studied before B | `overview` → `article_14` |
| `BUILDS_ON` | A → B | B extends A (not strict order) | `article_32` → `writ_jurisdiction` |
| `RELATED_TO` | A ↔ B | Symmetric affinity; either order stored once | FR ↔ DPSP |
| `CURRENT_AFFAIRS_OF` | CA → Concept | CA item linked to concept (also in `current_affairs_mappings`) | DPDP Act → Article 21 |
| `PYQ_OF` | Question → Concept | PYQ mapped (also in `pyq_mappings`) | Q18 → parliament.sessions |

**Storage:**

```
concept_relationships:
  id                UUID PK
  exam_id           FK
  source_id         string (concept_id OR ca_id OR question_id)
  source_type       concept | current_affair | pyq_question
  target_id         string (always concept_id for edges consumed by Learning Graph)
  target_type       concept
  relationship_type enum (above)
  weight            float 0.0–1.0 default 1.0
  status            active | deprecated
```

**Legacy mapping (Part 2 §8):**

| Legacy | v1.0 canonical |
|---|---|
| `prerequisite` | `PREREQUISITE` |
| `related` | `RELATED_TO` |
| `dependent` | `BUILDS_ON` (reverse direction normalized) |
| `frequently_asked_with` | `RELATED_TO` + tag `co_occurrence=pyq` |

### 10.3 Prerequisite enforcement rules

1. **Mentor planning:** MUST NOT schedule a concept as *first study* if any `PREREQUISITE` concept has `mastery < 40` (config `PREREQ_MASTERY_FLOOR`), unless student explicitly overrides.
2. **Question Generation:** MUST NOT generate advanced questions on concept if prerequisites unmet.
3. **Revision Engine:** prerequisites do NOT block revision (forgotten prerequisites get higher priority).
4. **Cycles forbidden:** `PREREQUISITE` edges MUST form a DAG; validated at catalog publish time.

### 10.4 Concept relationship seed examples (Polity)

| source_id | relationship_type | target_id |
|---|---|---|
| `...fundamental_rights.article_14` | PREREQUISITE | `...fundamental_rights.overview` |
| `...fundamental_rights.writ_jurisdiction` | BUILDS_ON | `...fundamental_rights.article_32` |
| `...fundamental_rights.overview` | RELATED_TO | `...dpsp.overview` |
| `...parliament.legislative_process` | PREREQUISITE | `...parliament.structure` |
| `...judiciary.judicial_review` | BUILDS_ON | `...fundamental_rights.overview` |

### 10.5 Rollup rules (subject/topic aggregates)

For LEARNING_GRAPH_SPECIFICATION:

```
topic_mastery(student, topic)   = Σ(I_c · m_c) / Σ(I_c)   for c in topic
subject_mastery(student, subject) = Σ(I_c · m_c) / Σ(I_c)   for c in subject
```

Same formula for Retention. Used for UI navigation only; **scoring engines use concept-level values**.

---

## 11. Scoring Engine Dependencies

Cross-reference: `SCORING_ENGINE_SPECIFICATION_V1_1.md` (and v1.0 for unchanged formulas).

### 11.1 Field consumption matrix

| Domain field | Mastery | Retention | Importance (Exam Weight) | Readiness |
|---|---|---|---|---|
| `concept_id` | PK | PK | PK | PK (via sub-scores) |
| `subject_id` / `topic_id` | rollup only | rollup only | rollup only | driver labels (R8) |
| `prelims_relevance` | routing MCQ evidence | — | `exam_relevance` factor | stage routing |
| `mains_relevance` | routing Mains evidence | — | `exam_relevance` factor | stage routing |
| `importance` (computed) | — | — | output | weight in `KnowledgeSub`, `RetentionSub`, coverage |
| `pyq_count` / `pyq_mappings` | — | — | PYQ frequency input | indirect |
| `parent_concept_id` | optional rollup | optional rollup | — | — |
| `PREREQUISITE` edges | — | — | — | Mentor constraint (not score) |
| `exam_stages` | channel selection | — | — | sub-score selection |
| `current_affairs_linkable` | — | — | — | `CASub` eligibility |
| `pyq_mappable` | — | — | required for Importance | — |
| `status=active` | required | required | required | required in coverage denom |

### 11.2 Score-specific domain requirements

**Mastery (v1.0 §2)**
- Requires: `concept_id`, assessment events tagged with `concept_id`.
- MCQ/Mains routing uses `prelims_relevance` / `mains_relevance` to validate question-concept fit (mis-tagged questions quarantined).

**Retention (v1.0 §3)**
- Requires: `concept_id`, `last_event_at` per concept (study/revision events).
- Stability `S_base` uses Mastery (computed, not domain field).

**Importance / Exam Weight (v1.0 §4 + v1.1 R5)**
- Requires: `concept_id`, `pyq_mappings`, `prelims_relevance`, `mains_relevance`, optional faculty weight.
- `exam_relevance` = normalized `max(prelims_relevance, mains_relevance)` for student's target stage set.
- Output cached in `concepts.importance` + copied to `student_concept_progress.importance_score`.

**Readiness (v1.1 §4 — R3 Option A)**
- `KnowledgeSub`: importance-weighted **`MasteryNonMCQ`** rollup over concepts with non-MCQ data.
- `RetentionSub`: importance-weighted **Retention** over concepts with data.
- `MCQSub`: exam-wide MCQ accuracy (not per-concept domain field).
- `WritingSub`: Mains/essay; concepts with `mains_relevance > 0`.
- `CASub`: concepts linked via CA mappings in last 90 days.
- **Coverage denominator:** count of `is_high_importance` concepts with any mastery data (§7.3).

### 11.3 Domain → Scoring config keys

| Config key | Domain source |
|---|---|
| `HIGH_IMPORTANCE_THRESHOLD` | default 70; aligns with `importance` band |
| `PREREQ_MASTERY_FLOOR` | default 40; used by Mentor, not Scoring |
| `READINESS_FORMULA_VERSION` | `readiness_v1_1` (uses `MasteryNonMCQ`) |

---

## 12. Revision Engine Dependencies

Cross-reference: Scoring v1.0 §10.4 Revision Priority; v1.1 R1 (Weakness internal).

### 12.1 Required domain fields per scheduled revision

| Field | Used for |
|---|---|
| `concept_id` | revision row key |
| `importance` (computed) | `imp_f = I/100` |
| Retention (computed) | `retgap_f = (100−R)/100` |
| Weakness (computed inline) | `weak_f = W/100` |
| Student `exam_date` | `exam_proximity(D_exam)` |
| `PREREQUISITE` edges | ordering tie-break (not in priority formula) |
| `status=active` | eligibility |
| `prelims_relevance` / `mains_relevance` | filter revisions for student's target stage (optional config) |

### 12.2 Revision Priority formula (unchanged; domain inputs)

```
priority_raw = (I/100) · ((100−R)/100) · (W/100) · exam_proximity(D_exam)
Top-N concepts → revisions table
```

### 12.3 Domain-driven scheduling constraints

1. Only `status=active` concepts eligible.
2. Minimum inter-repetition interval: `0.5 × S` days (Retention stability; not a domain field).
3. Concepts with `importance ≥ 80` AND `retention < 60` MUST appear in Top-N if any revision slots available (hard constraint override).
4. `CURRENT_AFFAIRS_OF` edges with CA published in last 30 days: multiply priority by `1.15` (cap 100 after normalization).

---

## 13. Preparation Twin Dependencies

Cross-reference: Part 2 §17; Scoring v1.1 §3 (Twin rebuild on events).

### 13.1 Twin profile → domain mapping

| Twin profile | Domain inputs |
|---|---|
| **Knowledge Profile** | subject/topic rollups of Mastery, Retention; strongest/weakest via `subject_id` aggregates |
| **Assessment Profile** | concepts with `prelims_relevance>0` (MCQ), `mains_relevance>0` (Mains) |
| **Behavior Profile** | Revision Health (not domain); study sessions tagged with `concept_id` |
| **Prediction Profile** | Readiness + gated predictions; coverage uses `is_high_importance` concept set |

### 13.2 Required domain attributes

| Attribute | Purpose in Twin |
|---|---|
| `subject_id` | "Strongest/weakest subject" labels |
| `topic_id` | "Most forgotten topic" label |
| `concept_id` | finest-grain weak-area detection |
| `importance` | weight weak areas by exam weight |
| `exam_stages` | split Prelims vs Mains readiness narrative |
| Full taxonomy | Mentor explainability strings ("Economy → Monetary Policy → Repo Rate") |

### 13.3 Twin rebuild triggers involving domain

| Event | Domain data touched |
|---|---|
| `LearningGraphUpdated` | concept scores |
| `PYQDataChanged` | `importance` recache |
| `DomainCatalogUpdated` | new concepts → create empty progress rows on next login |

---

## 14. Database Representation

### 14.1 Entity-relationship overview

```
exams 1──* subjects 1──* topics 1──* concepts
                              │
concepts *──* concepts        via concept_relationships
concepts *──* pyq_questions   via pyq_mappings
concepts *──* current_affairs via current_affairs_mappings
students *──* concepts        via student_concept_progress (Learning Graph)
```

### 14.2 Entity definitions (no SQL)

#### `exams`

| Column | Type | Notes |
|---|---|---|
| exam_id | string PK | `upsc_cse` |
| exam_code | string unique | |
| exam_name | string | |
| exam_type | enum | |
| prelims_weight | decimal | |
| mains_weight | decimal | |
| interview_weight | decimal | |
| domain_catalog_version | string | |
| status | enum | |

#### `subjects`

| Column | Type | Notes |
|---|---|---|
| subject_id | string PK | |
| exam_id | FK | |
| subject_name | string | |
| subject_slug | string | |
| prelims_applicable | bool | |
| mains_applicable | bool | |
| sort_order | int | |
| status | enum | |

#### `topics`

| Column | Type | Notes |
|---|---|---|
| topic_id | string PK | |
| subject_id | FK | |
| exam_id | FK | |
| topic_name | string | |
| topic_slug | string | |
| prelims_relevance | int | 0–100 |
| mains_relevance | int | 0–100 |
| sort_order | int | |
| status | enum | |

#### `concepts`

| Column | Type | Notes |
|---|---|---|
| concept_id | string PK | **Learning Graph node ID** |
| topic_id | FK | |
| subject_id | FK | must match topic's subject |
| exam_id | FK | |
| parent_concept_id | FK nullable | self-ref |
| concept_name | string | |
| concept_slug | string | |
| concept_type | enum | §6.3 |
| prelims_relevance | int | |
| mains_relevance | int | |
| interview_relevance | int | default 0 |
| difficulty | int | 1–5 |
| importance | decimal nullable | cached; Scoring Engine writes |
| importance_version | string nullable | |
| current_affairs_linkable | bool | |
| pyq_mappable | bool | |
| pyq_count | int default 0 | cached |
| exam_stages | string[] | derived |
| tags | string[] | |
| metadata | JSONB | extensions §7.1 |
| status | enum | |
| domain_catalog_version | string | |

#### `concept_relationships`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| exam_id | FK | |
| source_id | string | |
| source_type | enum | concept \| current_affair \| pyq_question |
| target_id | string | concept_id |
| target_type | enum | always concept |
| relationship_type | enum | §10.2 |
| weight | decimal | |
| status | enum | |

#### `pyq_mappings`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| question_id | FK | |
| concept_id | FK | |
| weight | decimal | sum=1 per question |
| mapping_type | enum | primary \| secondary \| distractor |
| mapped_by | enum | |
| verified | bool | |

#### `current_affairs_mappings`

| Column | Type | Notes |
|---|---|---|
| id | UUID PK | |
| ca_id | FK | |
| concept_id | FK | |
| link_weight | decimal | |
| link_type | enum | §8.3 |
| mapped_by | enum | |
| confidence | decimal | |

### 14.3 Integrity constraints (application-enforced)

1. `concepts.subject_id` MUST equal `topics.subject_id` for the concept's `topic_id`.
2. `concept_relationships.target_id` MUST reference `concepts.concept_id` with `status=active`.
3. `pyq_mappings.concept_id` MUST have `pyq_mappable=true`.
4. `current_affairs_mappings.concept_id` MUST have `current_affairs_linkable=true`.
5. `PREREQUISITE` graph MUST be acyclic (validated on catalog publish).
6. Every `active` concept MUST belong to an `active` topic and subject.
7. `student_concept_progress` rows created ONLY for `concepts.status=active`.

### 14.4 Index requirements (logical)

- `concepts(topic_id, status)`
- `concepts(subject_id, status)`
- `concept_relationships(source_id, relationship_type)`
- `concept_relationships(target_id, relationship_type)`
- `pyq_mappings(concept_id)`
- `current_affairs_mappings(concept_id, ca_id)`

---

## 15. Future Extensibility

### 15.1 Multi-exam pattern (APPSC, TSPSC, SSC, Banking, CAT, GATE)

**No domain-layer redesign.** Add a new exam by:

1. Insert `exams` row with new `exam_code` (e.g., `appsc_group1`).
2. Seed `subjects`, `topics`, `concepts` under that `exam_id`.
3. Reuse all tables, relationship types, mapping rules, and engine logic.
4. Configure exam-specific weights (`prelims_weight`, etc.) and stage sets.

```
exam_code namespace isolation:
  upsc.cse.polity.fundamental_rights.article_14   ← UPSC
  appsc.group1.polity.fundamental_rights.article_14 ← APPSC (may share slug path, different exam_id)
```

**Cross-exam concept linking (optional V3):** `RELATED_TO` edges may connect concepts across `exam_id` values for students preparing for multiple exams. Never merge rows; link with edges.

### 15.2 Exam-specific customization points

| Customizable per exam | Shared infrastructure |
|---|---|
| Subject/topic/concept catalog | Table shapes, relationship types |
| `prelims_relevance` / `mains_relevance` defaults | Scoring formulas |
| PYQ corpus | PYQ mapping rules |
| Stage definitions (e.g., SSC Tier I/II) | Revision Priority formula |
| Optional subjects (UPSC Optional) | Learning Graph node model |

### 15.3 Optional subject (UPSC) — V2 placeholder

| Field | Value |
|---|---|
| Pattern | Treat each Optional (e.g., Geography Optional) as additional `subjects` with `optional=true` flag |
| Student binding | `students.optional_subject_id` filters Importance weighting (Scoring v1.0 §4.10 per-student copy) |
| V1 | Not seeded; architecture supports via `subjects.optional` bool |

### 15.4 Catalog fork strategy

| Scenario | Approach |
|---|---|
| UPSC syllabus revision | New `domain_catalog_version`; deprecate old concepts (`status=deprecated`); migrate progress rows |
| State PSC overlap | Share concepts via `RELATED_TO`; do not duplicate identical concepts across exams unless exam-specific framing differs |
| Banking/SSC simpler hierarchy | Same 4 levels; fewer subjects; engines unchanged |

### 15.5 What extensibility does NOT allow

- Introducing a non-concept Learning Graph node type without a spec amendment.
- Storing Mastery/Retention on topics directly (rollups only).
- Exam-specific scoring formulas (formulas remain in Scoring Engine; domain supplies inputs only).

---

## Appendix A — Identifier quick reference

| Level | Pattern | Example |
|---|---|---|
| Exam | `{exam_code}` | `upsc_cse` |
| Subject | `{exam_code}.{subject_slug}` | `upsc.cse.polity` |
| Topic | `{subject_id}.{topic_slug}` | `upsc.cse.polity.fundamental_rights` |
| Concept | `{topic_id}.{concept_slug}` | `upsc.cse.polity.fundamental_rights.article_14` |

## Appendix B — Counts summary (V1)

| Entity | Count |
|---|---:|
| Exams | 1 (`upsc_cse`) |
| Subjects | 17 |
| Topics | 98 |
| Concepts (target) | ≥497 active |
| Relationship types | 5 |
| Concept types | 8 |

## Appendix C — LEARNING_GRAPH_SPECIFICATION.md handoff checklist

The next document MUST define, referencing this spec:

- [ ] `student_concept_progress` row lifecycle (create on onboarding / catalog add)
- [ ] Event → score update matrix (already in Scoring v1.1; domain supplies `concept_id` tags)
- [ ] Graph traversal algorithms for Mentor (PREREQUISITE-aware planning)
- [ ] Rollup formulas (§10.5) for topic/subject navigation UI
- [ ] Concept node states: `unrated`, `active`, `deprecated`
- [ ] Backfill procedure on `DomainCatalogUpdated`
- [ ] Faculty aggregate queries (Scoring v1.1 §6.5) over `subject_id` / `topic_id`

## Appendix D — Consistency notes with prior docs

| Prior doc | This spec resolves |
|---|---|
| Part 2 §7 four levels (Subject/Topic/Subtopic/Concept) | **Subtopic eliminated**; Topic = former Subtopic+Topic merged |
| Part 2 §8 relationship types | Mapped to §10.2 canonical enums |
| Part 2 §10 Importance formula | Domain supplies inputs; Scoring Engine computes (unchanged) |
| Master Plan §1.4 `syllabus` module | Implemented as subjects/topics/concepts tables here |
| Scoring v1.1 R5 Exam Weight | Display label for `importance` sourced from domain `concept_id` |
| Scoring v1.1 R3 MasteryNonMCQ | Requires concept-level MCQ vs non-MCQ evidence tagging on assessments |

---

*End of Exam Domain Specification v1.0. This document is the canonical UPSC knowledge hierarchy for PrepOS. All engines consume it; none may invent parallel taxonomy. Next document: `LEARNING_GRAPH_SPECIFICATION.md`.*
