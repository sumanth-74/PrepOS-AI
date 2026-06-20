# End-to-End User Journey Validation — Sprint P1.0

**Generated:** 2026-06-20  
**Evidence base:** Sprint I1.2 validation (`docs/I1_2_E2E_VALIDATION_REPORT.md`), API integration tests, manual UI gap analysis  
**Demo tenant:** `prepos-demo` (see `backend/scripts/seed_demo_data.py`)

---

## Validation Legend

| Status | Meaning |
|--------|---------|
| ✅ **Pass** | Works end-to-end via UI or verified API + projections |
| ⚠️ **Partial** | Backend works; UI missing or degraded UX |
| ❌ **Fail** | Not reachable without scripts/admin intervention |
| 🔧 **API-only** | Backend path verified; no frontend |

---

## Student Journey

| Step | UI | API / Backend | Status | Notes |
|------|----|--------------|--------|-------|
| Registration | ❌ No page | `POST /auth/register` | ❌ | Must use API or seed script |
| Login | ✅ `/login` | `POST /auth/login` | ✅ | Demo: `student@prepos-demo.example.com` |
| Profile bootstrap | 🔧 Silent | `GET /students/me` | ⚠️ | Auto-created; errors not shown in UI |
| Onboarding (goals, exam, complete) | ❌ No wizard | `PATCH /students/{id}`, `POST /students/onboarding/complete` | 🔧 API-only | I1.2 uses seed script; blocks self-service |
| Goal creation | ✅ `/student/goals` | `POST /goals` | ✅ | Requires `examId` from profile context |
| Learning graph view | ✅ `/student/learning-graph` | `GET /learning-graph`, `/readiness` | ✅ | Raw concept IDs; limit 50 nodes |
| Submit study activity | ❌ No UI | `POST /learning-graph/activities/study-session` | 🔧 API-only | I1.2 verified via API + event chain |
| Submit revision activity | ❌ No UI | `POST /learning-graph/activities/revision` | 🔧 API-only | Same |
| Recommendations update | ✅ `/student/recommendations` | `GET /twin/recommendations` | ✅ | Requires Celery/outbox drain or worker |
| Revision queue | ✅ `/student/revision-queue` | `GET /learning-graph/revisions/queue` | ✅ | Read-only; no complete action |
| Study plan view | ✅ `/student/study-plan` | `GET /study-plan` | ✅ | Empty until goal + forecast chain runs |
| Study plan execution | ✅ Complete/skip buttons | `POST /study-plan/items/complete\|skip` | ⚠️ | Mutations work; errors silent in UI |
| Forecast updates | ✅ `/student/forecast` | `GET /twin/dashboard`, `/twin` | ⚠️ | KPI cards OK; scenarios as raw JSON |
| Twin dashboard updates | ✅ `/student/dashboard` | `GET /twin/dashboard` | ✅ | I1.2: readiness 46.30 after activities |
| Token refresh mid-session | ❌ | `POST /auth/refresh` | ❌ | 15-min access token → forced re-login |

### Student journey verdict

**Backend chain:** ✅ Validated (I1.2)  
**UI self-service:** ❌ Blocked without onboarding + activity UI  
**Pilot-ready for students:** ⚠️ Only with pre-seeded accounts and admin-run seed

---

## Mentor Journey

| Step | UI | API / Backend | Status | Notes |
|------|----|--------------|--------|-------|
| Login (faculty) | ✅ `/login` | `POST /auth/login` | ✅ | `faculty@prepos-demo.example.com` |
| Dashboard | ✅ `/mentor/dashboard` | `GET /mentor/dashboard` | ✅ | Effectiveness may show 0 until cases resolved |
| Queue | ✅ `/mentor/queue` | `GET /mentor/queue` | ⚠️ | Empty unless case-creating actions fire or demo seed |
| Open case | ✅ `/mentor/cases/[id]` | `GET /mentor/cases/{id}` | ✅ | Linked from queue |
| Add note | ✅ Form | `POST /mentor/cases/{id}/notes` | ⚠️ | Works; mutation errors not shown |
| Resolve case | ✅ Form | `POST /mentor/cases/{id}/resolve` | ⚠️ | **Free-text reason often 400** — must use enum |
| Effectiveness update | 🔧 Dashboard only | Twin projection + case resolution events | ⚠️ | I1.2 verified after resolve |
| Student twin view | ✅ `/mentor/student/[id]` | Twin APIs with `student_id` | ⚠️ | JSON debug blocks; no student name |

### Mentor journey verdict

**Backend chain:** ✅ Validated (I1.2 with demo case seed)  
**UI:** ⚠️ Resolve workflow broken for typical user input (enum mismatch)  
**Pilot-ready for mentors:** ⚠️ With training on resolution enums + seeded queue

---

## Admin Journey

| Step | UI | API / Backend | Status | Notes |
|------|----|--------------|--------|-------|
| Tenant creation | ❌ | `POST /auth/register` | 🔧 API-only | Creates tenant + institute_admin |
| User management | ❌ | No dedicated admin API | ❌ | Users created via register or DB seed |
| Faculty/student provisioning | ❌ | Manual DB or register | ❌ | Seed script creates roles |
| Syllabus import | ❌ | `POST /syllabus/seed/import` | 🔧 API-only | Requires `super_admin` |
| Catalog publish | ❌ | `POST /syllabus/{exam}/catalog/versions/{v}/publish` | 🔧 API-only | Requires `super_admin` |
| Exam catalog CRUD | ❌ | `GET/POST /exams` | 🔧 API-only | Partially public read |
| Institute admin portal | ❌ | Mentor portal used instead | ❌ | No admin UI routes |

### Admin journey verdict

**No admin frontend exists.** All institute operations require API, OpenAPI docs, or seed scripts.

---

## Event Chain Dependency (all journeys)

Student activity → mentor case creation requires:

```
Activity → LearningGraphUpdated → ForecastUpdated → … → MentorActionUpdated → MentorCaseCreated
```

**Operational requirement:** Celery **worker + beat** must run in deployed environments. Local dev can use `seed_demo_data.py` synchronous drain or `CELERY_TASK_ALWAYS_EAGER=true`.

---

## Journey Blockers Summary

| Blocker | Affects |
|---------|---------|
| No registration/onboarding UI | Student self-service |
| No activity submission UI | Student learning loop |
| Celery worker required | All projection freshness |
| Mentor resolve enum mismatch | Mentor case closure |
| No admin UI | Tenant/syllabus/user ops |
| Token refresh missing | Sessions >15 min |

---

## Recommended Journey Fixes (P1.1 — product, not engines)

1. `/register` + `/student/onboarding` multi-step flow  
2. Activity buttons on revision queue and learning graph  
3. Mentor resolve dropdown (`STUDENT_CONTACTED`, etc.)  
4. Minimal admin page: syllabus status + invite user (API wrappers only)  
5. Token refresh in API client  
