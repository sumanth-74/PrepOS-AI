# Sprint R0.1 — Copilot v0 (Tools-Only) Implementation Report

**Date:** 2026-06-18  
**Scope:** Deterministic Student, Mentor, and Admin Copilots using existing PrepOS APIs — no RAG, LLM, or vector search.

**Related:** [RAG_READINESS_REPORT.md](./RAG_READINESS_REPORT.md) (R0.0 assessment)

---

## Summary

Sprint R0.1 delivers a **tools-only copilot** that routes natural-language questions to deterministic intent handlers backed by Twin, Learning Graph, Goals, Study Plan, Mentor Case, and health APIs. A floating chat panel is available on authenticated student, mentor, and admin routes.

**No RAG / LLM / pgvector** was added.

---

## Backend

### Module layout

```
backend/src/prepos/application/copilot/
  dto.py                 # Request/response models
  intent_router.py       # Keyword-based intent matching
  formatters.py          # Score/text formatting
  health_service.py      # Admin health aggregation
  service.py             # CopilotService orchestrator
  handlers/
    student.py           # 6 student intents
    mentor.py            # 5 mentor intents
    admin.py             # 4 admin intents

backend/src/prepos/api/v1/copilot/router.py
```

### API

**`POST /api/v1/copilot/query`**

Request:

```json
{
  "persona": "student|mentor|admin",
  "question": "...",
  "student_id": "optional UUID for mentor",
  "case_id": "optional UUID for mentor",
  "exam_id": "optional override"
}
```

Response:

```json
{
  "intent": "readiness_low",
  "answer": "...",
  "sources": [{ "label": "Twin dashboard", "reference": "GET /twin/dashboard" }]
}
```

### Supported intents

| Persona | Intent | Data sources |
|---------|--------|--------------|
| Student | `readiness_low` | Twin dashboard drivers |
| Student | `study_today` | Study plan, recommendations, twin |
| Student | `weakest_concepts` | LG weaknesses |
| Student | `recommendation_why` | Twin recommendations |
| Student | `goal_on_track` | Goals, twin forecast |
| Student | `next_activities` | Study plan, revision count |
| Mentor | `summarize_student` | Twin dashboard |
| Mentor | `escalation_reason` | Mentor case, twin mentor fields |
| Mentor | `top_risks` | Twin drivers, risk counts |
| Mentor | `forecast_summary` | Twin forecast sections |
| Mentor | `draft_coaching_note` | Template from twin + case |
| Admin | `platform_health` | `/health/ops` aggregation |
| Admin | `worker_status` | Celery worker ping |
| Admin | `outbox_status` | Outbox counts |
| Admin | `deployment_readiness` | Composite readiness check |

### RBAC

- **Student** persona → `student` role
- **Mentor** persona → `faculty` or `institute_admin` (+ `student_id` required)
- **Admin** persona → `institute_admin` (super_admin bypasses)

---

## Frontend

### Module layout

```
apps/web/src/features/copilot/
  types.ts
  suggested-prompts.ts
  hooks/use-copilot.ts
  components/
    copilot-launcher.tsx    # FAB + panel toggle
    copilot-panel.tsx       # Chat UI
    copilot-message-list.tsx
  copilot-root.tsx          # Root mount
  index.ts
```

### UI features

- Floating **Copilot** button (bottom-left; toasts remain bottom-right)
- Chat-like panel with message history
- Suggested prompt chips per persona
- Source citations (expandable)
- Persona auto-detected from route (`/student`, `/mentor`, `/admin`)
- Mentor student/case context from URL
- Mobile-responsive panel sizing
- ARIA: dialog, live region, labels

Mounted in `apps/web/src/app/layout.tsx` via `<CopilotRoot />`.

---

## Tests

| File | Coverage |
|------|----------|
| `tests/unit/test_copilot_intent_router.py` | Intent routing for all personas |
| `tests/unit/test_copilot_handlers.py` | Student + mentor answer formatting |
| `tests/unit/test_copilot_service.py` | Service orchestration + validation |
| `tests/contract/test_copilot_openapi_contract.py` | OpenAPI path registration |

Run:

```bash
cd backend && pytest tests/unit/test_copilot_*.py tests/contract/test_copilot_openapi_contract.py -q
cd apps/web && npm run typecheck
```

---

## Explicit non-goals (honored)

- No pgvector, embeddings, OpenAI, Anthropic
- No semantic search or `knowledge_chunks`
- No streaming WebSocket chat
- No LLM-generated coaching notes (template-only)

---

## Next steps (post R0.1)

1. Pilot copilot usage metrics (intent counts, unknown rate)
2. Add Playwright smoke test for copilot panel open + suggested prompt
3. Proceed to P7 RAG only if adoption validates need for content Q&A

---

*End of Sprint R0.1*
