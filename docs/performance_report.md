# Performance Audit — Sprint P1.0

**Generated:** 2026-06-20  
**Scope:** Query patterns, projections, hot paths — **no load testing performed**

---

## Executive Summary

PrepOS uses **bulk queries for heavy reads** (exam tree, LG overview) and **event-driven async projections** for twin/study plan rebuilds. Risks concentrate in **concept graph traversal N+1**, **uncached learning graph reads**, and **synchronous projection fan-out** under load without worker scaling.

**Performance readiness:** 60/100 (architecture sound; scale unproven)

---

## N+1 Query Patterns

| Location | Pattern | Risk | Severity |
|----------|---------|------|----------|
| `ExamCatalogService.get_concept_ancestors` | Loop: fetch parent per level | O(depth) queries | Medium |
| `ExamCatalogService.get_concept_descendants` | Recursive child fetches | O(nodes) queries | Medium |
| `build_exam_tree` | 4 bulk list queries | ✅ Good | — |
| Auth user load | `selectinload` roles/permissions | ✅ Good | — |
| Most LG read repos | Bulk selects by tenant+student | ✅ Good | — |

**Mitigation (no new engines):** Cache ancestor chains; batch parent lookups; materialized path column (future migration).

---

## Projection Rebuild Performance

### Twin incremental rebuild

| Item | Details |
|------|---------|
| Entry | `TwinRebuildService` via `request_twin_incremental_update` |
| Locking | `twin_rebuild_locks` — debounce + distributed lock |
| Triggers | 15+ event types → `twin_rebuild_orchestrator` consumers |
| Work per event | Multiple section rebuilds (readiness, recommendations, mentor, etc.) |

**Risk:** High event volume (goal update fan-out) causes **many sequential handler runs** per student. I1.2 seed drained **110+ events** for one activity batch.

**Mitigation:** Worker horizontal scaling; monitor outbox lag; debounce already present.

### Study plan rebuild

| Item | Details |
|------|---------|
| Trigger | `ForecastUpdated`, `LearningGraphUpdated`, personalization events |
| Service | `StudyPlanService.rebuild_study_plan` |

**Risk:** Rebuild on every forecast tick — acceptable for pilot, review at 100+ concurrent students.

---

## Learning Graph Traversal Performance

| Operation | Implementation | Notes |
|-----------|----------------|-------|
| Overview (limit 50) | Bulk node fetch | ✅ Paginated by limit param |
| Readiness aggregate | SQL aggregation | ✅ Indexed by tenant/student |
| Weaknesses | Top-N query | ✅ limit param |
| Revision queue | Projection table read | ✅ Precomputed |
| LG cache | `NoOpLearningGraphCache` in deps | ❌ **No caching** |

**Pilot impact:** 618 nodes provisioned per student (UPSC seed) — overview at limit=50 is fine; full graph ops need pagination UI.

**Indexes:** Migrations include composite indexes on `(tenant_id, student_id, concept_id)` and status fields.

---

## Mentor Queue Performance

| Operation | Implementation | Notes |
|-----------|----------------|-------|
| Queue list | Read from mentor projection tables | ✅ limit param (default 50) |
| Dashboard metrics | Aggregated query | ✅ Single round-trip |
| Case detail | PK lookup + notes | ✅ |

**Risk:** Low for pilot scale. At 1000 students, queue prioritization query needs EXPLAIN ANALYZE on production data volume.

---

## Recommendation Performance

| Operation | Implementation | Notes |
|-----------|----------------|-------|
| Twin recommendations | Read from twin projection payload | ✅ Precomputed |
| Regeneration | Event-driven on LG/forecast updates | Async |

**Not a runtime compute bottleneck** — depends on projection freshness (Celery).

---

## API Hot Paths (estimated)

| Endpoint | Load profile |
|----------|--------------|
| `GET /twin/dashboard` | Read projection — low CPU |
| `GET /learning-graph` | DB read up to 200 nodes — medium |
| `POST /learning-graph/activities/*` | Write outbox + 202 — low sync; high async fan-out |
| `GET /concepts/search` | Text search — depends on index |
| `POST /auth/login` | bcrypt verify — CPU bound under brute force |

---

## Frontend Performance

| Item | Status |
|------|--------|
| Next.js static generation | ✅ Most routes static |
| TanStack Query caching | ✅ 5 min stale default (check query-provider) |
| No pagination on LG page | ⚠️ Fixed 50 nodes |
| JSON `<pre>` on forecast | ⚠️ Large payload render cost |

---

## Load Testing Status

| Test | Status |
|------|--------|
| k6 / Locust scenarios | ❌ Not run |
| DB connection pool sizing | ⚠️ Default 10+20 — unvalidated |
| Celery worker concurrency | ⚠️ Default — unvalidated |

---

## Recommendations

### P0 — Pilot (10–100 users)

1. Ensure Celery worker running — projections are the real bottleneck  
2. Monitor outbox pending count and p95 dispatch latency  
3. Run EXPLAIN on mentor queue + LG readiness queries with seed data  

### P1 — 100–1000 users

4. Enable Redis-backed LG cache (infrastructure exists; NoOp wired)  
5. Fix concept ancestor N+1 before heavy concept API use  
6. Load test: 50 concurrent students posting activities  
7. Scale workers horizontally; separate `events` queue concurrency  

### P2

8. Read replicas for reporting queries  
9. CDN for Next.js static assets  
10. Connection pool tuning from load test results  

---

## Production Risks

| Risk | When |
|------|------|
| Outbox backlog under activity spikes | >50 concurrent writers |
| Twin rebuild lock contention | Multiple rapid events per student |
| bcrypt CPU on login storms | Auth endpoint without rate limit |
| Full LG fetch in future UI | If limit raised without pagination |
