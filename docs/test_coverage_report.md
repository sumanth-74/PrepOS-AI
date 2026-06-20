# Test Coverage Audit — Sprint P1.0

**Generated:** 2026-06-20  
**Scope:** `backend/tests/` — unit, integration, contract; frontend tests

---

## Executive Summary

Backend test suite is **strong and broad** (~454 test functions across 150 files), with heavy unit coverage of scoring, twin, mentor, and study plan engines. Integration tests cover auth, onboarding, LG event handlers, and twin projections. **No frontend E2E tests** exist. **No pytest-cov report** was generated in this audit; coverage percentages are estimated from test distribution.

**Testing readiness:** 70/100 (backend strong, frontend/ops gaps)

---

## Test Inventory

| Layer | Files | Test functions | Focus |
|-------|-------|----------------|-------|
| **Unit** | 121 | 363 | Domain logic, handlers, DTOs, migrations, scoring golden |
| **Integration** | 24 | 86 | Auth, onboarding, LG s45–s60, twin projections, outbox |
| **Contract** | 5 | 5 | OpenAPI schema compliance |
| **Total** | **150** | **454** | |

**Collection note:** `pytest --collect-only` reported 448 collected with **6 collection errors** in some integration modules (import/path issues when run outside full test env). Full suite should be run in CI with Postgres test DB.

---

## Unit Test Coverage (by domain)

| Domain | Approx. tests | Representative files |
|--------|---------------|----------------------|
| Scoring / readiness | 50+ | `test_scoring_*`, `test_readiness_*` |
| Twin / projections | 40+ | `test_twin_*`, `test_twin_rebuild_service` |
| Study plan | 15+ | `test_study_plan_*`, `test_adaptive_study_plan_v1` |
| Goals / forecast | 25+ | `test_goal_*`, `test_forecast_*`, `test_milestone_*` |
| Mentor / cases | 30+ | `test_mentor_*`, `test_case_*` |
| Interventions / behavior | 25+ | `test_intervention_*`, `test_behavior_*` |
| Learning graph domain | 10+ | `test_learning_graph_*` |
| Personalization | 15+ | `test_personalization_*`, `test_personalized_*` |
| Security / tenancy | 5+ | `test_security`, `test_tenancy` |
| Migrations | 15+ | `test_migration_*` |
| Handlers (event) | 20+ | `test_*_handlers.py` |

---

## Integration Test Coverage

| Flow | Status | File(s) |
|------|--------|---------|
| Auth register/login/refresh/logout | ✅ | `test_auth_flow.py`, `test_foundation_flow.py` |
| Student onboarding + outbox | ✅ | `test_student_onboarding_flow.py` |
| LG provisioning | ✅ | `test_learning_graph_provisioning_flow.py` |
| LG event handlers (assessment, revision) | ✅ | `test_learning_graph_event_handlers.py` |
| LG → twin cascade | ✅ | `test_learning_graph_twin_freshness_cascade.py` |
| Twin projections (decision, mentor, intervention) | ✅ | Multiple `test_twin_*_projection.py` |
| Exam catalog import/publish | ✅ | `test_exam_catalog_flow.py` |
| Outbox idempotency | ✅ | `test_outbox_idempotency.py` |
| Sprint compliance (s45–s60) | ✅ | `test_learning_graph_s*.py` |

---

## Contract Tests

| API surface | File |
|-------------|------|
| Global OpenAPI | `test_openapi_contract.py` |
| Exam | `test_exam_openapi_contract.py` |
| Student | `test_student_openapi_contract.py` |
| Learning graph | `test_learning_graph_openapi_contract.py` |
| Twin | `test_twin_openapi_contract.py` |

---

## E2E Coverage

| Layer | Status |
|-------|--------|
| Backend API E2E (scripted) | ✅ `seed_demo_data.py`, `i12_e2e_validation.py` |
| Playwright / Cypress | ❌ None |
| Frontend unit tests | ❌ None |
| Frontend integration tests | ❌ None |

---

## Missing Coverage (prioritized)

### P0 — Pilot gaps

| Gap | Risk |
|-----|------|
| No frontend E2E | UI regressions undetected (mentor resolve enum bug) |
| No CI pipeline documented running full pytest | Backend regressions on merge |
| Celery worker integration test in compose | Outbox not processed in prod-like env |

### P1 — Production gaps

| Gap | Risk |
|-----|------|
| No load/performance tests | Scale surprises |
| API audit endpoints without contract tests | goals, mentor, study_plan OpenAPI drift |
| No security tests (rate limit, RBAC fuzz) | Perimeter gaps |
| 6 pytest collection errors | Incomplete CI signal |

### P2

| Gap | Risk |
|-----|------|
| No mutation testing | Edge case escapes |
| No visual regression | UI polish regressions |

---

## Recommended Test Additions (P1.1 — no new engines)

1. **Playwright smoke** — login, student dashboard, mentor queue (5–10 tests)  
2. **OpenAPI contract** — mentor, goals, study_plan routers  
3. **Frontend component tests** — LoginForm, mentor resolve enum select (once fixed)  
4. **CI job** — `pytest` + `npm run build` on PR  
5. **Compose integration job** — API + worker + single activity E2E  

---

## How to Run

```bash
# Backend (requires PostgreSQL test DB or conftest skip)
cd backend && source .venv/bin/activate
pytest

# Frontend build verification
cd apps/web && npm run typecheck && npm run lint && npm run build

# Scripted E2E
python backend/scripts/i12_e2e_validation.py
```

---

## Coverage Estimate (qualitative)

| Area | Estimated coverage | Confidence |
|------|-------------------|------------|
| Domain scoring engines | High (~80%+) | Many golden tests |
| Event handlers | High | Dedicated handler tests |
| API routers | Medium | Contract tests partial |
| Repositories | Medium | Via integration |
| Frontend | None | 0% automated |

*Formal `pytest --cov` report recommended for next sprint baseline.*
