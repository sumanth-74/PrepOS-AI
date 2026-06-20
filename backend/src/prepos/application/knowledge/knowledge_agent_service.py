from __future__ import annotations

import time
from uuid import UUID

import structlog

from prepos.application.knowledge.citation_service import extract_citations
from prepos.application.knowledge.confidence import (
    INSUFFICIENT_EVIDENCE_ANSWER,
    filter_relevant_chunks,
    score_confidence,
    select_prompt_chunks,
)
from prepos.application.knowledge.dto import (
    KnowledgeAskRequest,
    KnowledgeAskResponse,
    KnowledgeSearchRequest,
)
from prepos.application.knowledge.llm_ports import LLMProviderPort
from prepos.application.knowledge.prompt_builder import build_grounded_prompt
from prepos.application.knowledge.services import KnowledgeSearchService
from prepos.core.config import Settings
from prepos.core.exceptions import ValidationError
from prepos.domain.knowledge.current_affairs import CURRENT_AFFAIRS_SOURCE_TYPES
from prepos.domain.knowledge.entities import KnowledgeSourceType

logger = structlog.get_logger(__name__)


class KnowledgeAgentService:
    def __init__(
        self,
        *,
        settings: Settings,
        search_service: KnowledgeSearchService,
        llm_provider: LLMProviderPort,
        evaluation_service: object | None = None,
    ) -> None:
        self._settings = settings
        self._search_service = search_service
        self._llm_provider = llm_provider
        self._evaluation_service = evaluation_service

    async def ask(
        self,
        *,
        tenant_id: UUID,
        request: KnowledgeAskRequest,
    ) -> KnowledgeAskResponse:
        query = request.query.strip()
        if not query:
            raise ValidationError("Query must not be empty.")

        logger.info(
            "knowledge_query_received",
            exam_id=request.exam_id,
            query_length=len(query),
            tenant_id=str(tenant_id),
        )

        search_query = query
        if request.retrieval_hints:
            hint_text = " ".join(hint.strip() for hint in request.retrieval_hints if hint.strip())
            if hint_text:
                search_query = f"{query} {hint_text}"

        prefer_recency = request.prefer_recency or request.current_affairs_mode
        prefer_pyq = request.prefer_pyq or request.pyq_mode
        source_types = list(request.source_types)
        if request.current_affairs_mode and not source_types:
            source_types = list(CURRENT_AFFAIRS_SOURCE_TYPES)
        if request.pyq_mode and not source_types:
            source_types = [KnowledgeSourceType.PYQ.value]

        retrieval_started = time.perf_counter()
        search_response = await self._search_service.search(
            tenant_id=tenant_id,
            request=KnowledgeSearchRequest(
                query=search_query,
                exam_id=request.exam_id,
                concept_ids=request.concept_ids,
                source_types=source_types,
                limit=request.limit,
                hybrid_alpha=request.hybrid_alpha,
                published_after=request.published_after,
                published_before=request.published_before,
                prefer_recency=prefer_recency,
                year_from=request.year_from,
                year_to=request.year_to,
                paper=request.paper,
                exam_stage=request.exam_stage,
                prefer_pyq=prefer_pyq,
            ),
        )
        retrieval_latency_ms = int((time.perf_counter() - retrieval_started) * 1000)

        relevant_chunks = filter_relevant_chunks(
            search_response.chunks,
            min_score=self._settings.knowledge_relevance_min_score,
        )
        prompt_chunks = select_prompt_chunks(
            relevant_chunks or search_response.chunks,
            limit=request.limit,
            prompt_max=self._settings.knowledge_ask_prompt_chunk_max,
        )
        confidence = score_confidence(len(relevant_chunks))

        logger.info(
            "knowledge_retrieval_completed",
            retrieval_latency_ms=retrieval_latency_ms,
            retrieved_chunks=len(search_response.chunks),
            relevant_chunks=len(relevant_chunks),
            prompt_chunks=len(prompt_chunks),
            tenant_id=str(tenant_id),
        )

        if not prompt_chunks:
            logger.info(
                "knowledge_low_confidence",
                reason="no_retrieved_chunks",
                confidence="low",
                tenant_id=str(tenant_id),
            )
            await self._record_evaluation(
                tenant_id=tenant_id,
                query=query,
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                confidence="low",
                citation_count=0,
                retrieved_chunks=search_response.chunks,
                relevant_chunks=relevant_chunks,
                source_types=source_types,
            )
            return KnowledgeAskResponse(
                answer=INSUFFICIENT_EVIDENCE_ANSWER,
                citations=[],
                confidence="low",
            )

        if len(relevant_chunks) <= 1:
            logger.info(
                "knowledge_low_confidence",
                reason="insufficient_relevant_chunks",
                relevant_chunks=len(relevant_chunks),
                confidence=confidence,
                tenant_id=str(tenant_id),
            )

        system_prompt, user_prompt = build_grounded_prompt(
            query=query,
            chunks=prompt_chunks,
            student_context=request.student_context,
            current_affairs_mode=request.current_affairs_mode,
            pyq_mode=request.pyq_mode,
            frequency_summary=request.frequency_summary,
        )
        generation_started = time.perf_counter()
        completion = await self._llm_provider.complete(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            temperature=0.0,
            max_tokens=self._settings.llm_max_completion_tokens,
        )
        generation_latency_ms = int((time.perf_counter() - generation_started) * 1000)

        citations = extract_citations(completion.content, context_chunks=prompt_chunks)
        if completion.content.strip() == INSUFFICIENT_EVIDENCE_ANSWER:
            confidence = "low"

        logger.info(
            "knowledge_generation_completed",
            generation_latency_ms=generation_latency_ms,
            retrieval_latency_ms=retrieval_latency_ms,
            prompt_tokens=completion.prompt_tokens,
            completion_tokens=completion.completion_tokens,
            citation_count=len(citations),
            confidence=confidence,
            model=completion.model,
            tenant_id=str(tenant_id),
        )

        if confidence == "low":
            logger.info(
                "knowledge_low_confidence",
                reason="confidence_scoring",
                relevant_chunks=len(relevant_chunks),
                confidence=confidence,
                tenant_id=str(tenant_id),
            )

        await self._record_evaluation(
            tenant_id=tenant_id,
            query=query,
            answer=completion.content.strip(),
            confidence=confidence,
            citation_count=len(citations),
            retrieved_chunks=search_response.chunks,
            relevant_chunks=relevant_chunks,
            source_types=source_types or _source_types_from_chunks(prompt_chunks),
        )

        return KnowledgeAskResponse(
            answer=completion.content.strip(),
            citations=citations,
            confidence=confidence,
        )

    async def _record_evaluation(
        self,
        *,
        tenant_id: UUID,
        query: str,
        answer: str,
        confidence: str,
        citation_count: int,
        retrieved_chunks: list,
        relevant_chunks: list,
        source_types: list[str],
    ) -> None:
        if self._evaluation_service is None:
            return
        from prepos.application.knowledge.evaluation_service import KnowledgeEvaluationService

        assert isinstance(self._evaluation_service, KnowledgeEvaluationService)
        await self._evaluation_service.evaluate_answer(
            tenant_id=tenant_id,
            query=query,
            answer=answer,
            confidence=confidence,
            citation_count=citation_count,
            retrieved_chunks=retrieved_chunks,
            relevant_chunks=relevant_chunks,
            source_types=source_types,
        )


def _source_types_from_chunks(chunks: list) -> list[str]:
    seen: list[str] = []
    for chunk in chunks:
        source_type = chunk.source.source_type
        if source_type not in seen:
            seen.append(source_type)
    return seen
