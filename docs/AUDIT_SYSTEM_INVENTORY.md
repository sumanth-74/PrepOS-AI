# PrepOS System Inventory Audit

**Generated:** 2026-06-18  
**Scope:** Full frontend route inventory, backend API inventory, integration matrix, navigation graph  
**Purpose:** Production-readiness baseline for integration and UX hardening pass

---

## 1. Executive Summary

| Area | Count | Notes |
|------|------:|-------|
| Backend API endpoints | 182 | 177 under `/api/v1` + 5 root health |
| Frontend pages | 50 → **62** | +12 admin/platform/security pages added in readiness pass |
| Admin pages | 24 → **36** | Includes `/admin` home, P11 dashboards, security sub-pages, agent evaluation |
| Student pages | 12 | All under `student/layout.tsx` |
| Mentor pages | 9 | All under `mentor/layout.tsx` |
| Faculty pages | 1 | Now has `faculty/layout.tsx` |
| Auth/public pages | 4 | `/`, `/login`, `/register`, `/unauthorized` |

---

## 2. Frontend Route Inventory

### 2.1 Admin (`/admin/*`) — 36 routes

| Route | Page file | Nav reachable |
|-------|-----------|---------------|
| `/admin` | `admin/page.tsx` | ✅ Sidebar + quick actions |
| `/admin/copilot` | `admin/copilot/page.tsx` | ✅ |
| `/admin/knowledge` | `admin/knowledge/page.tsx` | ✅ |
| `/admin/knowledge/[id]` | `admin/knowledge/[id]/page.tsx` | ✅ (detail) |
| `/admin/rag-quality` | `admin/rag-quality/page.tsx` | ✅ |
| `/admin/current-affairs` | `admin/current-affairs/page.tsx` | ✅ |
| `/admin/current-affairs/[id]` | `admin/current-affairs/[id]/page.tsx` | ✅ |
| `/admin/pyq` | `admin/pyq/page.tsx` | ✅ |
| `/admin/recommendations` | `admin/recommendations/page.tsx` | ✅ |
| `/admin/recommendation-effectiveness` | `admin/recommendation-effectiveness/page.tsx` | ✅ |
| `/admin/recommendation-validation` | `admin/recommendation-validation/page.tsx` | ✅ **NEW** |
| `/admin/memory` | `admin/memory/page.tsx` | ✅ |
| `/admin/planning` | `admin/planning/page.tsx` | ✅ |
| `/admin/forecasting` | `admin/forecasting/page.tsx` | ✅ |
| `/admin/forecast-accuracy` | `admin/forecast-accuracy/page.tsx` | ✅ **NEW** |
| `/admin/interventions` | `admin/interventions/page.tsx` | ✅ |
| `/admin/cohort` | `admin/cohort/page.tsx` | ✅ |
| `/admin/institution` | `admin/institution/page.tsx` | ✅ |
| `/admin/institution/outcomes` | `admin/institution/outcomes/page.tsx` | ✅ |
| `/admin/agents` | `admin/agents/page.tsx` | ✅ |
| `/admin/agent-traces` | `admin/agent-traces/page.tsx` | ✅ |
| `/admin/agent-evaluation` | `admin/agent-evaluation/page.tsx` | ✅ **NEW** |
| `/admin/agent-costs` | `admin/agent-costs/page.tsx` | ✅ |
| `/admin/approvals` | `admin/approvals/page.tsx` | ✅ |
| `/admin/agents/health` | `admin/agents/health/page.tsx` | ✅ |
| `/admin/security` | `admin/security/page.tsx` | ✅ |
| `/admin/security/tenant-audit` | `admin/security/tenant-audit/page.tsx` | ✅ **NEW (was 404)** |
| `/admin/security/knowledge` | `admin/security/knowledge/page.tsx` | ✅ **NEW (was 404)** |
| `/admin/security/rate-limits` | `admin/security/rate-limits/page.tsx` | ✅ **NEW (was 404)** |
| `/admin/platform-readiness` | `admin/platform-readiness/page.tsx` | ✅ |
| `/admin/jobs` | `admin/jobs/page.tsx` | ✅ **NEW** |
| `/admin/evaluations` | `admin/evaluations/page.tsx` | ✅ **NEW** |
| `/admin/monitoring` | `admin/monitoring/page.tsx` | ✅ **NEW** |
| `/admin/disaster-recovery` | `admin/disaster-recovery/page.tsx` | ✅ **NEW** |
| `/admin/adoption` | `admin/adoption/page.tsx` | ✅ **NEW** |
| `/admin/outcomes` | `admin/outcomes/page.tsx` | ✅ **NEW** |
| `/admin/health` | `admin/health/page.tsx` | ✅ |

**Layout:** `admin/layout.tsx` → `AdminShell` (sectioned sidebar, breadcrumbs, global search, worker banner)

### 2.2 Student (`/student/*`) — 12 routes

All wrapped by `student/layout.tsx` (`RoleGuard`, `OnboardingGuard`, `StudentShell`, `WorkerStatusBanner`).

| Route | Notes |
|-------|-------|
| `/student/dashboard` | Twin KPIs |
| `/student/activities` | Activity logging |
| `/student/learning-graph` | Graph overview |
| `/student/recommendations` | **Recommendation engine** (POST `/recommendations/student`) |
| `/student/revision-queue` | Spaced repetition |
| `/student/study-plan` | Legacy study plan |
| `/student/planning` | Adaptive planning |
| `/student/forecasting` | Goal forecasting |
| `/student/forecast` | Twin forecast + engine recs |
| `/student/goals` | Goal management |
| `/student/timeline` | Memory timeline (**double-shell fixed**) |
| `/student/onboarding` | Onboarding wizard |

### 2.3 Mentor (`/mentor/*`) — 9 routes

| Route | Notes |
|-------|-------|
| `/mentor/dashboard` | Mentor KPIs |
| `/mentor/queue` | Case queue |
| `/mentor/interventions` | Intervention queue |
| `/mentor/cohort` | Cohort view |
| `/mentor/cases/[id]` | Case detail |
| `/mentor/student/[studentId]` | Student twin + **engine recs** |
| `/mentor/students/[id]/planning` | Student planning |
| `/mentor/students/[id]/forecasting` | Student forecasting |
| `/mentor/students/[id]/interventions` | Student interventions |

### 2.4 Faculty (`/faculty`) — 1 route

| Route | Notes |
|-------|-------|
| `/faculty` | Faculty workspace — linked from mentor nav |

### 2.5 Auth / Public — 4 routes

| Route | Purpose |
|-------|---------|
| `/` | Auth redirect hub |
| `/login` | Login |
| `/register` | Registration |
| `/unauthorized` | Permission denied |

---

## 3. Backend API Inventory (182 endpoints)

See `backend/src/prepos/api/v1/router.py` and sub-routers. Summary by domain:

| Domain | Endpoints | Primary frontend client |
|--------|----------:|------------------------|
| Health (root) | 5 | Direct fetch (`/health/*`) |
| Auth | 5 | `authApi` |
| Exams / Syllabus / Concepts | 10 | `catalogApi` |
| Students | 4 | `studentApi` |
| Learning graph | 11 | `studentApi` |
| Study plan | 3 | `studentApi` |
| Goals | 3 | `studentApi` |
| Mentor | 6 | `mentorApi` |
| Twin (legacy) | 5 | `studentApi` (dashboard/twin still used) |
| Copilot | 2 | `copilotApi` |
| Faculty | 1 | `facultyApi` |
| **Recommendations engine** | 7 | **`recommendationsApi`** |
| Memory | 5 | `studentTimelineApi`, memory hooks |
| Planning | 8 | `studentApi`, planning hooks |
| Forecasting | 8 | forecasting hooks |
| Interventions | 7 | intervention hooks |
| Cohort | 5 | cohort hooks |
| Knowledge | 5 | `adminKnowledgeApi`, knowledge search |
| Current affairs | 6 | `adminCurrentAffairsApi` |
| PYQ | 8 | `adminPyqApi` |
| Admin dashboards | ~80 | Various `admin*Api` |
| Platform maturity (P11) | 20 | `adminPlatformApi`, `adminSecurityApi` |
| AgentOps | 12 | `adminAgent*Api`, `adminApprovalsApi` |

---

## 4. API Integration Matrix (summary)

Full per-route matrix: see [`API_COVERAGE_REPORT.md`](./API_COVERAGE_REPORT.md).

| Status | Count | Description |
|--------|------:|-------------|
| ✅ Wired + UI | ~138 | Client + hook/page exists |
| ⚠️ Client only | ~24 | API client exists; admin/ops POST actions not exposed in UI |
| ❌ Missing client | ~20 | Seed/import, search POST variants, agent benchmarks |

**Critical integrations fixed in this pass:**

- Recommendation engine → student, mentor, forecast pages
- Security sub-routes → dedicated admin pages
- P11 platform routes → dedicated admin pages
- Agent approvals → approve/reject actions
- Agent evaluation → admin page

---

## 5. Navigation Graph

### 5.1 Entry points (post-fix)

| Role | Login redirect | Primary shell |
|------|----------------|---------------|
| `student` | `/student/dashboard` | StudentShell |
| `faculty` | `/mentor/dashboard` | MentorShell |
| `institute_admin` / `super_admin` | **`/admin`** | AdminShell |

### 5.2 Previously orphaned pages (now linked)

| Page | Fix |
|------|-----|
| `/admin/platform-readiness` | Admin sidebar → Platform section |
| `/faculty` | Mentor nav → "Faculty workspace" |
| `/admin/security/*` sub-pages | Security section + pages created |
| P11 dashboards | Platform section in admin sidebar |

### 5.3 Duplicate navigation paths (accepted legacy)

| Feature | Modern path | Legacy path |
|---------|-------------|-------------|
| Forecasting | `/student/forecasting` | `/student/forecast` (twin) |
| Planning | `/student/planning` | `/student/study-plan` |

Both remain reachable; consolidation deferred (no new features rule).

### 5.4 Broken links fixed

| Link | Status |
|------|--------|
| `/admin/security/tenant-audit` | ✅ Page created |
| `/admin/security/knowledge` | ✅ Page created |
| `/admin/security/rate-limits` | ✅ Page created |

### 5.5 Server-side route protection

`apps/web/middleware.ts` enforces role prefixes:

- `/student/*` → `student`
- `/mentor/*`, `/faculty/*` → `faculty`, `institute_admin`, `super_admin`
- `/admin/*` → `institute_admin`, `super_admin`

Session cookies (`prepos-roles`, `prepos-authed`) synced on login via `session-cookie.ts`.

---

## 6. Files Changed in Readiness Pass (by phase)

### Phase 2 — Critical
- `apps/web/middleware.ts`
- `apps/web/src/lib/auth/session-cookie.ts`
- `apps/web/src/providers/auth-provider.tsx`
- `apps/web/src/app/student/timeline/page.tsx`
- `apps/web/src/components/ui/worker-status-banner.tsx`
- `apps/web/src/app/admin/security/{tenant-audit,knowledge,rate-limits}/page.tsx`

### Phase 3 — Admin rebuild
- `apps/web/src/app/admin/layout.tsx`
- `apps/web/src/app/admin/page.tsx`
- `apps/web/src/components/layout/admin-nav.tsx`
- `apps/web/src/components/ui/breadcrumbs.tsx`
- `apps/web/src/lib/auth/roles.ts`

### Phase 4–7 — API wiring & pages
- `apps/web/src/lib/api/index.ts` (`recommendationsApi`, approvals approve/reject, agent evaluation)
- `apps/web/src/lib/types/api.ts` (recommendation engine types)
- `apps/web/src/hooks/use-student-queries.ts`
- P11 + agent evaluation admin pages (9 new)
- `apps/web/src/app/admin/approvals/page.tsx`
- Student/mentor recommendation consumers updated

### Phase 8–10 — UX / responsiveness
- `QueryBoundary` on timeline, faculty, security, P11 pages
- `WorkerStatusBanner` in student, mentor, faculty, admin layouts
- Table captions + ARIA on approvals
- Admin responsive sidebar with mobile menu

### Phase 11 — E2E
- `apps/web/e2e/tests/admin.spec.ts`
- `apps/web/e2e/tests/faculty.spec.ts`

---

## 7. Known Remaining Gaps

1. **Admin POST mutations** — forecast-accuracy record, DR verify, evaluation label: client stubs exist; UI forms not added (read-only dashboards prioritized).
2. **Agent benchmarks** — `/admin/agent-benchmarks` backend exists; no dedicated page (health page partially covers).
3. **Syllabus seed/import, exam CRUD** — admin-only backend; no UI (intentionally out of scope).
4. **Cookie session** — middleware uses role cookies synced client-side; not httpOnly JWT (API still enforces auth).

---

*This document is the Phase 1 deliverable. Updated after production-readiness implementation pass.*
