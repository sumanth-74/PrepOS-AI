from __future__ import annotations

import json
from pathlib import Path
from uuid import UUID, uuid4

import pytest

from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import (
    KnowledgeAskRequest,
    KnowledgeSearchChunk,
    KnowledgeSearchResponse,
    KnowledgeSourceSummary,
)
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.knowledge.llm_ports import LLMCompletionResult, LLMProviderPort
from prepos.core.config import Settings

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_questions.json"


class EvalSearchService:
    async def search(self, *, tenant_id: UUID, request: object) -> KnowledgeSearchResponse:
        del tenant_id, request
        chunk_id = uuid4()
        return KnowledgeSearchResponse(
            query_embedding_model="eval-embedding",
            chunks=[
                KnowledgeSearchChunk(
                    chunk_id=chunk_id,
                    content="Indexed UPSC polity content for evaluation.",
                    score=0.92,
                    vector_score=0.9,
                    keyword_score=0.85,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="UPSC Eval Corpus",
                        source_type="ncert",
                    ),
                    metadata={"exam_id": "upsc_cse"},
                ),
                KnowledgeSearchChunk(
                    chunk_id=uuid4(),
                    content="Supporting constitutional context.",
                    score=0.81,
                    vector_score=0.8,
                    keyword_score=0.75,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="Constitution Notes",
                        source_type="book",
                    ),
                    metadata={"exam_id": "upsc_cse"},
                ),
                KnowledgeSearchChunk(
                    chunk_id=uuid4(),
                    content="Additional indexed reference.",
                    score=0.77,
                    vector_score=0.76,
                    keyword_score=0.7,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="Reference Material",
                        source_type="syllabus",
                    ),
                    metadata={"exam_id": "upsc_cse"},
                ),
            ],
        )


class EvalLLMProvider(LLMProviderPort):
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
            content=f"Grounded UPSC answer based on indexed content. [{chunk_id}]",
            prompt_tokens=150,
            completion_tokens=45,
            model="eval-llm",
        )

    @property
    def model_name(self) -> str:
        return "eval-llm"


@pytest.mark.parametrize("case", json.loads(GOLDEN_PATH.read_text(encoding="utf-8")))
@pytest.mark.asyncio
async def test_golden_knowledge_questions_generate_cited_answers(case: dict[str, str]) -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
    )
    service = KnowledgeAgentService(
        settings=settings,
        search_service=EvalSearchService(),  # type: ignore[arg-type]
        llm_provider=EvalLLMProvider(),
    )

    response = await service.ask(
        tenant_id=uuid4(),
        request=KnowledgeAskRequest(query=case["query"], exam_id=case["exam_id"], limit=8),
    )

    assert response.answer
    assert response.answer != INSUFFICIENT_EVIDENCE_ANSWER
    assert len(response.citations) >= 1
    assert response.confidence in {"high", "medium", "low"}
    assert "[" in response.answer and "]" in response.answer
