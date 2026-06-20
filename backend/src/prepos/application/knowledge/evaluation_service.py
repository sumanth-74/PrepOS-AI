from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import structlog

from prepos.application.knowledge.confidence import INSUFFICIENT_EVIDENCE_ANSWER
from prepos.application.knowledge.dto import KnowledgeSearchChunk
from prepos.application.knowledge.evaluation_ports import RagQualityRepositoryPort
from prepos.domain.knowledge.evaluation_metrics import (
    citation_coverage_score,
    hallucination_score,
    mean_reciprocal_rank,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    support_score,
)

logger = structlog.get_logger(__name__)


class KnowledgeEvaluationService:
    def __init__(self, *, repository: RagQualityRepositoryPort) -> None:
        self._repository = repository

    async def evaluate_answer(
        self,
        *,
        tenant_id: UUID,
        query: str,
        answer: str,
        confidence: str,
        citation_count: int,
        retrieved_chunks: list[KnowledgeSearchChunk],
        relevant_chunks: list[KnowledgeSearchChunk],
        source_types: list[str],
    ) -> dict[str, float | str | int]:
        eval_id = uuid4()
        logger.info(
            "rag_evaluation_started",
            query_id=str(eval_id),
            tenant_id=str(tenant_id),
            source_types=source_types,
        )

        retrieved_ids = [chunk.chunk_id for chunk in retrieved_chunks]
        relevant_ids = {chunk.chunk_id for chunk in relevant_chunks}
        retrieved_id_strs = [str(chunk_id) for chunk_id in retrieved_ids]
        relevant_id_strs = [str(chunk_id) for chunk_id in relevant_ids]

        primary_source_type = source_types[0] if len(source_types) == 1 else None
        now = datetime.now(UTC)

        query_eval = await self._repository.save_query_evaluation(
            tenant_id=tenant_id,
            query=query,
            source_type=primary_source_type,
            retrieved_chunk_ids=retrieved_id_strs,
            relevant_chunk_ids=relevant_id_strs,
            recall_at_5=recall_at_k(relevant_ids, retrieved_ids, 5),
            recall_at_8=recall_at_k(relevant_ids, retrieved_ids, 8),
            precision_at_5=precision_at_k(relevant_ids, retrieved_ids, 5),
            precision_at_8=precision_at_k(relevant_ids, retrieved_ids, 8),
            mrr=mean_reciprocal_rank(relevant_ids, retrieved_ids),
            ndcg=ndcg_at_k(relevant_ids, retrieved_ids, 8),
            created_at=now,
        )

        prompt_contents = [chunk.content for chunk in (relevant_chunks or retrieved_chunks)]
        coverage = citation_coverage_score(answer=answer, citation_count=citation_count)
        support = support_score(answer=answer, chunk_contents=prompt_contents)
        hallucination = hallucination_score(
            answer=answer,
            citation_coverage=coverage,
            support_score_value=support,
            citation_count=citation_count,
        )

        await self._repository.save_answer_evaluation(
            tenant_id=tenant_id,
            query=query,
            answer=answer,
            citation_count=citation_count,
            citation_coverage=coverage,
            support_score=support,
            hallucination_score=hallucination,
            confidence=confidence,
            source_types=source_types,
            query_evaluation_id=query_eval.id,
            created_at=now,
        )

        scores = {
            "citation_count": citation_count,
            "citation_coverage": coverage,
            "support_score": support,
            "hallucination_score": hallucination,
            "confidence": confidence,
        }

        logger.info(
            "knowledge_answer_evaluated",
            query_id=str(eval_id),
            tenant_id=str(tenant_id),
            source_types=source_types,
            **scores,
        )
        logger.info(
            "rag_evaluation_completed",
            query_id=str(eval_id),
            tenant_id=str(tenant_id),
            source_types=source_types,
            **scores,
        )

        if support < 40.0 and answer.strip() != INSUFFICIENT_EVIDENCE_ANSWER:
            logger.info(
                "rag_low_support",
                query_id=str(eval_id),
                tenant_id=str(tenant_id),
                source_types=source_types,
                support_score=support,
            )
        if hallucination >= 60.0:
            logger.info(
                "rag_high_hallucination",
                query_id=str(eval_id),
                tenant_id=str(tenant_id),
                source_types=source_types,
                hallucination_score=hallucination,
            )

        return scores
