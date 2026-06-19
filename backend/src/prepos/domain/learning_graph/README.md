# Learning Graph bounded context

The Learning Graph is the **sole writer** of per-concept student knowledge state (`student_concept_progress`).

## Responsibilities

- Provision graph nodes on `StudentOnboardingCompleted`
- Apply score mutations from domain events via `LearningGraphService`
- Emit `LearningGraphUpdated` through the transactional outbox
- Append-only audit: `learning_graph_events`, `score_audit_log`

## Single-writer rule

Only `LearningGraphService` may mutate score columns on `student_concept_progress`. All inbound events route through event handlers that delegate to this service.

## Scoring

Pure scoring functions live in `domain/scoring/`. The service invokes them and persists results — scoring modules never touch the database.

## Read path

`LearningGraphReadService` provides read-only APIs. Redis keys (`lg:node`, `lg:summary`, `lg:rollup`) are projection caches only; PostgreSQL is authoritative.

## Deferred to later sprints

- Full retention decay / spaced repetition (S5)
- PYQ importance propagation (S7)
- Readiness computation (S6 Preparation Twin)
