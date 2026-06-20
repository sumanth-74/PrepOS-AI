from __future__ import annotations

from prepos.application.pyq.dto import (
    PyqCoverageResponse,
    PyqIndexingMetricsResponse,
    PyqMappingReviewItem,
    PyqQuestionResponse,
    PyqSearchRequest,
    PyqSearchResponse,
    PyqTrendItem,
    PyqTrendsResponse,
)
from prepos.application.pyq.ports import PyqQuestionRecord, PyqRepositoryPort, PyqStatisticRecord
from prepos.application.pyq.pyq_ingestion_service import PYQIngestionService, _to_response
from prepos.application.knowledge.dto import KnowledgeSearchRequest
from prepos.application.knowledge.ports import KnowledgeRepositoryPort
from prepos.application.knowledge.services import KnowledgeSearchService
from prepos.core.exceptions import NotFoundError
from prepos.domain.knowledge.entities import KnowledgeSourceType
from prepos.domain.knowledge.pyq import is_pyq_boost_query
from uuid import UUID


class PyqService:
    def __init__(
        self,
        *,
        repository: PyqRepositoryPort,
        knowledge_repository: KnowledgeRepositoryPort,
        ingestion_service: PYQIngestionService,
        search_service: KnowledgeSearchService,
    ) -> None:
        self._repository = repository
        self._knowledge_repository = knowledge_repository
        self._ingestion_service = ingestion_service
        self._search_service = search_service

    async def upload(
        self,
        *,
        tenant_id: UUID | None,
        request: object,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> object:
        from prepos.application.pyq.dto import CreatePyqUploadRequest, PyqUploadResponse

        assert isinstance(request, CreatePyqUploadRequest)
        return await self._ingestion_service.ingest_upload(
            tenant_id=tenant_id,
            request=request,
            file_name=file_name,
            mime_type=mime_type,
            file_bytes=file_bytes,
        )

    async def get_question(
        self,
        *,
        tenant_id: UUID | None,
        question_id: UUID,
    ) -> PyqQuestionResponse:
        record = await self._repository.get_question_by_id(question_id, tenant_id=tenant_id)
        if record is None:
            raise NotFoundError("PYQ question not found.")
        return _to_response(record)

    async def search(
        self,
        *,
        tenant_id: UUID,
        request: PyqSearchRequest,
    ) -> PyqSearchResponse:
        prefer_pyq = request.prefer_pyq or is_pyq_boost_query(request.query)
        search_response = await self._search_service.search(
            tenant_id=tenant_id,
            request=KnowledgeSearchRequest(
                query=request.query,
                exam_id=request.exam_id,
                concept_ids=request.concept_ids,
                source_types=[KnowledgeSourceType.PYQ.value],
                limit=request.limit,
                year_from=request.year_from,
                year_to=request.year_to,
                paper=request.paper,
                exam_stage=request.exam_stage,
                prefer_pyq=prefer_pyq,
            ),
        )
        return PyqSearchResponse(
            chunks=search_response.chunks,
            query_embedding_model=search_response.query_embedding_model,
            pyq_boost_applied=prefer_pyq,
        )

    async def get_trends(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
        limit: int = 20,
    ) -> PyqTrendsResponse:
        statistics = await self._repository.list_statistics(exam_id=exam_id, limit=limit)
        total = await self._repository.count_questions(tenant_id=tenant_id, exam_id=exam_id)
        return PyqTrendsResponse(
            exam_id=exam_id,
            trends=[_to_trend_item(stat) for stat in statistics],
            total_questions=total,
        )

    async def get_coverage(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
    ) -> PyqCoverageResponse:
        questions = await self._repository.list_questions(
            tenant_id=tenant_id,
            exam_id=exam_id,
            limit=500,
        )
        mapped = sum(1 for question in questions if question.concept_ids)
        unmapped = len(questions) - mapped
        statistics = await self._repository.list_statistics(exam_id=exam_id, limit=10)
        return PyqCoverageResponse(
            exam_id=exam_id,
            total_questions=len(questions),
            mapped_questions=mapped,
            unmapped_questions=unmapped,
            top_concepts=[_to_trend_item(stat) for stat in statistics],
        )

    async def list_mapping_review(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> list[PyqMappingReviewItem]:
        rows = await self._repository.list_mappings_for_review(
            tenant_id=tenant_id,
            exam_id=exam_id,
            limit=limit,
        )
        items: list[PyqMappingReviewItem] = []
        for question, mappings in rows:
            items.append(
                PyqMappingReviewItem(
                    question=_to_response(question),
                    mappings=[
                        {
                            "concept_id": mapping.concept_id,
                            "confidence_score": mapping.confidence_score,
                        }
                        for mapping in mappings
                    ],
                )
            )
        return items

    async def get_indexing_metrics(
        self,
        *,
        tenant_id: UUID | None,
    ) -> PyqIndexingMetricsResponse:
        total_questions = await self._repository.count_questions(tenant_id=tenant_id)
        indexed_questions_stmt = await self._repository.list_questions(
            tenant_id=tenant_id,
            limit=10_000,
        )
        indexed_questions = sum(1 for q in indexed_questions_stmt if q.knowledge_chunk_id is not None)
        knowledge_metrics = await self._knowledge_repository.get_indexing_metrics(
            tenant_id=tenant_id,
            source_types=(KnowledgeSourceType.PYQ.value,),
        )
        return PyqIndexingMetricsResponse(
            total_questions=total_questions,
            indexed_questions=indexed_questions,
            total_knowledge_chunks=knowledge_metrics["total_chunks"],
            indexed_knowledge_chunks=knowledge_metrics["indexed_chunks"],
        )

    async def build_frequency_summary(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
        concept_ids: list[str],
        limit: int = 5,
    ) -> str:
        statistics = await self._repository.list_statistics(exam_id=exam_id, limit=100)
        if concept_ids:
            selected = [stat for stat in statistics if stat.concept_id in concept_ids][:limit]
        else:
            selected = statistics[:limit]
        if not selected:
            return "No PYQ frequency statistics available yet."
        lines = ["PYQ frequency summary:"]
        for stat in selected:
            lines.append(
                f"- {stat.concept_id}: {stat.pyq_count} questions "
                f"(frequency {stat.frequency_score}, trend {stat.trend_score})"
            )
        return "\n".join(lines)


def _to_trend_item(stat: PyqStatisticRecord) -> PyqTrendItem:
    return PyqTrendItem(
        concept_id=stat.concept_id,
        pyq_count=stat.pyq_count,
        first_appearance_year=stat.first_appearance_year,
        last_appearance_year=stat.last_appearance_year,
        frequency_score=stat.frequency_score,
        trend_score=stat.trend_score,
    )
