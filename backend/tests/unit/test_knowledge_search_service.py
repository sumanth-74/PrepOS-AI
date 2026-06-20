from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from prepos.application.knowledge.dto import KnowledgeSearchRequest
from prepos.application.knowledge.ports import KnowledgeSearchHit
from prepos.application.knowledge.services import KnowledgeSearchService
from prepos.core.config import Settings
from prepos.infrastructure.knowledge.embedding_provider import DeterministicEmbeddingProvider


class FakeKnowledgeRepository:
    async def vector_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        chunk_id = uuid4()
        return [(chunk_id, 0.91)]

    async def keyword_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        chunk_id = uuid4()
        return [(chunk_id, 0.75)]

    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> dict[UUID, KnowledgeSearchHit]:
        hits: dict[UUID, KnowledgeSearchHit] = {}
        for chunk_id in chunk_ids:
            hits[chunk_id] = KnowledgeSearchHit(
                chunk_id=chunk_id,
                content=f"content for {chunk_id}",
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=uuid4(),
                source_title="Sample Source",
                source_type="ncert",
                metadata_json={"exam_id": "upsc_cse"},
            )
        return hits


@pytest.mark.asyncio
async def test_search_service_returns_hybrid_results() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
    )
    service = KnowledgeSearchService(
        settings=settings,
        repository=FakeKnowledgeRepository(),  # type: ignore[arg-type]
        embedding_provider=DeterministicEmbeddingProvider(dimensions=settings.embedding_dims),
    )
    response = await service.search(
        tenant_id=uuid4(),
        request=KnowledgeSearchRequest(query="basic structure doctrine", exam_id="upsc_cse"),
    )
    assert response.query_embedding_model
    assert len(response.chunks) >= 1
    assert response.chunks[0].score > 0
