from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from prepos.application.knowledge.dto import KnowledgeSearchRequest
from prepos.application.knowledge.ports import KnowledgeSearchHit
from prepos.application.knowledge.services import KnowledgeSearchService
from prepos.core.config import Settings
from prepos.infrastructure.knowledge.embedding_provider import DeterministicEmbeddingProvider


class RecordingKnowledgeRepository:
    def __init__(self) -> None:
        self.last_published_after: datetime | None = None
        self.last_prefer_recency = False
        self._recent_id = uuid4()
        self._older_id = uuid4()

    async def vector_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        self.last_published_after = kwargs.get("published_after")  # type: ignore[assignment]
        return [(self._older_id, 0.8), (self._recent_id, 0.7)]

    async def keyword_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        return [(self._older_id, 0.6), (self._recent_id, 0.5)]

    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> dict[UUID, KnowledgeSearchHit]:
        now = datetime.now(UTC)
        return {
            self._recent_id: KnowledgeSearchHit(
                chunk_id=self._recent_id,
                content="Recent PIB release on climate policy.",
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=uuid4(),
                source_title="PIB Climate Update",
                source_type="pib",
                published_at=now - timedelta(days=3),
                source_authority="pib",
                metadata_json={},
            ),
            self._older_id: KnowledgeSearchHit(
                chunk_id=self._older_id,
                content="Older article on climate policy.",
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=uuid4(),
                source_title="Legacy CA Note",
                source_type="current_affairs",
                published_at=now - timedelta(days=400),
                source_authority="current_affairs",
                metadata_json={},
            ),
        }


@pytest.mark.asyncio
async def test_search_applies_date_filter_and_recency_ranking() -> None:
    repo = RecordingKnowledgeRepository()
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
    )
    service = KnowledgeSearchService(
        settings=settings,
        repository=repo,  # type: ignore[arg-type]
        embedding_provider=DeterministicEmbeddingProvider(dimensions=settings.embedding_dims),
    )

    response = await service.search(
        tenant_id=uuid4(),
        request=KnowledgeSearchRequest(
            query="climate policy update",
            exam_id="upsc_cse",
            source_types=["pib", "current_affairs"],
            published_after=date(2026, 1, 1),
            prefer_recency=True,
        ),
    )

    assert repo.last_published_after is not None
    assert len(response.chunks) >= 1
    assert response.chunks[0].source.source_type == "pib"
