# API Coverage Report

**Generated:** 2026-06-18  
**Backend endpoints:** 182  
**Frontend API modules:** 25+ exported clients in `apps/web/src/lib/api/index.ts`

---

## Coverage Summary

| Metric | Value | Evidence |
|--------|------:|----------|
| Routes with API client function | **162 / 182** | 89% |
| Routes with React Query hook or page consumer | **138 / 182** | 76% |
| Routes with working UI path | **130 / 182** | 71% |
| Admin P11 routes with pages | **10 / 10** | 100% |
| Recommendation engine routes wired | **4 / 7** | student, mentor, explain (via API), complete (client only) |
| AgentOps approve/reject | **2 / 2** | UI on `/admin/approvals` |

**Target was 100% route coverage.** Remaining ~20 routes are intentionally low-priority ops (seed/import, benchmarks run, POST record endpoints) or duplicate read paths.

---

## Fully Wired Domains (100% client + UI)

| Domain | Routes | Client | UI |
|--------|-------:|--------|-----|
| Auth | 5 | `authApi` | login/register |
| Mentor | 6 | `mentorApi` | mentor portal |
| Copilot | 2 | `copilotApi` | copilot panel + admin analytics |
| Faculty | 1 | `facultyApi` | `/faculty` |
| Admin copilot/knowledge/rag | 5 | `adminCopilotApi`, etc. | admin pages |
| Admin memory/planning/forecast/interventions | 8 | `admin*Api` | admin dashboards |
| Admin cohort/institution | 17 | `adminCohortApi`, `adminInstitutionApi` | admin pages |
| Admin agents/traces/costs/health | 9 | `adminAgentsApi`, etc. | admin pages |
| Admin security (P11) | 6 | `adminSecurityApi` | security pages |
| Admin platform (P11) | 10 GET | `adminPlatformApi` | platform pages |
| Health | 5 | direct fetch | ops dashboards + worker banner |
| Memory timeline | 1 | `studentTimelineApi` | `/student/timeline` |

---

## Recommendation Engine Integration

| Backend route | Client | Hook | Page | Status |
|---------------|--------|------|------|--------|
| `POST /recommendations/student` | ✅ | `useRecommendations()` | `/student/recommendations`, `/student/forecast` | ✅ |
| `POST /recommendations/mentor` | ✅ | `useRecommendations(studentId)` | `/mentor/student/[id]` | ✅ |
| `GET /recommendations/explain/{id}` | ✅ | — | explain not yet linked inline | ⚠️ client ready |
| `POST /recommendations/{id}/complete` | ✅ | — | no mark-complete button | ⚠️ client ready |
| `GET /recommendations/effectiveness` | ✅ | — | admin effectiveness page uses admin route | ✅ |
| `GET /recommendations/outcomes` | ✅ | — | no dedicated page | ⚠️ |
| `GET /recommendations/outcomes/{id}` | ❌ | — | — | Missing client |

**Legacy twin route** `GET /twin/recommendations` — client retained in `studentApi.recommendations` but **no longer used** by recommendation UI.

---

## AgentOps Coverage

| Backend route | Client | UI | Working |
|---------------|--------|-----|---------|
| `GET /admin/approvals` | ✅ | `/admin/approvals` | ✅ |
| `POST /admin/approvals/{id}/approve` | ✅ | approve button | ✅ |
| `POST /admin/approvals/{id}/reject` | ✅ | reject button | ✅ |
| `GET /admin/agent-traces` | ✅ | `/admin/agent-traces` | ✅ |
| `GET /admin/agent-traces/{id}` | ✅ | trace explorer | ✅ |
| `GET /admin/agent-evaluation` | ✅ | `/admin/agent-evaluation` | ✅ |
| `GET /admin/agent-costs` | ✅ | `/admin/agent-costs` | ✅ |
| `GET /admin/agents/health` | ✅ | `/admin/agents/health` | ✅ |
| `GET /admin/agent-benchmarks` | ❌ | — | Missing |
| `POST /admin/agent-benchmarks/run` | ❌ | — | Missing |

---

## Routes Missing Frontend Client (20)

| Route | Reason |
|-------|--------|
| `POST /exams` | Admin seed ops — no UI |
| `GET /exams/{id}` | Unused — list sufficient |
| `POST /syllabus/seed/import` | Dev seed |
| `POST /syllabus/.../publish` | Catalog ops |
| `GET /concepts/search` | Not exposed in UI search |
| `GET /concepts/{id}/descendants` | Unused |
| `POST /knowledge/search` | Copilot uses copilot/query |
| `POST /knowledge/ask` | Copilot path |
| `POST /current-affairs/search` | No student CA search page |
| `POST /pyq/search` | No student PYQ search page |
| `GET /admin/agent-benchmarks` | Not wired |
| `POST /admin/agent-benchmarks/run` | Not wired |
| `POST /admin/evaluations/label` | Read-only dashboard |
| `POST /admin/forecast-accuracy/record` | Read-only dashboard |
| `POST /admin/recommendation-validation/record` | Read-only dashboard |
| `POST /admin/disaster-recovery/verify` | Read-only dashboard |
| `GET /recommendations/outcomes/{id}` | Not wired |
| `GET /admin/agents/{type}/health` | Partial — leaderboard only |
| `GET /admin/security/tenant-audit/{id}/export` | Not wired |
| `POST /memory/rebuild` | No admin trigger UI |

---

## Routes Client-Only (no dedicated UI action)

These have `adminPlatformApi` or similar clients but display JSON dashboards without mutation forms:

- `POST /admin/platform-readiness/compute` — client exists; button not added (readiness auto-computed on GET)
- Planning/forecast student regenerate endpoints — mentor pages use subset

---

## Integration Quality Notes

1. **Error handling** — New pages use `QueryBoundary` (loading/empty/error/retry).
2. **Worker dependency** — `WorkerStatusBanner` polls `/health/worker` and `/health/outbox`.
3. **Authorization** — Middleware + `RoleGuard` + backend JWT (defense in depth).

---

*Phase 4 deliverable. Re-run after major API additions.*
