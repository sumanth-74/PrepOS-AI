from __future__ import annotations

from uuid import uuid4

import pytest

from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import (
    KnowledgeAskRequest,
    KnowledgeSearchChunk,
    KnowledgeSearchResponse,
    KnowledgeSourceSummary,
)
from prepos.application.knowledge.evaluation_service import KnowledgeEvaluationService
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.knowledge.llm_ports import LLMCompletionResult, LLMProviderPort
from prepos.application.knowledge.rag_quality_service import RagQualityService
from prepos.core.config import Settings
from prepos.domain.knowledge.evaluation_metrics import citation_coverage_score, support_score
from tests.unit.test_evaluation_service import InMemoryRagQualityRepository


class PipelineSearchService:
    async def search(self, *, tenant_id: object, request: object) -> KnowledgeSearchResponse:
        del tenant_id, request
        chunk_id = uuid4()
        return KnowledgeSearchResponse(
            query_embedding_model="pipeline-embedding",
            chunks=[
                KnowledgeSearchChunk(
                    chunk_id=chunk_id,
                    content="Federalism divides legislative powers between centre and states.",
                    score=0.93,
                    vector_score=0.9,
                    keyword_score=0.85,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="Polity Notes",
                        source_type="ncert",
                    ),
                    metadata={},
                ),
                KnowledgeSearchChunk(
                    chunk_id=uuid4(),
                    content="Additional constitutional context on federal structure.",
                    score=0.82,
                    vector_score=0.8,
                    keyword_score=0.75,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="Constitution Digest",
                        source_type="book",
                    ),
                    metadata={},
                ),
                KnowledgeSearchChunk(
                    chunk_id=uuid4(),
                    content="More indexed reference on cooperative federalism.",
                    score=0.78,
                    vector_score=0.77,
                    keyword_score=0.7,
                    source=KnowledgeSourceSummary(
                        source_id=uuid4(),
                        title="Syllabus Notes",
                        source_type="syllabus",
                    ),
                    metadata={},
                ),
            ],
        )


class PipelineLLMProvider(LLMProviderPort):
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
            content=f"Federalism divides powers between centre and states. [{chunk_id}]",
            prompt_tokens=100,
            completion_tokens=30,
            model="pipeline-llm",
        )

    @property
    def model_name(self) -> str:
        return "pipeline-llm"


@pytest.mark.asyncio
async def test_rag_quality_pipeline_from_agent_to_dashboard() -> None:
    settings = Settings(
        secret_key="test-secret-key-for-prepos-backend-foundation-32chars-min",
        database_url="postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
        knowledge_relevance_min_score=0.15,
    )
    repo = InMemoryRagQualityRepository()
    evaluation_service = KnowledgeEvaluationService(repository=repo)  # type: ignore[arg-type]
    agent = KnowledgeAgentService(
        settings=settings,
        search_service=PipelineSearchService(),  # type: ignore[arg-type]
        llm_provider=PipelineLLMProvider(),
        evaluation_service=evaluation_service,
    )
    tenant_id = uuid4()

    response = await agent.ask(
        tenant_id=tenant_id,
        request=KnowledgeAskRequest(query="Explain federalism", exam_id="upsc_cse"),
    )

    assert response.answer != INSUFFICIENT_EVIDENCE_ANSWER
    assert response.citations
    assert repo.answer_rows

    dashboard = RagQualityService(repository=repo)  # type: ignore[arg-type]
    metrics = await dashboard.get_quality_dashboard(tenant_id=tenant_id, period_days=30)
    assert metrics.retrieval.evaluation_count == 1
    assert metrics.faithfulness.evaluation_count == 1
    assert metrics.citation_coverage.avg_citation_count >= 1.0

    csv_body = await dashboard.export_csv(tenant_id=tenant_id, period_days=30)
    assert "query,answer,citation_count" in csv_body or "id,query,answer" in csv_body


def test_quality_metric_functions_for_pipeline_answer() -> None:
    answer = "Federalism divides powers between centre and states."
    chunks = ["Federalism divides legislative powers between centre and states."]
    coverage = citation_coverage_score(answer=answer, citation_count=0)
    support = support_score(answer=answer, chunk_contents=chunks)
    assert coverage == 0.0
    assert support >= 50.0
