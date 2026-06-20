from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from prepos.application.knowledge.dto import KnowledgeSearchRequest
from prepos.application.knowledge.ports import KnowledgeSearchHit
from prepos.application.knowledge.services import KnowledgeSearchService
from prepos.core.config import Settings
from prepos.domain.pyq.trends import PyqQuestionYearHit, compute_concept_statistics
from prepos.infrastructure.knowledge.embedding_provider import DeterministicEmbeddingProvider


class RecordingPyqRepository:
    def __init__(self) -> None:
        self.last_year_from: int | None = None
        self.last_paper: str | None = None
        self._pyq_id = uuid4()
        self._generic_id = uuid4()

    async def vector_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        self.last_year_from = kwargs.get("year_from")  # type: ignore[assignment]
        self.last_paper = kwargs.get("paper")  # type: ignore[assignment]
        return [(self._generic_id, 0.9), (self._pyq_id, 0.85)]

    async def keyword_search(self, **kwargs: object) -> list[tuple[UUID, float]]:
        return [(self._generic_id, 0.7), (self._pyq_id, 0.65)]

    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> dict[UUID, KnowledgeSearchHit]:
        return {
            self._pyq_id: KnowledgeSearchHit(
                chunk_id=self._pyq_id,
                content="PYQ on federalism from 2023 GS2 paper.",
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=uuid4(),
                source_title="UPSC PYQ 2023",
                source_type="pyq",
                metadata_json={"year": 2023, "paper": "GS2", "concept_ids": ["polity_federalism"]},
            ),
            self._generic_id: KnowledgeSearchHit(
                chunk_id=self._generic_id,
                content="Generic note on federalism.",
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=uuid4(),
                source_title="NCERT Note",
                source_type="ncert",
                metadata_json={},
            ),
        }


@pytest.mark.asyncio
async def test_pyq_search_applies_filters_and_boosts_pyq_chunks() -> None:
    repo = RecordingPyqRepository()
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
            query="show previous year questions on federalism",
            exam_id="upsc_cse",
            source_types=["pyq"],
            year_from=2020,
            paper="GS2",
            prefer_pyq=True,
        ),
    )

    assert repo.last_year_from == 2020
    assert repo.last_paper == "GS2"
    assert response.chunks
    assert response.chunks[0].source.source_type == "pyq"


def test_trend_calculation_prefers_recent_concepts() -> None:
    hits = [
        PyqQuestionYearHit("polity_federalism", 2024, 1.0),
        PyqQuestionYearHit("polity_federalism", 2023, 1.0),
        PyqQuestionYearHit("polity_federalism", 2022, 1.0),
        PyqQuestionYearHit("polity_federalism", 2010, 1.0),
        PyqQuestionYearHit("economy_gst", 2010, 1.0),
    ]
    stats = compute_concept_statistics(hits=hits, reference_year=2026)
    federalism = next(item for item in stats if item.concept_id == "polity_federalism")
    gst = next(item for item in stats if item.concept_id == "economy_gst")
    assert federalism.pyq_count == 4
    assert federalism.trend_score > gst.trend_score
