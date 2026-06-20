# Sprint P1.1A — Student Self-Service Completion

**Date:** 2026-06-18  
**Scope:** Frontend product completion only (no backend domain logic, engines, or scoring changes)

---

## Summary

Sprint P1.1A closes the highest-impact student self-service gaps identified in P1.0: registration, onboarding wizard, activity logging, and core UX polish. All frontend validation passes.

**Estimated MVP readiness impact:** 66/100 → **~76/100** (product completion for pilot demo paths; scale and ops gaps remain from P1.0).

---

## Screens Implemented

| Screen | Route | Description |
|--------|-------|-------------|
| Institute registration | `/register` | RHF + Zod form; creates tenant + institute admin via API |
| Sign in (enhanced) | `/login` | Pre-fills tenant/email after registration; link to register |
| Student onboarding wizard | `/student/onboarding` | 5-step flow with progress pills: exam → year → hours → level → review |
| Log activity | `/student/activities` | Four forms: study session, revision, assessment, PYQ update |
| Student error boundary | `/student/*` (error.tsx) | Page-level retry + dashboard fallback |

**Enhanced existing screens:**

- Dashboard — KPI skeleton loading, empty state with CTA to log activity
- Revision queue — empty state with CTA to log revision
- All student shell pages — active sidebar navigation

---

## Routes Added

| Route | File |
|-------|------|
| `/register` | `apps/web/src/app/register/page.tsx` |
| `/student/onboarding` | `apps/web/src/app/student/onboarding/page.tsx` |
| `/student/activities` | `apps/web/src/app/student/activities/page.tsx` |

**Layout / navigation:**

- `apps/web/src/app/student/layout.tsx` — onboarding bypasses shell + guard; other routes use `OnboardingGuard` + `StudentShell`
- `apps/web/src/components/layout/student-nav.tsx` — added **Log Activity** nav item
- `apps/web/src/app/student/error.tsx` — route-level error boundary

---

## API Integrations Completed

| Feature | Method | Endpoint | Client |
|---------|--------|----------|--------|
| Registration | POST | `/auth/register` | `authApi.register` |
| Exam catalog | GET | `/exams` | `catalogApi.listExams` |
| Profile update (onboarding steps) | PATCH | `/students/{id}` | `studentApi.updateProfile` |
| Complete onboarding | POST | `/students/onboarding/complete` | `studentApi.completeOnboarding` |
| Study session | POST | `/learning-graph/activities/study-session` | `studentApi.submitStudySession` |
| Revision | POST | `/learning-graph/activities/revision` | `studentApi.submitRevision` |
| Assessment | POST | `/learning-graph/activities/assessment` | `studentApi.submitAssessment` |
| PYQ update | POST | `/learning-graph/activities/pyq-change` | `studentApi.submitPyqChange` |

**Post-submission behavior:**

- `invalidateStudentData()` refreshes profile, twin, learning-graph, study-plan, and goals queries after onboarding completion and all activity submissions.

**Request shapes (aligned to existing backend DTOs):**

- Study session: `{ concept_id, exam_id, engaged_minutes }`
- Revision: `{ concept_id, exam_id, recall_grade }`
- Assessment: `{ concept_id, exam_id, mcq_correct, self_confidence? }`
- PYQ: `{ concept_id, exam_id, global_importance }`

`exam_id` is injected from student profile context in `useActivityMutations`.

---

## UX Improvements

| Area | Implementation |
|------|----------------|
| Active sidebar nav | `usePathname()` + `aria-current="page"` in `app-shell.tsx` |
| Empty states | `QueryBoundary` `emptyAction` on dashboard, revision queue, activities |
| Loading skeletons | `LoadingSkeleton`, `KpiSkeletonGrid`; optional `loadingFallback` on `QueryBoundary` |
| Error boundaries | `apps/web/src/app/student/error.tsx` |
| Onboarding redirect | `OnboardingGuard` sends incomplete profiles to `/student/onboarding` |
| Loading a11y | `role="status"` / `aria-live="polite"` on loading components |

---

## Validation Results

```text
npm run typecheck   PASS
npm run lint        PASS (0 errors; unused-import warnings fixed)
npm run build       PASS — 18 routes compiled
```

---

## Remaining Gaps

| Gap | Severity | Notes |
|-----|----------|-------|
| Concept labels in activity picker | Medium | Shows truncated UUID; syllabus concept names not exposed on learning-graph overview API |
| Activity projection latency | Medium | 202 responses require Celery worker (or dev outbox drain) before dashboard/twin update |
| Student self-registration | Low | `/register` creates **institute admin**, not student accounts; students still need institute provisioning |
| Token refresh | Medium | Unchanged from P1.0 — long sessions may expire without silent refresh |
| Mobile polish | Low | Sidebar toggle works; no dedicated mobile nav patterns |
| E2E browser tests | Medium | No Playwright/Cypress coverage for new flows |
| Mentor portal | N/A | Out of P1.1A scope |

---

## Files Touched (Key)

**New**

- `apps/web/src/app/register/page.tsx`
- `apps/web/src/app/student/onboarding/page.tsx`
- `apps/web/src/app/student/activities/page.tsx`
- `apps/web/src/app/student/error.tsx`
- `apps/web/src/components/auth/register-form.tsx`
- `apps/web/src/components/auth/onboarding-guard.tsx`
- `apps/web/src/components/student/onboarding-wizard.tsx`
- `apps/web/src/components/student/activity-forms.tsx`
- `apps/web/src/hooks/use-onboarding.ts`
- `apps/web/src/hooks/use-activity-mutations.ts`
- `apps/web/src/lib/query/invalidate-student-data.ts`
- `apps/web/src/components/ui/loading-skeleton.tsx`

**Modified**

- `apps/web/src/lib/types/api.ts` — register, onboarding, activity types
- `apps/web/src/lib/api/index.ts` — API client methods
- `apps/web/src/stores/index.ts` — `setTenantSlug`
- `apps/web/src/app/student/layout.tsx`
- `apps/web/src/components/layout/app-shell.tsx`
- `apps/web/src/components/layout/student-nav.tsx`
- `apps/web/src/components/auth/login-form.tsx`
- `apps/web/src/components/ui/query-boundary.tsx`
- `apps/web/src/components/ui/loading-state.tsx`
- `apps/web/src/app/student/dashboard/page.tsx`
- `apps/web/src/app/student/revision-queue/page.tsx`
- `apps/web/src/app/login/page.tsx`

---

## Demo Path (Post-P1.1A)

1. **Institute admin:** `/register` → `/login?registered=1`
2. **Student:** `/login` with demo credentials (`prepos-demo` / `student@prepos-demo.example.com`)
3. If onboarding incomplete → `/student/onboarding` (5 steps)
4. **Log activity:** `/student/activities` → submit study/revision/assessment/PYQ
5. **Verify:** `/student/dashboard` refreshes after worker processes outbox events

**No backend changes were made in this sprint.**
