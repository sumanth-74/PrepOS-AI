from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from prepos.application.knowledge.current_affairs_dto import (
    CreateCurrentAffairsArticleRequest,
    CurrentAffairsArticleListResponse,
    CurrentAffairsArticleResponse,
    CurrentAffairsIndexingMetricsResponse,
    CurrentAffairsSearchRequest,
    CurrentAffairsSearchResponse,
)
from prepos.application.knowledge.dto import CreateKnowledgeSourceRequest, KnowledgeSearchRequest
from prepos.application.knowledge.ports import KnowledgeRepositoryPort, KnowledgeSourceRecord
from prepos.application.knowledge.services import KnowledgeIngestionService, KnowledgeSearchService
from prepos.core.exceptions import NotFoundError, ValidationError
from prepos.domain.knowledge.concept_mapping import map_concepts_from_text
from prepos.domain.knowledge.current_affairs import CURRENT_AFFAIRS_SOURCE_TYPES, is_current_affairs_source_type


class CurrentAffairsIngestionService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepositoryPort,
        ingestion_service: KnowledgeIngestionService,
    ) -> None:
        self._repository = repository
        self._ingestion_service = ingestion_service

    async def ingest_upload(
        self,
        *,
        tenant_id: UUID | None,
        request: CreateCurrentAffairsArticleRequest,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> CurrentAffairsArticleResponse:
        if not is_current_affairs_source_type(request.source_type):
            raise ValidationError(
                "Unsupported current affairs source type.",
                details={"source_type": request.source_type},
            )

        text_preview = file_bytes.decode("utf-8", errors="ignore")[:2000]
        mapped_concepts = map_concepts_from_text(title=request.title, content_preview=text_preview)
        concept_ids = list(dict.fromkeys([*request.concept_ids, *mapped_concepts]))
        source_authority = request.source_authority or request.source_type

        knowledge_request = CreateKnowledgeSourceRequest(
            exam_id=request.exam_id,
            source_type=request.source_type,
            title=request.title,
            catalog_version=request.catalog_version,
            subject_id=request.subject_id,
            topic_id=request.topic_id,
            concept_ids=concept_ids,
            metadata={
                **request.metadata,
                "published_at": request.published_at.isoformat() if request.published_at else None,
                "source_authority": source_authority,
                "exam_stage": request.exam_stage,
                "importance": request.importance,
            },
        )

        source = await self._ingestion_service.ingest_upload(
            tenant_id=tenant_id,
            request=knowledge_request,
            file_name=file_name,
            mime_type=mime_type,
            file_bytes=file_bytes,
        )

        await self._repository.update_current_affairs_metadata(
            source.id,
            published_at=request.published_at,
            source_authority=source_authority,
            exam_stage=request.exam_stage,
            importance=request.importance,
        )
        refreshed = await self._repository.get_source_by_id(source.id, tenant_id=tenant_id)
        if refreshed is None:
            raise NotFoundError("Current affairs article not found after ingestion.")
        return _to_article_response(refreshed)


class CurrentAffairsService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepositoryPort,
        ingestion_service: CurrentAffairsIngestionService,
        search_service: KnowledgeSearchService,
    ) -> None:
        self._repository = repository
        self._ingestion_service = ingestion_service
        self._search_service = search_service

    async def upload_article(
        self,
        *,
        tenant_id: UUID | None,
        request: CreateCurrentAffairsArticleRequest,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> CurrentAffairsArticleResponse:
        return await self._ingestion_service.ingest_upload(
            tenant_id=tenant_id,
            request=request,
            file_name=file_name,
            mime_type=mime_type,
            file_bytes=file_bytes,
        )

    async def list_articles(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> CurrentAffairsArticleListResponse:
        sources = await self._repository.list_sources(
            tenant_id=tenant_id,
            exam_id=exam_id,
            source_types=tuple(CURRENT_AFFAIRS_SOURCE_TYPES),
            limit=limit,
            offset=offset,
        )
        return CurrentAffairsArticleListResponse(
            articles=[_to_article_response(source) for source in sources],
            total=len(sources),
        )

    async def get_article(
        self,
        *,
        tenant_id: UUID | None,
        article_id: UUID,
    ) -> CurrentAffairsArticleResponse:
        source = await self._repository.get_source_by_id(article_id, tenant_id=tenant_id)
        if source is None or not is_current_affairs_source_type(source.source_type):
            raise NotFoundError("Current affairs article not found.")
        return _to_article_response(source)

    async def search(
        self,
        *,
        tenant_id: UUID,
        request: CurrentAffairsSearchRequest,
    ) -> CurrentAffairsSearchResponse:
        source_types = request.source_types or list(CURRENT_AFFAIRS_SOURCE_TYPES)
        search_response = await self._search_service.search(
            tenant_id=tenant_id,
            request=KnowledgeSearchRequest(
                query=request.query,
                exam_id=request.exam_id,
                concept_ids=request.concept_ids,
                source_types=source_types,
                limit=request.limit,
                published_after=request.published_after,
                published_before=request.published_before,
                prefer_recency=request.prefer_recency,
            ),
        )
        return CurrentAffairsSearchResponse(
            chunks=search_response.chunks,
            query_embedding_model=search_response.query_embedding_model,
            recency_boost_applied=request.prefer_recency,
        )

    async def get_indexing_metrics(
        self,
        *,
        tenant_id: UUID | None,
    ) -> CurrentAffairsIndexingMetricsResponse:
        metrics = await self._repository.get_indexing_metrics(
            tenant_id=tenant_id,
            source_types=tuple(CURRENT_AFFAIRS_SOURCE_TYPES),
        )
        return CurrentAffairsIndexingMetricsResponse(
            total_articles=metrics["total_sources"],
            active_articles=metrics["active_sources"],
            processing_articles=metrics["processing_sources"],
            failed_articles=metrics["failed_sources"],
            total_chunks=metrics["total_chunks"],
            indexed_chunks=metrics["indexed_chunks"],
        )


def _to_article_response(source: KnowledgeSourceRecord) -> CurrentAffairsArticleResponse:
    metadata = source.metadata_json or {}
    concept_ids_raw = metadata.get("concept_ids", [])
    concept_ids = [str(item) for item in concept_ids_raw] if isinstance(concept_ids_raw, list) else []
    return CurrentAffairsArticleResponse(
        id=source.id,
        tenant_id=source.tenant_id,
        exam_id=source.exam_id,
        source_type=source.source_type,
        title=source.title,
        status=source.status,
        published_at=source.published_at,
        source_authority=source.source_authority,
        exam_stage=source.exam_stage,
        importance=source.importance,
        chunk_count=source.chunk_count,
        indexed_chunk_count=source.indexed_chunk_count,
        concept_ids=concept_ids,
        metadata=metadata,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )
