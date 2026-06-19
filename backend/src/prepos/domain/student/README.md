# Student bounded context

The Student domain owns learner profiles, onboarding state, and the provisioning shells
required before Learning Graph (S4) and Preparation Twin (S6) engines are implemented.

## Responsibilities

- Persist student goals: target exam, target year, daily study hours, experience level
- Track onboarding completion lifecycle
- On onboarding completion:
  - Create a `learning_graph_provisions` shell (expected node count, zero provisioned nodes)
  - Create a `preparation_twins` shell with empty JSONB profiles and `status=provisioned`
  - Emit `StudentOnboardingCompleted` via the transactional outbox

## What this module does NOT do

- Bulk insert `student_concept_progress` rows (deferred to S4 Learning Graph)
- Twin rebuild / scoring projections (deferred to S6 Preparation Twin)
- Diagnostic assessment flows

## Key tables

| Table | Purpose |
|---|---|
| `students` | Tenant-scoped profile linked 1:1 to `users` |
| `learning_graph_provisions` | Provisioning contract for LG bulk node creation |
| `preparation_twins` | Twin shell per `(tenant, student, exam)` |

## API surface

| Method | Path | Description |
|---|---|---|
| GET | `/api/v1/students/me` | Current user's profile (auto-creates empty profile) |
| GET | `/api/v1/students/{student_id}` | Profile by ID (self or admin) |
| PATCH | `/api/v1/students/{student_id}` | Update goals before onboarding |
| POST | `/api/v1/students/onboarding/complete` | Complete onboarding + provision shells |

## Events

### `StudentOnboardingCompleted`

Producer: `student_onboarding_service`

Payload (DOMAIN_EVENTS §9.2):

- `student_id`
- `user_id`
- `tenant_id`
- `exam_id`
- `diagnostic_offered`
- `target_stages[]`
- `catalog_version`

Consumers (future sprints):

- S4 Learning Graph — bulk node provisioning from `learning_graph_provisions`
- S6 Preparation Twin — `FullRebuild` from empty shell

## Field naming

API responses expose `target_exam` (maps to `target_exam_id` in DB) and `daily_study_hours`
(maps to master plan `daily_hours`).

## Authorization

- Students may view/update their own profile
- `institute_admin` / `super_admin` may view any student in tenant
- Goal updates after onboarding are blocked for students; admins may override
