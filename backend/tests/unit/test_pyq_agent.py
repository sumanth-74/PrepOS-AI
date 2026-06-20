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
    async def search(self, *, tenant_id: UUID, request: object) -> KnowledgeSearchResponse:
        del tenant_id, request
        chunk_id = uuid4()
        return KnowledgeSearchResponse(
            chunks=[
                KnowledgeSearchChunk(
                    chunk_id=chunk_id,
                    content="2023 GS2 PYQ on federalism.",
                    score=0.95,
                    vector_score=0.95,
                    keyword_score=0.8,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="UPSC PYQ 2023",
                        source_type="pyq",
                    ),
                    metadata={"year": 2023, "paper": "GS2"},
                ),
                KnowledgeSearchChunk(
                    chunk_id=uuid4(),
                    content="2021 GS2 PYQ on cooperative federalism.",
                    score=0.88,
                    vector_score=0.88,
                    keyword_score=0.7,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="UPSC PYQ 2021",
                        source_type="pyq",
                    ),
                    metadata={"year": 2021, "paper": "GS2"},
                ),
            ],
            query_embedding_model="test-model",
        )


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
            content=f"Federalism was tested in UPSC 2023 GS2. [{chunk_id}]",
            prompt_tokens=10,
            completion_tokens=5,
            model="fake-llm",
        )

    @property
    def model_name(self) -> str:
        return "fake-llm"


@pytest.mark.asyncio
async def test_knowledge_agent_pyq_mode_uses_pyq_grounding() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
        knowledge_relevance_min_score=0.1,
    )
    agent = KnowledgeAgentService(
        settings=settings,
        search_service=FakeSearchService(),  # type: ignore[arg-type]
        llm_provider=FakeLLMProvider(),
    )

    response = await agent.ask(
        tenant_id=uuid4(),
        request=KnowledgeAskRequest(
            query="Show PYQs on Federalism",
            exam_id="upsc_cse",
            pyq_mode=True,
            prefer_pyq=True,
            frequency_summary="PYQ frequency summary:\n- polity_federalism: 5 questions",
        ),
    )

    assert "2023" in response.answer
    assert response.citations
    assert response.confidence in {"medium", "high"}
