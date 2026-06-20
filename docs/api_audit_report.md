# API Audit — Sprint P1.0

**Generated:** 2026-06-20  
**Base path:** `/api/v1`  
**Total endpoints:** 49 (+ 2 health at root)  
**Global auth:** Bearer token or `access_token` HttpOnly cookie via `get_current_context`

---

## Global Conventions

| Concern | Implementation |
|---------|----------------|
| **Validation** | Pydantic v2 on request bodies and query params; FastAPI 422 on schema failure |
| **Domain errors** | `{ error: { code, message, details, correlation_id } }` via `DomainError` handler |
| **Request ID** | `X-Request-Id` header; auto-generated if absent |
| **Correlation ID** | Set from request context on writes; propagated to outbox |
| **Pagination** | Offset/limit only on `GET /concepts/search`; other lists use `limit` only |
| **Rate limiting** | ❌ None |

### Error code → HTTP mapping

| Code | HTTP |
|------|------|
| `NOT_FOUND` | 404 |
| `TENANT_ACCESS_DENIED`, `AUTHORIZATION_ERROR` | 403 |
| `AUTHENTICATION_ERROR` | 401 |
| `CONFLICT`, `OPTIMISTIC_LOCK` | 409 |
| `VALIDATION_ERROR` | 422 |
| default | 400 |

---

## Health (public)

| Method | Route | Auth | Request | Response | Pagination | Validation | Errors |
|--------|-------|------|---------|----------|------------|------------|--------|
| GET | `/health` | None | — | `{ status: "ok" }` | — | — | — |
| GET | `/health/ready` | None | — | `{ status, checks: { api, database } }` | — | — | Degraded if DB fails |

---

## Auth — `/api/v1/auth`

| Method | Route | Auth | Roles | Request DTO | Response DTO | Notes |
|--------|-------|------|-------|-------------|--------------|-------|
| POST | `/register` | None | — | `RegisterRequest`: tenant_slug, tenant_name, email, password (8–128), full_name | `TokenResponse` | 201; sets cookies; creates institute_admin |
| POST | `/login` | None | — | `LoginRequest`: tenant_slug, email, password | `TokenResponse` | Sets HttpOnly cookies |
| POST | `/refresh` | None | — | `RefreshRequest`: refresh_token | `TokenResponse` | Rotates refresh JTI |
| POST | `/logout` | Required | Any | Optional `RefreshRequest` | 204 | Revokes refresh |
| GET | `/me` | Required | Any | — | `UserResponse` | id, tenant_id, email, roles, permissions |

---

## Exams — `/api/v1/exams`

| Method | Route | Auth | Roles | Request | Response | Pagination |
|--------|-------|------|-------|---------|----------|------------|
| GET | `` | **Public** | — | Query: `status?` | `list[ExamResponse]` | — |
| POST | `` | Required | super_admin \| institute_admin | `CreateExamRequest` | `ExamResponse` | — |
| GET | `/{exam_id}` | **Public** | — | — | `ExamResponse` | — |

---

## Syllabus — `/api/v1/syllabus`

| Method | Route | Auth | Roles | Request | Response |
|--------|-------|------|-------|---------|----------|
| GET | `/{exam_id}/tree` | **Public** | — | Query: include_draft, catalog_version? | `ExamTreeResponse` |
| POST | `/{exam_id}/catalog/versions/{version}/publish` | Required | super_admin | `PublishCatalogRequest?` | `CatalogVersionResponse` |
| POST | `/seed/import` | Required | super_admin | — | `SeedImportResponse` |

---

## Concepts — `/api/v1/concepts` (all public)

| Method | Route | Request (query/body) | Response | Pagination |
|--------|-------|------------------------|----------|------------|
| GET | `/search` | exam_id, query, subject_id, topic_id, status, catalog_version, offset≥0, limit 1–100 | `PaginatedConceptsResponse` | offset/limit + total |
| GET | `/{concept_id}` | — | `ConceptResponse` | — |
| GET | `/{concept_id}/ancestors` | — | `ConceptAncestorsResponse` | — |
| GET | `/{concept_id}/descendants` | — | `ConceptDescendantsResponse` | — |

---

## Students — `/api/v1/students`

| Method | Route | Auth | Roles | Request | Response |
|--------|-------|------|-------|---------|----------|
| GET | `/me` | Required | Any (auto-create student profile) | — | `StudentProfileResponse` |
| GET | `/{student_id}` | Required | StudentAccessPolicy | — | `StudentProfileResponse` |
| PATCH | `/{student_id}` | Required | can_modify; post-onboarding blocked for students | `UpdateStudentGoalsRequest` | `StudentProfileResponse` |
| POST | `/onboarding/complete` | Required | student \| admin | `CompleteOnboardingRequest` | `CompleteOnboardingResponse` |

---

## Learning Graph — `/api/v1/learning-graph`

All require auth. Optional `student_id` with student self-access enforcement.

| Method | Route | Request | Response | Limit |
|--------|-------|---------|----------|-------|
| GET | `` | student_id?, limit | `LearningGraphOverviewResponse` | 1–200, default 50 |
| GET | `/summary` | student_id? | `LearningGraphSummaryResponse` | — |
| GET | `/nodes/{concept_id}` | student_id? | `ConceptProgressNodeResponse` | — |
| GET | `/weaknesses` | student_id?, limit | `LearningGraphWeaknessesResponse` | 1–50 |
| GET | `/revisions/due` | student_id?, limit | `list[DueRevisionItemResponse]` | 1–200 |
| GET | `/revisions/queue` | student_id?, limit | `list[RevisionQueueItemResponse]` | 1–200 |
| GET | `/readiness` | student_id? | `LearningGraphReadinessResponse` | — |
| POST | `/activities/assessment` | `RecordAssessmentRequest` | `LearningGraphActivityResponse` (202) | — |
| POST | `/activities/revision` | `RecordRevisionRequest` | 202 | — |
| POST | `/activities/study-session` | `RecordStudySessionRequest` | 202 | — |
| POST | `/activities/pyq-change` | `RecordPyqChangeRequest` | 202 | — |

**Write path:** Outbox enqueue → async projection (Celery).

---

## Study Plan — `/api/v1/study-plan`

| Method | Route | Request | Response |
|--------|-------|---------|----------|
| GET | `` | student_id?, exam_id? | `StudyPlanResponse` |
| POST | `/items/complete` | `StudyPlanExecutionRequest` | `StudyPlanExecutionResponse` (202) |
| POST | `/items/skip` | same | 202 |

---

## Goals — `/api/v1/goals`

| Method | Route | Request | Response |
|--------|-------|---------|----------|
| POST | `` | `GoalUpsertRequest` + student_id? | `GoalResponse` (201) |
| PUT | `` | same | `GoalResponse` |
| GET | `` | exam_id (required), student_id? | `GoalResponse \| null` |

**GoalUpsertRequest:** exam_id, target_readiness_score (0–100), target_date, daily_capacity_minutes (30–300)

---

## Mentor — `/api/v1/mentor`

Requires **faculty** or **institute_admin** (`super_admin` bypass).

| Method | Route | Request | Response | Limit |
|--------|-------|---------|----------|-------|
| GET | `/queue` | — | `list[MentorQueueItemResponse]` | 1–200 |
| GET | `/dashboard` | — | `MentorDashboardResponse` | — |
| GET | `/cases/{case_id}` | — | `MentorCaseResponse` | — |
| GET | `/cases` | status? | `list[MentorCaseResponse]` | 1–200 |
| POST | `/cases/{case_id}/notes` | `AddCaseNoteRequest` | `MentorCaseResponse` | — |
| POST | `/cases/{case_id}/resolve` | `ResolveCaseRequest` | `MentorCaseResponse` | Enum validation |

---

## Twin — `/api/v1/twin`

| Method | Route | Response | Limit | Notes |
|--------|-------|----------|-------|-------|
| GET | `/recommendations` | `list[TwinRecommendationResponse]` | 1–100 | |
| GET | `` | `TwinResponse` | — | Full projection |
| GET | `/dashboard` | `TwinDashboardResponse` | — | Lightweight read model |
| GET | `/metrics` | `TwinProjectionMetricsResponse` | — | ⚠️ Any authenticated user |
| GET | `/snapshot` | `TwinSnapshotResponse` | — | Deprecated |

---

## API Audit Findings

### Strengths

- Consistent Pydantic DTOs across domains
- RBAC enforced at router and use-case layers
- Tenant isolation via JWT `tenant_id`
- Domain error envelope with correlation ID
- Contract tests for OpenAPI schemas (5 files)

### Gaps (P1.0)

| Gap | Severity | Recommendation |
|-----|----------|----------------|
| 9 public read endpoints (exams, concepts, syllabus tree) | Medium | Rate limit or API key for production |
| No rate limiting on auth endpoints | High | Add slowapi/throttle on login/register/refresh |
| `/twin/metrics` open to all roles | Low | Restrict to admin |
| Inconsistent pagination (limit-only vs offset/limit) | Low | Document per-endpoint contracts |
| 422 uses FastAPI default shape, not domain envelope | Low | Unify error responses |
| Frontend covers ~40% of endpoints | High | Product sprint, not API sprint |

---

## Frontend ↔ API Matrix (summary)

| Domain | Backend endpoints | Frontend wired |
|--------|-------------------|----------------|
| Auth | 5 | 3 (login, me, logout) |
| Students | 4 | 1 (me read only) |
| Learning graph | 11 | 5 read + 0 write |
| Study plan | 3 | 3 |
| Goals | 3 | 3 |
| Twin | 5 | 3 |
| Mentor | 6 | 5 |
| Catalog (exams/syllabus/concepts) | 10 | 0 |
