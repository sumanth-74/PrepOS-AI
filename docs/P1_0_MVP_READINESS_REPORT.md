# Sprint P1.0 — MVP Readiness Score & Final Recommendation

**Generated:** 2026-06-20  
**Sprint objective:** Pilot readiness audit — **no new intelligence engines**

**Related reports:**

- [Frontend Audit](./frontend_audit_report.md)
- [E2E Journey Validation](./e2e_journey_report.md)
- [Deployment Readiness](./deployment_readiness_report.md)
- [API Audit](./api_audit_report.md)
- [Observability](./observability_report.md)
- [Security](./security_audit_report.md)
- [Performance](./performance_report.md)
- [Test Coverage](./test_coverage_report.md)
- [I1.2 E2E Validation](./I1_2_E2E_VALIDATION_REPORT.md)

---

## 9. MVP Readiness Score

| Category | Score (0–100) | Notes |
|----------|---------------|-------|
| **Frontend** | 55 | Routes build and render; missing onboarding, activities, refresh, admin; mentor resolve UX bug |
| **Backend** | 82 | 49 APIs, event chain validated, 454 tests; Celery required for freshness |
| **API** | 78 | Consistent DTOs/RBAC; public catalog + no rate limits |
| **Security** | 65 | Solid JWT/bcrypt/RBAC; no rate limit, open register, localStorage tokens |
| **Performance** | 60 | Async projections scale with workers; N+1 on concept tree; uncached LG |
| **Testing** | 70 | Strong backend unit/integration; zero frontend E2E |
| **Deployment** | 62 | Compose-ready backend; frontend placeholder in docker-compose |
| **Operations** | 58 | structlog + optional Sentry/OTEL; partial readiness; no runbooks |

### Overall MVP Readiness Score: **66 / 100**

**Interpretation:** Platform is **technically proven** (I1.2) but **not self-service pilot-ready** without seed scripts, ops runbooks, and critical UI gaps closed.

---

## 10. Can PrepOS Be Used By…?

### 10 students — **Yes, with constraints** ✅

| Requirement | Status |
|-------------|--------|
| Pre-seeded accounts | ✅ `seed_demo_data.py` |
| Celery worker running | Required |
| Manual institute setup | Acceptable for pilot |
| UI gaps | Students need admin to seed; no self-registration |

**Verdict:** Controlled pilot with hand-holding works today.

---

### 100 students — **Not yet** ⚠️

| Blocker | Why |
|---------|-----|
| No onboarding UI | Cannot scale manual seeding |
| No activity UI | Learning loop breaks without API/scripts |
| Celery ops unproven | Outbox lag at moderate write volume |
| No rate limiting | Auth/catalog abuse risk |
| Single-worker default | Projection backlog risk |
| No monitoring alerts | Incidents undetected |

**Verdict:** Needs P1.1 product hardening + ops baseline (estimated 4–6 weeks).

---

### 1000 students — **No** ❌

| Blocker | Why |
|---------|-----|
| All 100-student blockers | Amplified |
| Load testing not done | Unknown breaking point |
| No horizontal scaling runbook | Worker/DB pool untuned |
| No CDN/TLS production frontend | Deployment immature |
| Concept API N+1 | Catalog features won't scale |
| No LG caching | Read amplification |

**Verdict:** Requires performance validation, infra hardening, and multi-tenant ops (estimated 3+ months post-pilot).

---

## Blockers (Prioritized)

### P0 — Must fix before any external pilot

1. **Celery worker + beat in production** — projections stall without them  
2. **Registration + onboarding UI** — students cannot self-serve  
3. **Study/revision activity UI** — core learning loop invisible in product  
4. **Token refresh in frontend** — 15-min sessions unusable for study sessions  
5. **Mentor case resolve enum select** — free-text causes 400 errors  
6. **Deploy real Next.js frontend** — replace docker-compose nginx placeholder  
7. **Production secrets + COOKIE_SECURE** — security baseline  

### P1 — Should fix before 100-student pilot

8. Concept label mapping in UI  
9. Rate limiting on `/auth/*`  
10. Mutation error feedback (study plan, mentor forms)  
11. CI: pytest + frontend build on every PR  
12. Playwright smoke tests (student + mentor happy paths)  
13. Readiness probe: Redis + outbox pending alert  
14. Minimal admin UI (syllabus status, user invite)  

### P2 — Before scale / production

15. OpenAPI codegen for frontend DTOs  
16. LG Redis cache enablement  
17. Fix concept ancestor N+1  
18. Load testing suite  
19. Full observability (OTEL + Sentry + request ID echo)  
20. Security headers + register invite gate  

---

## Production Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| Outbox backlog → stale twin/UI | **Critical** | Worker monitoring, alerts on pending count |
| Missing Celery in deploy | **Critical** | Compose/K8s checklist; fail deploy if worker unhealthy |
| Placeholder frontend deployed | **High** | Separate Next.js deploy pipeline |
| Default SECRET_KEY | **High** | Startup validation rejects placeholder |
| Open registration spam tenants | **Medium** | Invite-only register |
| XSS → token in localStorage | **Medium** | Refresh + httpOnly path |
| Auth brute force | **Medium** | Rate limits |
| OTEL off in prod misconfig | **Low** | Deploy checklist |
| Mentor queue empty in demos | **Low** | Document seed script or escalation thresholds |

---

## Recommended Next Implementation Phase

### **Sprint P1.1 — Pilot Product Completion** (4–6 weeks)

**Scope:** Product and ops only — **zero new engines**

| Workstream | Deliverables |
|------------|--------------|
| **Student UX** | `/register`, `/student/onboarding` wizard, activity forms on revision queue + LG |
| **Auth hardening** | Token refresh, 401 retry, optional Next.js middleware |
| **Mentor UX** | Resolve enum dropdown, mutation toasts, student name on queue |
| **Concept UX** | Label resolver hook using `/concepts/{id}` |
| **Admin MVP** | Single admin page: tenant info, syllabus publish status, invite user |
| **Deploy** | Next.js Dockerfile, production compose profile, env checklist |
| **Ops** | Worker health, outbox alert, request ID response header |
| **QA** | Playwright smoke (10 tests), CI pipeline |

**Exit criteria:** 10-student pilot runs self-service for 2 weeks without seed script re-runs.

---

### **Sprint P1.2 — Scale Preparation** (after pilot feedback)

- Rate limiting, LG cache, load tests to 100 concurrent users  
- OpenAPI codegen, E2E expansion, admin user management  
- Formal pytest-cov baseline ≥70% on application layer  

---

### **Sprint P2.0 — Production** (after 100-student validation)

- Multi-region deploy, read replicas, CDN  
- Full observability stack, security audit remediation  
- 1000-student load test gate  

---

## Summary

PrepOS has a **mature backend** with validated event-driven architecture and extensive tests. The **frontend MVP shell works** but lacks the flows real students and mentors need day-to-day. With **P1.1 focused on UX completion and ops** — not new AI — the platform can support a **10-student controlled pilot** immediately (with seed + worker) and a **100-student pilot** after P1.1.

**Overall MVP Readiness: 66/100 — proceed to pilot only with documented constraints; do not open public registration until P0 blockers are cleared.**
