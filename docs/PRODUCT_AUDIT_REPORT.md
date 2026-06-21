# PrepOS AI — Complete Product Audit Report

**Audit date:** 2026-06-18  
**Scope:** Feature-complete platform through P11 (no new features; read-only audit)  
**Auditors (roles):** Senior QA Architect · Staff Frontend Engineer · Backend Lead · Product Owner · Solutions Architect  
**Method:** Route inventory, API ↔ UI cross-reference, navigation crawl, component state review, module data-flow trace, severity classification  

---

## Executive summary

PrepOS has a **mature backend** (~166 API routes) and a **broad admin dashboard layer** (27 admin pages). Student and mentor portals are **largely functional** for core learning flows (Twin read, Learning Graph, Planning, Forecasting, Copilot). However, the product exhibits **integration debt**, **discoverability gaps**, and **P11 UI incompleteness** that affect production readiness for non-technical users.

| Severity | Count | Theme |
|----------|-------|-------|
| **Critical** | 4 | Broken navigation (404), auth guard gaps, split legacy/modern paths confusing users |
| **High** | 12 | Recommendation Engine not wired to UI; admin discoverability; missing error states; P11 pages absent |
| **Medium** | 18 | Partial modules, API-only features, accessibility gaps |
| **Low** | 14 | Unused API client stubs, polish, orphan routes |

**Overall verdict:** Backend **Production-ready** · Frontend **Pilot-ready with known gaps** · End-to-end product **Partially production-ready**

---

## 1. Route inventory

**Total frontend routes:** 50 (`apps/web/src/app/**/page.tsx`)  
**Auth model:** Client-side `RoleGuard` only (no Next.js middleware)

### 1.1 Public routes

| Route | Persona | Status | Notes |
|-------|---------|--------|-------|
| `/` | All | ✅ Functional | Redirects by role |
| `/login` | All | ✅ Functional | |
| `/register` | All | ✅ Functional | Creates tenant + institute admin |
| `/unauthorized` | All | ✅ Functional | Role mismatch fallback |

### 1.2 Student portal (`RoleGuard: student`)

| Route | Status | Notes |
|-------|--------|-------|
| `/student/dashboard` | ✅ Functional | Twin KPIs via QueryBoundary |
| `/student/activities` | ✅ Functional | All 4 LG activity POST types |
| `/student/learning-graph` | ✅ Functional | Concept labels; 50-node limit |
| `/student/recommendations` | ⚠️ Partial | Read-only; uses legacy `/twin/recommendations`, no CTAs |
| `/student/revision-queue` | ⚠️ Partial | Read-only; no inline complete action |
| `/student/study-plan` | ⚠️ Partial | Legacy study plan; mutation errors may be silent |
| `/student/planning` | ✅ Functional | Adaptive planning (generate/complete/explain) |
| `/student/forecasting` | ✅ Functional | Structured scenarios |
| `/student/goals` | ✅ Functional | |
| `/student/forecast` | ⚠️ Partial | Raw JSON dump for twin simulations (legacy) |
| `/student/timeline` | ⚠️ Partial | Works but no QueryBoundary; **double StudentShell** (layout + page) |
| `/student/onboarding` | ✅ Functional | Bypasses main shell (by design) |

### 1.3 Mentor portal (`RoleGuard: faculty, institute_admin, super_admin`)

| Route | Status | Notes |
|-------|--------|-------|
| `/mentor/dashboard` | ✅ Functional | Default landing for admin roles too |
| `/mentor/queue` | ✅ Functional | Empty without seed data |
| `/mentor/interventions` | ✅ Functional | Generate/execute/complete wired |
| `/mentor/cohort` | ✅ Functional | |
| `/mentor/student/[studentId]` | ⚠️ Partial | Twin view; some debug-style JSON blocks |
| `/mentor/cases/[id]` | ✅ Functional | Resolution uses enum select (fixed from P1 audit) |
| `/mentor/students/[id]/planning` | ✅ Functional | |
| `/mentor/students/[id]/forecasting` | ✅ Functional | |
| `/mentor/students/[id]/interventions` | ✅ Functional | |

### 1.4 Faculty workspace

| Route | Persona | Status | Notes |
|-------|---------|--------|-------|
| `/faculty` | faculty, institute_admin | ⚠️ Partial | API wired; raw JSON cohort display; **not in any nav** — orphan route |

### 1.5 Admin portal (`RoleGuard: institute_admin, super_admin`)

| Route | Status | Notes |
|-------|--------|-------|
| `/admin/health` | ✅ Functional | Uses public `/health/ops` |
| `/admin/copilot` | ✅ Functional | |
| `/admin/knowledge` | ✅ Functional | Upload + list |
| `/admin/knowledge/[id]` | ✅ Functional | |
| `/admin/rag-quality` | ✅ Functional | |
| `/admin/pyq` | ✅ Functional | |
| `/admin/current-affairs` | ✅ Functional | |
| `/admin/current-affairs/[id]` | ✅ Functional | |
| `/admin/recommendations` | ⚠️ Partial | Dashboard only; loading text, weak error handling |
| `/admin/recommendation-effectiveness` | ⚠️ Partial | Same pattern |
| `/admin/memory` | ⚠️ Partial | No error branch in dashboard |
| `/admin/planning` | ⚠️ Partial | |
| `/admin/forecasting` | ⚠️ Partial | |
| `/admin/interventions` | ⚠️ Partial | |
| `/admin/cohort` | ⚠️ Partial | |
| `/admin/institution` | ⚠️ Partial | |
| `/admin/institution/outcomes` | ⚠️ Partial | |
| `/admin/agents` | ⚠️ Partial | Marketplace API unused |
| `/admin/agents/health` | ⚠️ Partial | No page-level error state |
| `/admin/agent-traces` | ⚠️ Partial | Clickable rows not keyboard-accessible |
| `/admin/agent-costs` | ⚠️ Partial | No error UI |
| `/admin/approvals` | ⚠️ Partial | List only; approve/reject API not in client |
| `/admin/security` | ⚠️ Partial | Main KPIs work; **links to 3 missing sub-pages (404)** |
| `/admin/platform-readiness` | ⚠️ Partial | Read-only; no recompute button; orphan (no inbound links) |

**Missing routes (linked but 404):**

| Dead link | Linked from |
|-----------|-------------|
| `/admin/security/tenant-audit` | `/admin/security` header |
| `/admin/security/knowledge` | `/admin/security` header |
| `/admin/security/rate-limits` | `/admin/security` header |

**Missing routes (API + client exist, no page):**

| Intended route | Backend API |
|----------------|-------------|
| `/admin/jobs` | `GET /admin/jobs` |
| `/admin/evaluations` | `GET /admin/evaluations` |
| `/admin/forecast-accuracy` | `GET /admin/forecast-accuracy` |
| `/admin/recommendation-validation` | `GET /admin/recommendation-validation` |
| `/admin/monitoring` | `GET /admin/monitoring` |
| `/admin/disaster-recovery` | `GET /admin/disaster-recovery` |
| `/admin/adoption` | `GET /admin/adoption` |
| `/admin/outcomes` | `GET /admin/outcomes` (≠ `/admin/institution/outcomes`) |
| `/admin/agent-evaluation` | `GET /admin/agent-evaluation` |

### 1.6 Persona access matrix (routes)

| Persona | Accessible areas |
|---------|------------------|
| **Student** | `/student/*`, Copilot (student persona) |
| **Faculty** | `/mentor/*`, `/faculty`, Copilot (mentor persona), `/admin/approvals` |
| **Institute Admin** | All mentor routes + all `/admin/*` + Copilot (admin on `/admin/*`) |
| **Super Admin** | Same as institute admin; backend bypasses role checks |

---

## 2. API audit

**Backend routes:** ~166 (v1 + health)  
**Frontend API client wrappers:** ~120 (`apps/web/src/lib/api/index.ts`)  
**Routes without frontend client:** 44  

### 2.1 Endpoints not used by UI (selected)

| Domain | Missing from client / unused | Impact |
|--------|------------------------------|--------|
| **Recommendations engine** | All 7 `/recommendations/*` routes | Engine not reachable from UI except via Copilot/twin |
| **Knowledge Q&A** | `POST /knowledge/search`, `/knowledge/ask` | No direct student knowledge UI (Copilot only) |
| **PYQ / CA search** | `POST /pyq/search`, `/current-affairs/search` | No student browse UI |
| **Memory** | `/memory/student`, `/mentor/{id}`, `/milestones`, rebuild | Timeline uses timeline only; rebuild admin-only with no UI button |
| **Learning Graph** | `/summary`, `/nodes/{id}`, `/revisions/due` | Partial graph coverage |
| **Twin** | `/metrics`, `/snapshot` (deprecated) | Low impact |
| **Mentor** | `GET /mentor/cases` (list) | Queue uses other endpoints |
| **AgentOps** | `/agent-evaluation`, approve/reject, benchmarks | Partial AgentOps surface |
| **P11 write ops** | DR verify, eval label, forecast/rec validation record | Admin record APIs unused |

### 2.2 UI calling APIs that exist ✓

| Module | Client | Backend | Wired in UI |
|--------|--------|---------|-------------|
| Auth | `authApi` | `/auth/*` | ✅ login, register, refresh |
| Twin dashboard | `studentApi.twinDashboard` | `/twin/dashboard` | ✅ |
| Learning Graph | `studentApi.learningGraph` | `/learning-graph` | ✅ |
| Activities | `submitStudySession`, etc. | LG activity POSTs | ✅ |
| Adaptive planning | `studentApi.*Plan*` | `/planning/*` | ✅ |
| Forecasting | `studentApi.*Forecast*` | `/forecasting/*` | ✅ |
| Mentor ops | `mentorApi.*` | `/mentor/*` | ✅ (except case list) |
| Interventions | `mentorApi.*Intervention*` | `/interventions/*` | ✅ mentor; ❌ student history |
| Cohort | `mentorApi.cohort*` | `/cohort/*` | ✅ |
| Copilot | `copilotApi.query` | `/copilot/query` | ✅ |
| Admin dashboards | `admin*Api` | `/admin/*` | ✅ (most read paths) |
| Faculty | `facultyApi.workspace` | `/faculty/workspace` | ✅ `/faculty` |

### 2.3 UI components with missing / incomplete API integration

| UI surface | Gap |
|------------|-----|
| `/student/recommendations` | No `POST /recommendations/student`, complete, or explain |
| `/admin/approvals` | No approve/reject actions in client |
| `/admin/agents` | `marketplace` client fn never called |
| `/admin/platform-readiness` | `computeReadiness` never called |
| `/admin/security` sub-links | Client fns exist (`tenantAudits`, `knowledgeSecurity`, `rateLimits`) but no pages |
| All P11 `adminPlatformApi.*` except readiness | Zero component imports |
| Student intervention history | `studentApi.myInterventionHistory` defined, never used |

---

## 3. Navigation audit

### 3.1 Menus

| Portal | Nav component | Items | Gaps |
|--------|---------------|-------|------|
| **Student** | `student-nav.tsx` | 11 items | Onboarding intentionally omitted |
| **Mentor** | `mentor-nav.tsx` | 4 items | Deep links (student twin, cases) not in nav |
| **Faculty** | None | — | `/faculty` not linked anywhere |
| **Admin** | None | — | Hub-and-spoke via page header links only |

### 3.2 Breadcrumbs

**Status:** ❌ Not implemented platform-wide. No breadcrumb component found. Users rely on browser back and header cross-links.

### 3.3 Cross-links

**Working clusters:**
- Agents: agents ↔ traces ↔ costs ↔ health ↔ approvals ↔ copilot
- Knowledge: knowledge ↔ rag-quality ↔ pyq ↔ current-affairs ↔ health
- Institution: institution ↔ outcomes ↔ cohort ↔ interventions

**Gaps:**
- No links **to** `/admin/platform-readiness` or `/faculty` from anywhere
- Institute admins land on `/mentor/dashboard` with no path to admin home
- Security page links to **3 dead routes**

### 3.4 Dead links (confirmed)

| href | Severity |
|------|----------|
| `/admin/security/tenant-audit` | **Critical** (404) |
| `/admin/security/knowledge` | **Critical** (404) |
| `/admin/security/rate-limits` | **Critical** (404) |

### 3.5 Structural navigation issues

| Issue | Severity |
|-------|----------|
| Admin has no index/home route | **High** |
| `institute_admin` default portal is mentor, not admin | **High** |
| Duplicate nav: Twin Forecast + Goal Forecasting in student nav | **Medium** |
| Duplicate planning: Study Plan + Adaptive Planning | **Medium** |
| Two student URL patterns: `/mentor/student/` vs `/mentor/students/` | **Medium** |

---

## 4. UI audit

### 4.1 Loading states

| Area | Assessment |
|------|------------|
| Student pages (QueryBoundary) | ✅ Strong |
| Mentor pages | ✅ Good |
| Admin dashboards | ⚠️ Mostly plain "Loading…" text without `role="status"` |
| `/student/timeline` | ❌ No loading indicator |
| `/faculty` | ⚠️ Inline "Loading…" only |
| `/admin/platform-readiness` | ⚠️ Shows "—" while loading |

### 4.2 Error states

| Area | Assessment |
|------|------------|
| Student (QueryBoundary) | ✅ Strong |
| Mentor | ✅ Good |
| Admin dashboards | ❌ ~13 dashboards lack explicit error UI; silent zeros on failure |
| `/student/timeline` | ⚠️ Red inline text only |
| `/faculty` | ❌ No error handling |
| Global | ✅ `error.tsx` at app and student level |

**Admin dashboards WITH error handling:** copilot-analytics, ops-health, knowledge-operations, knowledge-source-detail, agent-orchestration (partial)

### 4.3 Empty states

| Area | Assessment |
|------|------------|
| Student pages | ✅ EmptyState + actions on most pages |
| `/student/planning`, `/student/forecasting` | ⚠️ `isEmpty={() => false}` disables empty UI |
| Mentor | ✅ Good |
| Admin | ⚠️ Often empty tables with no EmptyState component |
| `/student/timeline` | ⚠️ Plain text only |

### 4.4 Responsive issues

| Finding | Severity |
|---------|------------|
| AppShell mobile menu (lg: breakpoint) | ✅ Implemented |
| Admin tables use `overflow-x-auto` | ✅ Horizontal scroll on mobile |
| Page padding `p-4 sm:p-6` consistent | ✅ |
| Copilot panel on small screens | ⚠️ Not formally audited; likely usable |
| Faculty workspace two-column grid | ✅ `md:grid-cols-2` |

See `docs/MOBILE_UX_CHECKLIST.md` — checklist exists; Playwright mobile E2E not confirmed.

### 4.5 Accessibility issues

| Finding | Severity |
|---------|------------|
| Shell nav: `aria-label`, `aria-current` | ✅ Good |
| Copilot: dialog roles, live regions | ✅ Good |
| LoadingState: `role="status"` | ✅ Good |
| Menu toggle: no `aria-expanded` / `aria-controls` | **Medium** |
| Admin tables: no captions, scope, or row headers | **Medium** |
| Agent trace clickable `<tr>` without keyboard support | **Medium** |
| Many admin loading/error as unmarked `<p>` | **Low** |
| EmptyState `<h3>` without page `<h1>` hierarchy on some pages | **Low** |

### 4.6 Broken layouts

| Finding | Severity |
|---------|------------|
| `/student/timeline` double `StudentShell` (nested sidebars) | **High** |
| `/faculty` raw JSON in `<pre>` for cohort insights | **Medium** |
| `/student/forecast` raw JSON twin block | **Medium** |
| Mentor student twin debug JSON sections | **Low** |

---

## 5. Feature audit

Legend: ✅ Working · ⚠️ Partial · ❌ Broken · ⬚ Not connected

### 5.1 Twin

| Layer | Status |
|-------|--------|
| UI → API | ⚠️ Partial |
| API → Service | ✅ Working |
| Service → DB | ✅ Working (requires Celery for freshness) |

**Findings:**
- ✅ Dashboard readiness KPIs work end-to-end
- ⚠️ `/student/forecast` shows raw JSON (legacy path)
- ⚠️ Overlaps with Goal Forecasting module in nav
- ⬚ `/twin/metrics` not exposed in frontend client
- ⚠️ Recommendations page uses `/twin/recommendations` not Recommendation Engine

### 5.2 Learning Graph

| Layer | Status |
|-------|--------|
| UI → API | ⚠️ Partial |
| API → Service | ✅ Working |
| Service → DB | ✅ Working |

**Findings:**
- ✅ Overview, readiness, activity ingestion
- ⚠️ Revision queue read-only (no complete on queue page)
- ⬚ `weaknesses` API in client but unused in UI
- ⚠️ Hard 50-node limit in client

### 5.3 Recommendations

| Layer | Status |
|-------|--------|
| UI → API | ⬚ Not connected (engine) |
| Twin rec path | ⚠️ Partial (read-only) |
| API → Service | ✅ Working |
| Admin analytics | ✅ Working |

**Findings:**
- ❌ `/recommendations/student`, complete, explain — **no frontend integration**
- ⚠️ Student page shows twin recs without accept/complete CTAs
- ✅ Admin recommendation + effectiveness dashboards

### 5.4 Planning

| Layer | Status |
|-------|--------|
| Student adaptive | ✅ Working |
| Legacy study plan | ⚠️ Partial |
| Mentor + Admin | ✅ Working |

**Findings:**
- ✅ Full generate → complete → explain on `/student/planning`
- ⚠️ Legacy `/student/study-plan` coexists in nav (confusing)
- ✅ Mentor per-student planning wired

### 5.5 Forecasting

| Layer | Status |
|-------|--------|
| Student | ✅ Working |
| Mentor | ✅ Working |
| Admin | ✅ Working |

**Findings:**
- ✅ `/student/forecasting` structured UI
- ⚠️ Legacy `/student/forecast` still in nav (twin JSON)

### 5.6 Interventions

| Layer | Status |
|-------|--------|
| Mentor | ✅ Working |
| Admin | ✅ Working |
| Student history | ⬚ Not connected |

**Findings:**
- ✅ Generate/execute/complete/explain on mentor views
- ⬚ `myInterventionHistory` API never called — no student UI

### 5.7 Cohorts

| Layer | Status |
|-------|--------|
| Mentor | ✅ Working |
| Admin | ✅ Working |

**Findings:** Full segment/risk/trend/summary chain wired.

### 5.8 Institution Intelligence

| Layer | Status |
|-------|--------|
| Admin institution | ✅ Working |
| Admin outcomes (P7) | ✅ Working |
| P11 `/admin/outcomes` | ⬚ Not connected |

**Findings:**
- ✅ `/admin/institution` and `/admin/institution/outcomes` dashboards
- ⬚ P11 outcome measurement API has client stub, no page

### 5.9 Knowledge

| Layer | Status |
|-------|--------|
| Admin ops | ✅ Working |
| RAG quality | ✅ Working |
| Student browse | ⬚ Not connected |
| Copilot consumption | ✅ Working (backend handlers) |

**Findings:**
- ✅ Upload, index, metrics, source detail
- ⬚ No student knowledge search UI (Copilot-only)
- ✅ P11 knowledge security scan runs on upload (backend)

### 5.10 Current Affairs

| Layer | Status |
|-------|--------|
| Admin ops | ✅ Working |
| Student browse | ⬚ Not connected |
| Copilot | ✅ Working (intents) |

### 5.11 PYQ

| Layer | Status |
|-------|--------|
| Admin ops | ✅ Working |
| Student browse | ⬚ Not connected |
| Activity logging | ✅ Working (`submitPyqChange`) |
| Copilot | ✅ Working |

### 5.12 Copilot

| Layer | Status |
|-------|--------|
| Global launcher | ✅ Working |
| Persona routing | ✅ Working |
| Query API | ✅ Working |
| Rich cards (P11) | ✅ Working |
| Feedback API | ⚠️ Partial (client exists; UI thumbs not confirmed on all surfaces) |
| Agent mode | ⬚ Backend only (`agent_mode` not sent from UI) |
| Admin analytics | ✅ Working |

### 5.13 Agents

| Layer | Status |
|-------|--------|
| Orchestration dashboard | ✅ Working |
| Marketplace | ⬚ API + client exist; UI not connected |
| Orchestrator (agent_mode) | ⬚ Not exposed in UI |

### 5.14 AgentOps

| Layer | Status |
|-------|--------|
| Traces | ✅ Working |
| Costs | ⚠️ Partial (weak error UI) |
| Health leaderboard | ⚠️ Partial |
| Approvals list | ⚠️ Partial (no approve/reject in UI) |
| Agent evaluation | ⬚ Backend only — no page/client |
| Benchmarks | ⬚ Backend only |

---

## 6. Data flow audit

### 6.1 Healthy chains (examples)

```
Student Dashboard
  → studentApi.twinDashboard()
  → GET /twin/dashboard
  → TwinReadService
  → SqlAlchemyTwinRepository
  → preparation_twins + learning_graph projections
  ✅ Complete

Student Adaptive Planning
  → studentApi.generatePlan()
  → POST /planning/generate
  → AdaptivePlanningService
  → PlanningRepository
  → planning tables
  ✅ Complete

Copilot Query
  → copilotApi.query()
  → POST /copilot/query
  → CopilotService (+ PromptSecurityService P11)
  → Intent handlers / AgentOrchestrator
  → Domain services → Repositories
  ✅ Complete (requires OPENAI_API_KEY for RAG paths)

Admin Knowledge Upload
  → adminKnowledgeApi.uploadSource()
  → POST /knowledge/sources
  → KnowledgeIngestionService (+ KnowledgeSecurityService P11)
  → KnowledgeRepository + Celery embed task
  ✅ Complete (requires worker on knowledge queue)
```

### 6.2 Broken or incomplete chains

| Flow | Break point | Severity |
|------|-------------|----------|
| Student Recommendations (engine) | UI calls `/twin/recommendations`; `/recommendations/*` never invoked | **High** |
| Student intervention history | API client exists; no page | **Medium** |
| Admin security sub-pages | UI links → 404; APIs ready | **Critical** |
| P11 platform dashboards | APIs + client stubs; no pages | **High** |
| Agent approvals action | List loads; approve/reject not in client | **High** |
| Twin projection refresh | UI → API OK; async Celery/outbox required | **High** (ops) |
| Knowledge embed after upload | API OK; requires `knowledge` Celery queue | **High** (ops) |
| Agent evaluation dashboard | Backend route; no UI chain | **Medium** |
| Memory rebuild (admin) | POST /memory/rebuild; no admin UI button | **Low** |
| `/admin/outcomes` (P11) vs `/admin/institution/outcomes` (P7) | Naming collision risk; P11 page missing | **Medium** |

### 6.3 Async dependency map

Many read models depend on **Celery worker + outbox**:

```
Activity POST → Outbox → Worker → Learning Graph event → Twin projection
Recommendation generation → Event → Twin refresh
Knowledge upload → embed_source_chunks task → ACTIVE status
```

**If worker not running:** UI shows stale or empty data — not a broken API chain but **operational critical path**.

---

## 7. Severity classification

### Critical (4)

| ID | Finding | Area |
|----|---------|------|
| C-01 | Dead links: `/admin/security/tenant-audit`, `/knowledge`, `/rate-limits` return 404 | Navigation |
| C-02 | `/student/timeline` double StudentShell — broken layout | UI |
| C-03 | Celery worker required for twin/LG/rec freshness; silent failure if down | Data flow |
| C-04 | Client-side-only RBAC — no middleware; URLs guessable | Security posture |

### High (12)

| ID | Finding | Area |
|----|---------|------|
| H-01 | Recommendation Engine API entirely disconnected from student UI | Feature |
| H-02 | Institute admin lands on mentor portal; no admin home/discoverability | Navigation |
| H-03 | 8+ P11 admin APIs have client stubs but zero UI pages | Feature |
| H-04 | Admin approvals: list without approve/reject actions | Feature |
| H-05 | ~13 admin dashboards lack error states (silent failure) | UI |
| H-06 | Legacy vs modern duplicate nav (forecast, planning, recommendations) | UX |
| H-07 | Knowledge Celery queue must run for embeddings | Data flow |
| H-08 | OPENAI_API_KEY required for Copilot RAG; fails opaque without it | Copilot |
| H-09 | Agent evaluation backend with no frontend | AgentOps |
| H-10 | `/faculty` orphan route — no nav entry | Navigation |
| H-11 | `/admin/platform-readiness` orphan — no inbound links | Navigation |
| H-12 | Access token 15-min expiry; refresh may not cover all flows | Auth UX |

### Medium (18)

| ID | Finding | Area |
|----|---------|------|
| M-01 | Revision queue read-only | Learning Graph |
| M-02 | Student intervention history API unused | Interventions |
| M-03 | `/student/forecast` raw JSON legacy page | Twin |
| M-04 | Faculty workspace raw JSON display | UI |
| M-05 | Agent marketplace API unused | Agents |
| M-06 | Platform readiness compute API not wired to UI | P11 |
| M-07 | P11 `/admin/outcomes` vs institution outcomes naming confusion | Product |
| M-08 | Menu button missing aria-expanded | A11y |
| M-09 | Admin tables lack semantic markup | A11y |
| M-10 | Agent trace table rows not keyboard accessible | A11y |
| M-11 | Planning/forecasting empty states disabled | UI |
| M-12 | Two mentor student URL patterns | Navigation |
| M-13 | `weaknesses` API unused | Learning Graph |
| M-14 | Mentor case list API not in client | Mentor |
| M-15 | Knowledge/CA/PYQ search APIs not in student UI | Content |
| M-16 | Copilot agent_mode not exposed in UI | Copilot |
| M-17 | Copilot feedback UI incomplete on message surfaces | Copilot |
| M-18 | No breadcrumbs anywhere | Navigation |

### Low (14)

| ID | Finding | Area |
|----|---------|------|
| L-01 | `/twin/metrics`, `/snapshot` not in client | Twin |
| L-02 | LG `/summary`, `/nodes/{id}`, `/revisions/due` unused | Learning Graph |
| L-03 | Memory rebuild admin API no button | Memory |
| L-04 | Health endpoints not in frontend client (by design) | API |
| L-05 | Syllabus publish/seed super-admin APIs UI-less | Catalog |
| L-06 | Admin loading text without role="status" | A11y |
| L-07 | EmptyState heading hierarchy | A11y |
| L-08 | Mentor twin view debug JSON blocks | UI polish |
| L-09 | 50-node LG hard limit | UX |
| L-10 | P11 write APIs (record forecast accuracy, etc.) admin-only scripts | API |
| L-11 | `/student/timeline` no loading skeleton | UI |
| L-12 | Duplicate RoleGuard on timeline page | Code smell |
| L-13 | DR verify, adoption dashboards — API ready, UI deferred | P11 |
| L-14 | Mobile E2E not in CI for new P11 routes | QA |

---

## 8. Recommended remediation priority (audit-only; no code changes)

| Priority | Action | Addresses |
|----------|--------|-----------|
| P0 | Create missing `/admin/security/*` pages OR remove dead links | C-01 |
| P0 | Fix `/student/timeline` double shell | C-02 |
| P0 | Document worker + OpenAI as hard prerequisites in onboarding | C-03, H-08 |
| P1 | Add admin layout/nav or admin home route | H-02, H-11 |
| P1 | Wire Recommendation Engine to student UI OR document twin-only path | H-01 |
| P1 | Build P11 admin pages for jobs, evaluations, monitoring, adoption | H-03 |
| P1 | Wire approvals approve/reject in UI + API client | H-04 |
| P1 | Add error boundaries to admin dashboards | H-05 |
| P2 | Consolidate legacy/modern nav (forecast, planning) | H-06 |
| P2 | Add `/faculty` to mentor nav | H-10 |
| P2 | Student intervention history page | M-02 |
| P2 | Revision queue inline actions | M-01 |
| P3 | A11y pass on admin tables and mobile menu | M-08, M-09 |
| P3 | Agent evaluation + marketplace UI | M-05, H-09 |

---

## 9. Appendix

### Audit artifacts referenced

- `docs/e2e_journey_report.md` (P1.0 — partially stale)
- `docs/frontend_audit_report.md` (partially stale; many gaps fixed)
- `docs/PRODUCT_EXPERIENCE_GUIDE.md`
- `docs/MOBILE_UX_CHECKLIST.md`
- `apps/web/src/lib/api/index.ts`
- `backend/src/prepos/api/v1/router.py`

### Test baseline at audit time

- Backend unit tests: 587 passing (per prior CI)
- Frontend: typecheck/lint not re-run as part of this audit
- E2E: Playwright exists; P11 routes not confirmed in E2E suite

### Sign-off

This audit documents **current state only**. No code was modified. Findings should be triaged into a remediation backlog by product and engineering leads.

---

*End of report*
