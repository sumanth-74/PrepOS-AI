# Sprint P1.1B — Pilot Hardening & UX Completion

**Date:** 2026-06-18  
**Scope:** Frontend hardening only (no backend domain logic, engines, event chains, or scoring changes)

---

## Summary

Sprint P1.1B closes pilot-critical UX and reliability gaps: silent session expiry, raw UUID display, sparse mentor workflows, and missing mutation feedback. Estimated pilot readiness: **~76/100 → ~84/100**.

---

## Screens Improved

| Area | Screen / Route | Improvements |
|------|----------------|--------------|
| **Auth** | All authenticated routes | Automatic token refresh on 401; proactive refresh before expiry; logout revokes refresh token |
| **Student** | Learning graph | Concept names + syllabus path via `ConceptLabel` |
| **Student** | Revision queue | Concept names + path in table |
| **Student** | Recommendations | Concept names + path |
| **Student** | Study plan | Concept names + path on daily/weekly items |
| **Student** | Activities | Concept dropdown shows `name · subject › topic` |
| **Student** | Forecast | Top actions show concept names |
| **Student** | Goals, activities, study plan, onboarding | Success/error toasts on mutations |
| **Mentor** | Queue | Student label (exam-based) + exam subtitle; priority badges; escalation tones |
| **Mentor** | Case detail | Resolution enum dropdown; optimistic notes; toasts; short refs instead of UUIDs |
| **Mentor** | Dashboard | KPI skeleton loading; empty state copy |
| **Mentor** | Student twin | Student display name; concept labels in recommendations |
| **Global** | All routes | Toast provider; React error boundary; enhanced global error page |

---

## APIs Integrated

| Feature | Method | Endpoint | Client |
|---------|--------|----------|--------|
| Token refresh | POST | `/auth/refresh` | `authApi.refresh` |
| Logout (refresh revoke) | POST | `/auth/logout` | `authApi.logout` (body: `refresh_token`) |
| Syllabus tree (concept cache) | GET | `/syllabus/{exam_id}/tree` | `catalogApi.getExamTree` |
| Concept ancestors (fallback) | GET | `/concepts/{id}/ancestors` | `catalogApi.getConceptAncestors` |
| Student profile (mentor lookup) | GET | `/students/{id}` | `studentApi.getProfile` |
| Exam catalog (mentor labels) | GET | `/exams` | `catalogApi.listExams` (reused) |

Existing activity, onboarding, goals, study-plan, and mentor mutation endpoints unchanged — now with refresh-aware client and toast feedback.

---

## 1. Token Refresh Flow

**Implementation**

- `lib/api/token-refresh.ts` — single-flight refresh coordinator, proactive scheduling
- `lib/api/client.ts` — 401 interceptor: refresh → retry once; `X-Request-ID` on every request
- `stores/index.ts` — persists `tokenExpiresAt` from `expires_in`
- `providers/auth-provider.tsx` — refresh before clearing session on bootstrap 401; schedules proactive refresh on login

**Behavior**

1. Access token expires → next API call returns 401
2. Client calls `POST /auth/refresh` with stored refresh token
3. New token pair persisted; original request retried
4. Refresh failure → store cleared (user redirected on next auth check / logout)
5. Proactive refresh ~60s before expiry when `expires_in` is known

**Manual validation**

1. Sign in as demo student
2. In DevTools → Application → Local Storage → `prepos-auth`, set `accessToken` to an invalid value (keep `refreshToken`)
3. Navigate or refetch dashboard — session should recover without redirect to login
4. Invalidate both tokens — user should be logged out on next request

---

## 2. Concept Label Resolution

**New modules**

- `hooks/use-concept-lookup.ts` — TanStack Query cache for syllabus tree + per-concept ancestor fallback
- `components/ui/concept-label.tsx` — reusable label with optional path

**Coverage**

- Learning graph, revision queue, recommendations, study plan, activities, forecast, mentor student recommendations

**Cache strategy**

- Primary: `GET /syllabus/{exam_id}/tree` → in-memory map (1h stale time)
- Fallback: `GET /concepts/{id}/ancestors` for nodes missing from tree

---

## 3. Mentor UX Completion

| Item | Status |
|------|--------|
| Queue: student label | ✅ Exam-based display via profile + catalog (no legal name in API) |
| Queue: exam name | ✅ Subtitle from student `target_exam` |
| Queue: priority badges | ✅ `PriorityBadge` (Critical/High/Medium/Low + score) |
| Case: resolution enum | ✅ Dropdown aligned to `CaseResolutionReason` |
| Case: note toasts | ✅ Success/error |
| Case: optimistic notes | ✅ Immediate UI update, rollback on error |
| Dashboard: skeletons | ✅ `KpiSkeletonGrid` |
| Dashboard: empty state | ✅ Descriptive copy |

---

## 4. Mutation UX (Toasts)

| Mutation | Toast |
|----------|-------|
| Onboarding complete | Success / error |
| Onboarding step save | Error only |
| Activity submissions (×4) | Success / error |
| Goal create/update | Success / error |
| Study plan complete/skip | Success / error |
| Mentor note | Success / error |
| Mentor resolve | Success / error |

**Implementation:** `stores/toast-store.ts`, `lib/toast.ts`, `components/ui/toast-provider.tsx`

---

## 5. Frontend Observability

| Capability | Location |
|------------|----------|
| Request ID logging | `lib/observability/request-id.ts` → `X-Request-ID` header + structured console logs |
| Global error boundary | `components/error-boundary.tsx` → wraps app in root layout |
| Next.js error UI | `app/error.tsx` → captures to observability hook |
| React Query monitoring | `lib/observability/query-monitor.ts` → query/mutation cache error subscription |
| Sentry hooks (disabled) | `lib/observability/sentry.ts` — active when `NEXT_PUBLIC_SENTRY_ENABLED=true` and `NEXT_PUBLIC_SENTRY_DSN` set |

---

## Validation Results

```text
npm run typecheck   PASS
npm run lint        PASS
npm run build       PASS — 18 routes compiled
```

---

## Remaining Pilot Blockers

| Blocker | Severity | Notes |
|---------|----------|-------|
| Student legal name in mentor queue | Medium | Backend queue DTO has no `full_name`; UI uses exam-based label + short ref |
| Activity projection latency | Medium | 202 + Celery/outbox still required for twin refresh |
| No automated E2E for refresh flow | Medium | Manual DevTools steps documented above |
| Sentry package not installed | Low | Hooks ready; add `@sentry/nextjs` when DSN available |
| Docker frontend still placeholder | Medium | From P1.0 — deploy real Next.js build separately |
| Scale / ops gaps from P1.0 | Medium | Unchanged (1000-user target, observability backend) |

---

## Key Files Added

- `src/lib/api/token-refresh.ts`
- `src/lib/observability/request-id.ts`
- `src/lib/observability/sentry.ts`
- `src/lib/observability/query-monitor.ts`
- `src/lib/toast.ts`
- `src/stores/toast-store.ts`
- `src/hooks/use-concept-lookup.ts`
- `src/hooks/use-exam-lookup.ts`
- `src/hooks/use-student-lookup.ts`
- `src/components/ui/concept-label.tsx`
- `src/components/ui/toast-provider.tsx`
- `src/components/error-boundary.tsx`
- `src/components/mentor/priority-badge.tsx`
- `src/components/mentor/queue-table.tsx`

---

## Environment Variables (Observability)

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_SENTRY_DSN` | Sentry DSN (optional) |
| `NEXT_PUBLIC_SENTRY_ENABLED` | Set to `true` to enable capture hooks |

**No backend changes were made in this sprint.**
