# Security Audit — Sprint P1.0

**Generated:** 2026-06-20  
**Scope:** Authentication, authorization, tenancy, transport, secrets

---

## Executive Summary

Core auth is **production-grade at the pattern level** (bcrypt, JWT access/refresh rotation, RBAC, tenant isolation). Gaps are **operational and perimeter**: no rate limiting, public catalog APIs, placeholder secrets in examples, and incomplete frontend token lifecycle.

**Security readiness:** 65/100

---

## JWT Handling

| Item | Status | Details |
|------|--------|---------|
| Algorithm | ✅ | HS256 |
| Access token TTL | ✅ | 15 minutes (configurable) |
| Refresh token TTL | ✅ | 7 days |
| Token in Authorization header | ✅ | Bearer |
| Token in HttpOnly cookie | ✅ | Dual path supported |
| Secret key | ⚠️ | Min 32 chars required; placeholder in `.env.example` |
| Payload | ✅ | user_id, tenant_id, roles[], token type |

---

## Refresh Tokens

| Item | Status | Details |
|------|--------|---------|
| Stored in DB | ✅ | With JTI |
| Rotation on refresh | ✅ | Old JTI revoked |
| Revoke on logout | ✅ | |
| Frontend refresh flow | ❌ | Token stored but never used |
| Cookie + body dual delivery | ✅ | Backend supports both |

---

## RBAC (Role-Based Access Control)

| Role | Typical access |
|------|----------------|
| `student` | Own profile, LG, twin, study plan, goals |
| `faculty` | Mentor dashboard, queue, cases |
| `institute_admin` | Mentor portal + student admin operations |
| `super_admin` | Bypass all role checks; syllabus seed/publish |

| Item | Status |
|------|--------|
| Roles in JWT | ✅ |
| `require_role()` helper | ✅ |
| Router-level checks | ✅ Mentor, syllabus publish, seed import |
| Use-case-level checks | ✅ Student access policy, onboarding policy |
| Frontend RoleGuard | ⚠️ Client-only; bypassable before hydration |

---

## Tenant Isolation

| Item | Status | Details |
|------|--------|---------|
| tenant_id in JWT | ✅ | |
| Queries scoped by tenant | ✅ | Repository pattern |
| Cross-tenant student access | ✅ Blocked | StudentAccessPolicy |
| Register creates new tenant | ⚠️ | Open registration — no invite gate |
| Integration tests for isolation | ✅ | LG provisioning tenant isolation test |

---

## CORS

| Item | Status | Details |
|------|--------|---------|
| Middleware | ✅ | FastAPI CORSMiddleware |
| Credentials | ✅ | `allow_credentials=True` |
| Origins | ✅ | From `CORS_ORIGINS` env JSON list |
| Methods/headers | ✅ | Wildcard allowed |

**Production:** Must restrict origins to known frontend domains only.

---

## Rate Limiting

| Item | Status |
|------|--------|
| Login/register/refresh | ❌ None |
| Public catalog endpoints | ❌ None |
| Activity ingestion | ❌ None |

**Risk:** Brute-force credentials, catalog scraping, activity spam.

**Recommendation:** Add slowapi or reverse-proxy rate limits on `/auth/*` and public GETs.

---

## Password Storage

| Item | Status | Details |
|------|--------|---------|
| Algorithm | ✅ | bcrypt |
| Salt | ✅ | gensalt per hash |
| Register min length | ✅ | 8 characters (Pydantic) |
| Login validation | ✅ | Constant-time verify via bcrypt |

---

## Secrets Management

| Item | Status | Details |
|------|--------|---------|
| `.env.example` | ⚠️ | Contains placeholder SECRET_KEY |
| Settings validation | ✅ | SECRET_KEY min 32 chars |
| DB credentials in compose | ⚠️ | Hardcoded `prepos/prepos` for dev |
| Secrets in git | ✅ | `.env` not committed (example only) |
| Production guidance | ⚠️ | Document secrets manager requirement |

---

## Additional Security Notes

| Topic | Status | Notes |
|-------|--------|-------|
| CSRF (cookie auth) | ⚠️ | SameSite=lax; no CSRF token |
| `/twin/metrics` | ⚠️ | Any authenticated role |
| Public syllabus/concepts | ⚠️ | Intentional for catalog; consider auth in prod |
| Audit logging | ✅ | Auth events to audit log |
| HTTPS enforcement | ⚠️ | `COOKIE_SECURE=false` in dev example |
| SQL injection | ✅ | SQLAlchemy parameterized queries |
| Input validation | ✅ | Pydantic on all write DTOs |

---

## Frontend Security Gaps

| Gap | Severity |
|-----|----------|
| Access token in localStorage (Zustand persist) | Medium — XSS exposure |
| No refresh rotation | High — session expiry UX + stale tokens |
| No CSP headers documented | Medium |
| Client-only auth guards | Low — API still enforces |

---

## Recommendations

### P0 — Before pilot

1. Enforce strong `SECRET_KEY` at deploy (fail if placeholder)  
2. Rate limit `/auth/login`, `/auth/register`, `/auth/refresh`  
3. Implement token refresh in frontend  
4. Set `COOKIE_SECURE=true` in production  
5. Fix mentor resolve to prevent injection via free-text (use enum)  

### P1 — Before scale

6. Consider httpOnly-only auth (reduce localStorage token)  
7. Gate `/auth/register` behind invite or admin approval  
8. Restrict public catalog or add API key  
9. Add CSRF protection if cookie-primary auth  
10. Restrict `/twin/metrics` to admin roles  

### P2

11. Security headers middleware (HSTS, CSP, X-Frame-Options)  
12. Periodic dependency audit (`pip audit`, npm audit)  

---

## Production Risks

| Risk | Likelihood | Impact |
|------|------------|--------|
| Credential stuffing on login | Medium | Account compromise |
| Open tenant registration | Medium | Spam tenants |
| XSS → token theft from localStorage | Low–Medium | Session hijack |
| Default dev secrets in prod deploy | Low | Critical if misconfigured |
