# Sprint P7 S15 — Knowledge Foundation (Phase 1 RAG Infrastructure)

## Summary

Phase 1 retrieval infrastructure is implemented without LLM answer generation. Admins can upload UTF-8 text/markdown sources; the system chunks content, embeds via Celery, and exposes hybrid search (vector + Postgres FTS + Reciprocal Rank Fusion).

## Database

Migration `028_knowledge_foundation`:

- Enables `pgvector`
- `knowledge_sources` — provenance, status, indexing metrics
- `knowledge_chunks` — retrieval units with generated `content_tsv`
- `knowledge_chunk_embeddings` — `vector(1536)` with HNSW index (pgvector index limit ≤2000 dims; OpenAI matryoshka reduction via `EMBEDDING_DIMS`)

Chunk metadata stores: `exam_id`, `subject_id`, `topic_id`, `concept_ids`, `catalog_version`, `tenant_id`.

## Infrastructure

| Component | Location |
|-----------|----------|
| Embedding port | `application/knowledge/ports.py` |
| OpenAI provider | `infrastructure/knowledge/embedding_provider.py` |
| Deterministic fallback | same (when `OPENAI_API_KEY` unset) |
| Local file storage | `infrastructure/knowledge/local_storage.py` |
| Chunking | `domain/knowledge/chunking.py` |
| Ingestion | `application/knowledge/services.py` → `KnowledgeIngestionService` |
| Celery embedding job | `tasks/knowledge_tasks.py` (`knowledge` queue) |

## APIs

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| POST | `/api/v1/knowledge/search` | Authenticated | Hybrid retrieval |
| POST | `/api/v1/knowledge/sources` | Institute admin | Upload + ingest |
| GET | `/api/v1/knowledge/sources` | Institute admin | List sources |
| GET | `/api/v1/knowledge/sources/{id}` | Institute admin | Source detail + metrics |
| GET | `/api/v1/admin/knowledge/metrics` | Institute admin | Aggregated indexing metrics |

## Search

1. Embed query (OpenAI or deterministic fallback)
2. Vector similarity (`<=>` cosine distance) on `knowledge_chunk_embeddings`
3. Postgres FTS via `plainto_tsquery` / `ts_rank_cd`
4. Reciprocal Rank Fusion (`k=60` default)
5. Tenant scope: `(tenant_id IS NULL OR tenant_id = caller tenant)`

## Observability

Per-source fields: `chunk_count`, `indexed_chunk_count`, `embedding_failure_count`, `ingestion_failure_count`, `last_error`, ingestion timestamps.

Structured logs: `knowledge_ingestion_started`, `knowledge_ingestion_failed`, `knowledge_embedding_failed`, `knowledge_indexing_completed`.

Admin metrics endpoint aggregates totals across sources.

## Configuration

See `.env.example`:

- `OPENAI_API_KEY`, `EMBEDDING_MODEL`, `EMBEDDING_DIMS`
- `KNOWLEDGE_STORAGE_PATH`, `KNOWLEDGE_HYBRID_ALPHA`
- `KNOWLEDGE_CHUNK_SIZE_TOKENS`, `KNOWLEDGE_CHUNK_OVERLAP_TOKENS`

Docker Postgres image updated to `pgvector/pgvector:pg17`. Celery worker listens on `default,events,knowledge`.

## Explicit non-goals (unchanged)

- No Knowledge Agent
- No `/knowledge/ask`
- No chat / copilot changes
- No LLM generation

## Local workflow

**Postgres requirement:** Migration `028` needs the `vector` extension. Use Docker (`pgvector/pgvector:pg17`, already in `docker-compose.yml`) or pre-install the extension as a superuser:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

```bash
cd backend
source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
pytest tests/unit/test_knowledge_*.py tests/unit/test_migration_028_knowledge_foundation.py -q
```

Upload example (admin token):

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/sources \
  -H "Authorization: Bearer $ADMIN_TOKEN" \
  -F exam_id=upsc_cse \
  -F source_type=ncert \
  -F title="Polity Notes" \
  -F file=@notes.txt
```

Search example:

```bash
curl -X POST http://localhost:8000/api/v1/knowledge/search \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"basic structure doctrine","exam_id":"upsc_cse","limit":8}'
```

## Tests

- Chunking, RRF, embedding provider, search service (mocked repo), migration model columns

## Success criteria mapping

| Criterion | Status |
|-----------|--------|
| Search returns relevant chunks | Hybrid vector + FTS + RRF implemented |
| Hybrid retrieval works | RRF merges ranked lists |
| Ingestion pipeline stable | Upload → chunk → Celery embed → active |
| Admin can upload and index sources | POST/GET source APIs |
