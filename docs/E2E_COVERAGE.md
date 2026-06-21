# E2E Test Coverage

**Generated:** 2026-06-18  
**Framework:** Playwright (`apps/web/playwright.config.ts`)  
**Test directory:** `apps/web/e2e/tests/`

---

## Test Suites

| Suite | File | Journeys covered |
|-------|------|------------------|
| Smoke | `smoke.spec.ts` | App loads |
| Auth | `auth.spec.ts` | Login, redirect |
| API health | `api-health.spec.ts` | Backend reachable |
| Student | `student.spec.ts` | Dashboard, activities, revision, learning graph |
| Mentor | `mentor.spec.ts` | Dashboard, queue |
| Admin knowledge | `admin-knowledge.spec.ts` | Knowledge ops |
| **Admin** | `admin.spec.ts` | **NEW** — admin home, security sub-pages, P11, agent ops |
| **Faculty** | `faculty.spec.ts` | **NEW** — faculty workspace nav |

---

## Journey Coverage Matrix

| Journey | Covered | Spec |
|---------|---------|------|
| Login | ✅ | `auth.spec.ts` |
| Student dashboard | ✅ | `student.spec.ts` |
| Student activities | ✅ | `student.spec.ts` |
| Student copilot | ⚠️ | Manual — copilot panel in shell |
| Student knowledge | ❌ | No dedicated spec |
| Student planning | ❌ | Add `student-planning.spec.ts` |
| Student forecasting | ❌ | Add `student-forecasting.spec.ts` |
| Student recommendations | ❌ | Add after engine migration verify |
| Mentor dashboard | ✅ | `mentor.spec.ts` |
| Mentor queue | ✅ | `mentor.spec.ts` |
| Faculty workspace | ✅ | `faculty.spec.ts` |
| Admin home | ✅ | `admin.spec.ts` |
| Admin security pages | ✅ | `admin.spec.ts` |
| Admin P11 dashboards | ✅ partial | jobs + platform-readiness |
| Admin agents/approvals | ✅ partial | agent-evaluation + approvals list |
| Admin copilot analytics | ❌ | |
| Admin institution/cohort | ❌ | |

---

## Critical Workflow Status

| Workflow | E2E | Notes |
|----------|-----|-------|
| login | ✅ | All suites use `loginAs()` helper |
| copilot | ⚠️ | UI present; no automated query test |
| knowledge | ✅ partial | `admin-knowledge.spec.ts` |
| planning | ❌ | |
| forecasting | ❌ | |
| recommendations | ❌ | Engine wired; spec pending |
| interventions | ❌ | |
| cohort | ❌ | |
| institution | ❌ | |
| agents | ✅ partial | approvals + evaluation page load |

---

## Running Tests

```bash
cd apps/web
npm run test:e2e
```

**Prerequisites:**
- API at `http://localhost:8000`
- Web at `http://localhost:3000`
- Demo seed: `backend/scripts/seed_demo_data.py`

**Demo credentials** (from `e2e/helpers/auth.ts`):

| Role | Email |
|------|-------|
| Student | `student@prepos-demo.example.com` |
| Faculty | `faculty@prepos-demo.example.com` |
| Admin | `admin@prepos-demo.example.com` |
| Password | `SecurePass123!` |

---

## Recommended Next Specs (not implemented — out of scope for fix pass)

1. `student-recommendations.spec.ts` — verify engine cards render
2. `admin-approvals.spec.ts` — approve/reject with seeded pending action
3. `middleware-auth.spec.ts` — student blocked from `/admin`
4. `worker-banner.spec.ts` — banner visible when worker down

---

*Phase 11 deliverable.*
