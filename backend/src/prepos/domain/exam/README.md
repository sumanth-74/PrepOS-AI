# Exam Domain Bounded Context

## Ownership

The **Exam / Syllabus** bounded context owns the platform-global UPSC knowledge catalog:

- Exams, exam tracks (GS1–GS4, Essay, CSAT)
- Subjects, topics, concepts
- Concept relationships (`PREREQUISITE`, `BUILDS_ON`, `RELATED_TO`, …)
- Catalog versions and publish workflow

Catalog data is **platform-global** (no tenant scoping on taxonomy tables). Tenant isolation applies only to admin mutations via RBAC.

## Hierarchy Model

```
Exam (upsc_cse)
 └── ExamTrack (prelims_gs1, mains_gs1, …)
 └── Subject (upsc.cse.polity)
      └── Topic (upsc.cse.polity.fundamental_rights)
           └── Concept (Learning Graph node candidate)
                └── optional child concepts (max depth 2)
```

Concept relationships form a typed graph independent of the parent pointer.

## APIs

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/exams` | List exams |
| POST | `/api/v1/exams` | Create exam (admin) |
| GET | `/api/v1/exams/{exam_id}` | Get exam |
| GET | `/api/v1/syllabus/{exam_id}/tree` | Full syllabus tree |
| POST | `/api/v1/syllabus/{exam_id}/catalog/versions/{version}/publish` | Publish catalog |
| POST | `/api/v1/syllabus/seed/import` | Idempotent UPSC seed import |
| GET | `/api/v1/concepts/search` | Search concepts (paginated) |
| GET | `/api/v1/concepts/{concept_id}` | Get concept |
| GET | `/api/v1/concepts/{concept_id}/ancestors` | Parent chain + topic/subject |
| GET | `/api/v1/concepts/{concept_id}/descendants` | Child concepts |

## Events

### `DomainCatalogUpdated`

- **Producer:** `PublishCatalogVersionUseCase`
- **Scope:** platform-global (`tenant_id = null`, metadata `scope=platform`)
- **Payload:** `exam_id`, `catalog_version`, `concepts_added[]`, `concepts_deprecated[]`
- **Transport:** transactional outbox → Celery dispatcher → registered handlers

Consumers (future sprints): Learning Graph backfill, Revision cancel, PYQ/CA revalidation, Twin rebuild.

## Seed Data

Canonical seed: `seeds/upsc_cse_concepts_v1_0.json` (generated from `application/exam/seed_catalog.py`).

Regenerate:

```bash
cd backend && python3 scripts/generate_upsc_seed.py
```

## Invariants (publish-time)

1. Active concepts require active topic + subject
2. `concepts.subject_id` must match topic's subject
3. Concept hierarchy depth ≤ 2
4. `PREREQUISITE` edges form a DAG
5. Each active topic has ≥ 3 active concepts
