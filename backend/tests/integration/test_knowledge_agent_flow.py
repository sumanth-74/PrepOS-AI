from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from prepos.application.knowledge.dto import (
    KnowledgeAskRequest,
    KnowledgeSearchChunk,
    KnowledgeSearchResponse,
    KnowledgeSourceSummary,
)
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.knowledge.llm_ports import LLMCompletionResult, LLMProviderPort
from prepos.core.config import Settings


class FakeSearchService:
    def __init__(self, chunks: list[KnowledgeSearchChunk]) -> None:
        self._chunks = chunks

    async def search(self, *, tenant_id: UUID, request: object) -> KnowledgeSearchResponse:
        del tenant_id, request
        return KnowledgeSearchResponse(chunks=self._chunks, query_embedding_model="test-embedding")


class FakeLLMProvider(LLMProviderPort):
    async def complete(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.0,
        max_tokens: int | None = None,
    ) -> LLMCompletionResult:
        del system_prompt, temperature, max_tokens
        chunk_id = user_prompt.split("chunk_id=")[1].split()[0]
        return LLMCompletionResult(
            content=f"The doctrine limits amending power. [{chunk_id}]",
            prompt_tokens=120,
            completion_tokens=40,
            model="fake-llm",
        )

    @property
    def model_name(self) -> str:
        return "fake-llm"


def _chunk(score: float) -> KnowledgeSearchChunk:
    chunk_id = uuid4()
    return KnowledgeSearchChunk(
        chunk_id=chunk_id,
        content="Basic structure doctrine summary",
        score=score,
        vector_score=score,
        keyword_score=score,
        source=KnowledgeSourceSummary(source_id=uuid4(), title="Polity Notes", source_type="ncert"),
        metadata={},
    )


@pytest.mark.asyncio
async def test_knowledge_agent_returns_grounded_answer_with_citations() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
        knowledge_relevance_min_score=0.15,
    )
    chunks = [_chunk(0.9), _chunk(0.85), _chunk(0.8)]
    service = KnowledgeAgentService(
        settings=settings,
        search_service=FakeSearchService(chunks),  # type: ignore[arg-type]
        llm_provider=FakeLLMProvider(),
    )

    response = await service.ask(
        tenant_id=uuid4(),
        request=KnowledgeAskRequest(
            query="Explain the basic structure doctrine",
            exam_id="upsc_cse",
            limit=8,
        ),
    )

    assert response.answer
    assert response.confidence == "high"
    assert len(response.citations) >= 1
    assert response.citations[0].source_title == "Polity Notes"


@pytest.mark.asyncio
async def test_knowledge_agent_returns_insufficient_evidence_without_chunks() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
    )
    service = KnowledgeAgentService(
        settings=settings,
        search_service=FakeSearchService([]),  # type: ignore[arg-type]
        llm_provider=FakeLLMProvider(),
    )

    response = await service.ask(
        tenant_id=uuid4(),
        request=KnowledgeAskRequest(query="Unknown topic", exam_id="upsc_cse"),
    )

    assert "don't have enough indexed content" in response.answer.lower()
    assert response.confidence == "low"
    assert response.citations == []
