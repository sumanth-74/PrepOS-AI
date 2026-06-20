# Frontend Completion Audit — Sprint P1.0

**Scope:** `apps/web` (Next.js 15 App Router)  
**Generated:** 2026-06-20  
**Routes audited:** 14 pages, 3 layouts, shared auth/API/shell components

---

## Executive Summary

The web app delivers a **read-heavy student and mentor portal** with login, role guards, TanStack Query data fetching, and mutation support on goals, study plan, and mentor cases. It is **not pilot-complete** as a self-service product: registration, onboarding, activity submission, concept labeling, token refresh, and admin surfaces are missing. Several write flows lack user-visible error handling.

**Overall frontend completion estimate:** ~55% of pilot-required UX

---

## Route Audit

### `/` — Root redirect

| Field | Assessment |
|-------|------------|
| **Purpose** | Auth gate; redirect to role default portal or `/login` |
| **APIs** | `GET /auth/me` (via `AuthProvider`) |
| **Missing functionality** | Deep-link preservation; marketing/landing page |
| **Missing validations** | — |
| **Loading states** | ✅ `LoadingState` during auth bootstrap |
| **Error states** | ❌ Silent failure if `/auth/me` errors (user stuck loading) |
| **Mobile** | ✅ Centered loader |
| **Accessibility** | ❌ Loader lacks `role="status"` / `aria-live` |

---

### `/login` — Sign in

| Field | Assessment |
|-------|------------|
| **Purpose** | Tenant + email + password login |
| **APIs** | `POST /auth/login`, `GET /auth/me` |
| **Missing functionality** | Registration, password reset, institute discovery |
| **Missing validations** | ⚠️ Password min-length not enforced client-side (backend: ≥8 register, ≥1 login) |
| **Loading states** | ✅ Session check + submit pending |
| **Error states** | ✅ Form-level login error |
| **Mobile** | ✅ Responsive card |
| **Accessibility** | ⚠️ Errors not linked via `aria-describedby`; missing `autoComplete` on password |

---

### `/unauthorized` — Access denied

| Field | Assessment |
|-------|------------|
| **Purpose** | Wrong-role access message |
| **APIs** | None |
| **Missing functionality** | Link to correct portal for dual-role users |
| **Loading/error** | N/A |
| **Mobile** | ✅ |
| **Accessibility** | ✅ Uses `PageHeader` h1 |

---

### `/student/dashboard` — Twin overview

| Field | Assessment |
|-------|------------|
| **Purpose** | KPI snapshot: readiness, forecast, plan, mentor, intervention |
| **APIs** | `GET /twin/dashboard` |
| **Missing functionality** | Many dashboard fields unused; no onboarding gate; drivers not linked to concepts |
| **Loading/error** | ✅ `QueryBoundary` |
| **Mobile** | ✅ Responsive KPI grid |
| **Accessibility** | ⚠️ KPI cards not semantic `<dl>`; color-only status badges |

---

### `/student/learning-graph` — Concept progress

| Field | Assessment |
|-------|------------|
| **Purpose** | Readiness breakdown, concept nodes, twin drivers |
| **APIs** | `GET /learning-graph/readiness`, `GET /learning-graph`, `GET /twin/dashboard` |
| **Missing functionality** | Concept detail, weaknesses API (wired but unused), activity recording, pagination beyond 50 nodes, syllabus tree |
| **Loading/error** | ✅ Per-section `QueryBoundary` (partial page load) |
| **Mobile** | ⚠️ Multiple sequential loading blocks |
| **Accessibility** | ❌ Raw concept IDs as headings; no table semantics for metrics |

---

### `/student/recommendations` — Twin recommendations

| Field | Assessment |
|-------|------------|
| **Purpose** | Prioritized study actions |
| **APIs** | `GET /twin/recommendations` |
| **Missing functionality** | Action CTAs, filters, link to concept detail |
| **Loading/error** | ✅ |
| **Mobile** | ✅ Card stack |
| **Accessibility** | ⚠️ Priority conveyed partly by color |

---

### `/student/revision-queue` — Revision queue

| Field | Assessment |
|-------|------------|
| **Purpose** | Tabular revision queue projection |
| **APIs** | `GET /learning-graph/revisions/queue` |
| **Missing functionality** | Complete revision action (`POST /learning-graph/activities/revision`); concept labels |
| **Loading/error** | ✅ |
| **Mobile** | ⚠️ Horizontal scroll table |
| **Accessibility** | ❌ Table lacks `scope`, caption; raw concept IDs |

---

### `/student/study-plan` — Study plan execution

| Field | Assessment |
|-------|------------|
| **Purpose** | Daily/weekly plan; complete/skip daily items |
| **APIs** | `GET /study-plan`, `POST /study-plan/items/complete`, `POST /study-plan/items/skip` |
| **Missing functionality** | Weekly item actions; `actual_minutes` on complete; onboarding redirect when empty |
| **Missing validations** | — |
| **Loading states** | ✅ Query load; ⚠️ global `busy` disables all buttons during one mutation |
| **Error states** | ❌ Mutation failures silent (optimistic rollback only) |
| **Mobile** | ✅ |
| **Accessibility** | ❌ No `aria-busy`; no skip confirmation |

---

### `/student/goals` — Goal management

| Field | Assessment |
|-------|------------|
| **Purpose** | Create/update goal; show trajectory and milestones |
| **APIs** | `GET /goals`, `POST /goals`, `PUT /goals` |
| **Missing functionality** | Exam picker (`GET /exams`); profile goal fields (`PATCH /students/{id}`) |
| **Missing validations** | ⚠️ No future-date check on `target_date`; `daily_capacity_minutes` error not shown |
| **Loading/error** | ✅ Manual loading/error states |
| **Mobile** | ✅ |
| **Accessibility** | ⚠️ Field errors not `aria-describedby` |

---

### `/student/forecast` — Forecast & scenarios

| Field | Assessment |
|-------|------------|
| **Purpose** | Forecast KPIs, scenarios, recommendations |
| **APIs** | `GET /twin/dashboard`, `GET /twin`, `GET /twin/recommendations` |
| **Missing functionality** | Structured scenario UI; twin JSON shown in `<pre>` blocks |
| **Loading/error** | ✅ |
| **Mobile** | ⚠️ JSON dumps scroll poorly |
| **Accessibility** | ❌ `<pre>` JSON not screen-reader friendly |

---

### `/mentor/dashboard` — Mentor workspace

| Field | Assessment |
|-------|------------|
| **Purpose** | Case counts, effectiveness, best action |
| **APIs** | `GET /mentor/dashboard` |
| **Missing functionality** | Drill-down links to filtered queue; case list page |
| **Loading/error** | ✅ |
| **Mobile** | ✅ |
| **Accessibility** | ⚠️ KPI grouping not semantic |

---

### `/mentor/queue` — Mentor queue

| Field | Assessment |
|-------|------------|
| **Purpose** | Prioritized student/case table |
| **APIs** | `GET /mentor/queue` |
| **Missing functionality** | Student names (`GET /students/{id}`); filters |
| **Loading/error** | ✅ |
| **Mobile** | ⚠️ Wide table horizontal scroll |
| **Accessibility** | ❌ UUIDs as link text |

---

### `/mentor/cases/[id]` — Case management

| Field | Assessment |
|-------|------------|
| **Purpose** | Case detail, notes, resolve |
| **APIs** | `GET /mentor/cases/{id}`, `POST .../notes`, `POST .../resolve` |
| **Missing functionality** | Resolution reason must be enum; UI uses free-text → **400 on invalid values** |
| **Missing validations** | ❌ No enum select for `CaseResolutionReason` |
| **Loading states** | ✅ Page + mutation pending |
| **Error states** | ❌ Mutation errors not surfaced |
| **Mobile** | ✅ |
| **Accessibility** | ❌ Textareas missing proper labels |

---

### `/mentor/student/[studentId]` — Student twin (mentor view)

| Field | Assessment |
|-------|------------|
| **Purpose** | Read-only twin for queued student |
| **APIs** | `GET /twin/dashboard`, `GET /twin`, `GET /twin/recommendations` (with `student_id`) |
| **Missing functionality** | Learning graph, study plan, goals, student profile header, case link |
| **Loading/error** | ✅ |
| **Mobile** | ✅ |
| **Accessibility** | ❌ JSON `<pre>` blocks |

---

## Cross-Cutting Gaps

### Auth & session

| Gap | Severity |
|-----|----------|
| No registration UI | P0 |
| No token refresh (`POST /auth/refresh`) | P0 |
| No 401 interceptor in API client | P0 |
| Client-only route guards (no Next.js middleware) | P1 |
| Dual-role users always routed to mentor portal | P1 |
| Logout does not send refresh token body | P2 |

### Onboarding & profile

| Gap | Severity |
|-----|----------|
| No onboarding wizard | P0 |
| `onboarding_completed` never checked in student layout | P0 |
| `PATCH /students/{id}` not exposed | P0 |
| `POST /students/onboarding/complete` not called from UI | P0 |

### Concept labels

| Gap | Severity |
|-----|----------|
| Raw `concept_id` displayed everywhere | P1 |
| `GET /concepts/{id}` and syllabus tree unused | P1 |

### Navigation & shell

| Gap | Severity |
|-----|----------|
| No active nav highlighting (`aria-current`) | P2 |
| Mobile sidebar not a drawer overlay | P2 |
| Mentor nav missing case/student routes | P2 |

### Backend API coverage (frontend client)

**Implemented:** auth (login/me/logout), student twin/LG/study-plan/goals, mentor dashboard/queue/cases

**Not implemented in client:** register, refresh, student update/onboarding, LG activities, concept search, syllabus, exams list, mentor case list, twin metrics

---

## Build Status (P1.0 verification)

| Check | Result |
|-------|--------|
| `npm run typecheck` | PASS |
| `npm run lint` | PASS |
| `npm run build` | PASS (15 routes) |

---

## Priority Fix List (no new engines)

1. Registration + onboarding flow with layout gate  
2. Token refresh + 401 handling in `apiRequest`  
3. Concept label resolver (batch `/concepts/{id}` or syllabus cache)  
4. Mentor resolve enum select + mutation error toasts  
5. Study/revision activity forms on revision queue + learning graph  
6. Active nav + mobile drawer polish  
7. Next.js middleware for auth redirect  
