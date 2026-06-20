# Observability Audit — Sprint P1.0

**Generated:** 2026-06-20  
**Scope:** Logging, tracing, health, error reporting

---

## Executive Summary

PrepOS has **solid structured logging foundations** and optional Sentry/OpenTelemetry hooks, but observability is **off by default in development** and **incomplete for production ops** (no metrics endpoint, partial readiness, no response request-ID echo).

**Observability readiness:** 58/100

---

## Structured Logging

| Component | Location | Status |
|-----------|----------|--------|
| Logger | `backend/src/prepos/core/logging.py` | ✅ structlog, JSON to stdout |
| Timestamps | ISO UTC | ✅ |
| Context binding | `request_id`, `tenant_id`, `user_id` | ✅ via deps + handlers |
| Domain errors | WARNING with code, message, path | ✅ `main.py` handler |
| Event handlers | `event_handled`, `event_duplicate_skipped` | ✅ dispatcher logs |

**Sample context fields:** `request_id`, `tenant_id`, `user_id`, `correlation_id` on write paths

---

## Request IDs

| Item | Status | Notes |
|------|--------|-------|
| Incoming `X-Request-Id` | ✅ | Accepted in deps |
| Auto-generation | ✅ | UUID if header absent |
| Bound to structlog | ✅ | |
| Returned on response | ❌ | No middleware echoes header |
| Frontend propagation | ⚠️ | I1.2 validation sets `x-request-id` manually; client does not by default |

---

## Correlation IDs

| Item | Status | Notes |
|------|--------|-------|
| Set from request context | ✅ | On authenticated writes |
| Outbox events | ✅ | `correlation_id`, `causation_id` on domain events |
| Cross-service trace | ⚠️ | Same as request_id in current impl; no separate correlation header |
| Celery task propagation | ⚠️ | Envelope dict passed; log context may reset in worker |

---

## Event Tracing

| Item | Status | Notes |
|------|--------|-------|
| Outbox table | ✅ | `outbox_events` with status, attempts, errors |
| Processed events | ✅ | Idempotency via `processed_events` |
| Handler registration | ✅ | 20+ handler modules imported in `main.py` |
| Celery dispatch | ✅ | `dispatch_domain_event` task |
| Beat publish batch | ✅ | Every 30s |
| Event audit in logs | ✅ | `event_handled`, producer, consumer name |
| Distributed trace spans per event | ❌ | No OTEL span per handler unless enabled |

**Debug workflow:** Query `outbox_events` by `correlation_id`; grep logs for `event_handled`.

---

## OpenTelemetry

| Item | Status | Notes |
|------|--------|-------|
| Setup | `core/observability.py` | ✅ SQLAlchemy + Redis instrumentation |
| FastAPI instrumentation | ✅ | Via `instrument_fastapi_app` |
| **Development skip** | ⚠️ | **Disabled when `app_env=development` OR `otel_enabled=false`** |
| `.env.example` | `OTEL_ENABLED=false` | Off by default |
| Exporter | OTLP or console | Configurable |
| Service name | `OTEL_SERVICE_NAME=prepos-api` | ✅ |

**Gap:** Local dev intentionally skips OTEL (fixed CORS/OPTIONS crash history); prod must explicitly enable.

---

## Sentry

| Item | Status | Notes |
|------|--------|-------|
| Integration | `setup_sentry` | ✅ FastAPI, Celery, SQLAlchemy |
| DSN | Optional `SENTRY_DSN` | Empty in example |
| PII | `send_default_pii=false` | ✅ |
| Trace sample rate | 10% default | Configurable |

---

## Health Checks

| Endpoint | Purpose | Checks | Status |
|----------|---------|--------|--------|
| `GET /health` | Liveness | API process | ✅ |
| `GET /health/ready` | Readiness | PostgreSQL `SELECT 1` | ✅ partial |

**Readiness gaps:**

| Missing check | Impact |
|---------------|--------|
| Redis connectivity | Celery/cache failures undetected |
| Celery worker alive | Outbox backlog undetected |
| Outbox pending count threshold | Projection lag undetected |
| Migration version match | Schema drift undetected |

---

## Frontend Observability

| Item | Status |
|------|--------|
| Client-side error reporting | ❌ No Sentry/browser SDK |
| API error logging | ❌ Errors thrown to UI only |
| Performance monitoring | ❌ |

---

## Recommendations (no new engines)

### P0 — Pilot

1. Echo `X-Request-Id` on all API responses  
2. Extend `/health/ready` with Redis ping  
3. Enable Sentry in staging with DSN  
4. Add frontend API client header: `X-Request-Id` per request  

### P1 — Production

5. Enable OTEL with OTLP endpoint in prod  
6. Add Celery worker health endpoint or queue depth metric  
7. Alert on outbox `pending` count > threshold  
8. Structured log aggregation (CloudWatch/Datadog/Loki)  

### P2

9. Prometheus `/metrics` endpoint  
10. Browser Sentry for Next.js  

---

## Production Risks

| Risk | Detection today | Mitigation |
|------|-----------------|------------|
| Silent outbox backlog | Manual DB query | Worker health + pending alert |
| Request not traceable across FE/BE | No response header | Echo request ID |
| OTEL off in prod misconfig | No traces | Deploy checklist item |
| DB up but Redis down | Ready=ok | Add Redis to readiness |
