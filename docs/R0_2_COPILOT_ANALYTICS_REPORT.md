# Sprint R0.2 — Copilot Analytics & Adoption Validation

**Date:** 2026-06-18  
**Scope:** Copilot usage tracking, admin analytics API, adoption dashboard, CSV export — no RAG/LLM/pgvector.

**Related:** [R0_1_COPILOT_IMPLEMENTATION_REPORT.md](./R0_1_COPILOT_IMPLEMENTATION_REPORT.md)

---

## Summary

Sprint R0.2 instruments Copilot v0 with persistent analytics so pilot teams can measure adoption and decide whether P7 RAG investment is justified.

---

## Database schema (migration `027_copilot_analytics`)

| Table | Purpose |
|-------|---------|
| `copilot_sessions` | 30-minute idle session grouping per user/persona |
| `copilot_queries` | One row per `POST /copilot/query` with timing and intent |
| `copilot_intent_metrics` | Daily rollup `(tenant, date, persona, intent)` |

**Tracked fields per query:** `user_id`, `role`, `persona`, `intent`, `query_text`, `response_time_ms`, `created_at`, plus `session_id`.

---

## Tracking flow

1. User sends `POST /api/v1/copilot/query` (optional `session_id` for continuity).
2. Copilot service routes intent and builds deterministic answer.
3. `CopilotAnalyticsService.record_query()`:
   - Reuses active session within 30 minutes or creates a new one.
   - Inserts `copilot_queries` row.
   - Upserts `copilot_intent_metrics` for the current UTC date.
4. Response includes `session_id` for subsequent queries in the same session.

**Module paths:**

- `backend/src/prepos/application/copilot/analytics_service.py`
- `backend/src/prepos/infrastructure/db/repositories/copilot_analytics_repository.py`

---

## Admin API

| Method | Path | Auth |
|--------|------|------|
| `GET` | `/api/v1/admin/copilot/analytics?days=30` | `institute_admin` |
| `GET` | `/api/v1/admin/copilot/analytics/export?days=30` | `institute_admin` (CSV) |

**Metrics returned:**

- DAU / WAU
- Total queries, unique copilot users, queries per active user
- Unknown intent rate
- Student / mentor / admin usage breakdown
- Intent distribution
- Daily usage trend
- Top prompts & unknown intent prompts
- Adoption funnel (registered → sessions → first query → 3+ queries → 5+ queries)
- Pilot success criteria evaluation

---

## Pilot success criteria (automated)

| Criterion | Target | Field |
|-----------|--------|-------|
| Active user adoption | ≥40% of tenant users | `success_criteria.active_user_adoption_met` |
| Unknown intent rate | <15% | `success_criteria.unknown_intent_rate_met` |
| Queries per active user | >3 | `success_criteria.queries_per_active_user_met` |
| Content-explanation signal | In top prompts (proxy) | `success_criteria.content_explanation_in_top_five_met` |

**Note:** Native RAG content intents do not exist in v0. The dashboard uses a **proxy signal** — top prompts containing `explain`, `define`, `what is`, etc. — to estimate demand for P7 knowledge Q&A.

---

## Frontend

**Route:** `/admin/copilot`

**Features:**

- KPI tiles (DAU, WAU, queries, queries/user)
- Persona usage cards
- Success criteria checklist
- CSS bar charts: daily trend, intent distribution, top prompts, unknown intents, adoption funnel
- Period selector (7–90 days)
- Export CSV button
- Link from `/admin/health`

**Files:**

- `apps/web/src/app/admin/copilot/page.tsx`
- `apps/web/src/components/admin/copilot-analytics-dashboard.tsx`

---

## Tests

| File | Coverage |
|------|----------|
| `tests/unit/test_copilot_analytics_service.py` | Recording + analytics math + CSV |
| `tests/unit/test_migration_027_copilot_analytics.py` | Migration head |
| `tests/contract/test_copilot_analytics_openapi_contract.py` | Admin routes registered |
| Updated `tests/unit/test_copilot_service.py` | Analytics integration mock |

Run:

```bash
cd backend
pytest tests/unit/test_copilot_analytics_service.py tests/unit/test_migration_027_copilot_analytics.py \
  tests/contract/test_copilot_analytics_openapi_contract.py tests/unit/test_copilot_*.py -q
cd ../apps/web && npm run typecheck
```

---

## Explicit non-goals (honored)

- No RAG, LLM, pgvector, embeddings, or semantic search
- No new copilot intents — analytics only

---

## How to use during pilot

1. Deploy migration `027_copilot_analytics`.
2. Run pilot with Copilot enabled for all roles.
3. Review `/admin/copilot` weekly.
4. Export CSV for offline analysis or sharing with stakeholders.
5. If success criteria are met **and** unknown/content-proxy prompts are high → prioritize P7 RAG.
6. If adoption is low but unknown rate is high → improve intent router before RAG.
7. If adoption is low and unknown rate is low → improve Copilot discoverability/UX first.

---

*End of Sprint R0.2*
