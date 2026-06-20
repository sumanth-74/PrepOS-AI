from __future__ import annotations

import hashlib
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import structlog

from prepos.application.knowledge.dto import (
    CreateKnowledgeSourceRequest,
    KnowledgeIndexingMetricsResponse,
    KnowledgeSearchChunk,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
    KnowledgeSourceListResponse,
    KnowledgeSourceResponse,
    KnowledgeSourceSummary,
)
from prepos.application.knowledge.ports import (
    KnowledgeRepositoryPort,
    KnowledgeSourceRecord,
    KnowledgeStoragePort,
)
from prepos.core.config import Settings
from prepos.core.exceptions import ConflictError, NotFoundError, ValidationError
from prepos.domain.knowledge.chunking import chunk_text
from prepos.domain.knowledge.current_affairs import apply_ranking_boosts
from prepos.domain.knowledge.pyq import apply_pyq_ranking_boost, is_pyq_boost_query
from prepos.domain.knowledge.entities import KnowledgeSourceStatus
from prepos.domain.knowledge.rrf import reciprocal_rank_fusion

logger = structlog.get_logger(__name__)

_TEXT_MIME_TYPES = {
    "text/plain",
    "text/markdown",
    "text/x-markdown",
    "application/octet-stream",
}


class KnowledgeIngestionService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: KnowledgeRepositoryPort,
        storage: KnowledgeStoragePort,
        embed_task: object | None = None,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._storage = storage
        self._embed_task = embed_task

    async def ingest_upload(
        self,
        *,
        tenant_id: UUID | None,
        request: CreateKnowledgeSourceRequest,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> KnowledgeSourceResponse:
        if not file_bytes:
            raise ValidationError("Uploaded file is empty.")

        content_hash = hashlib.sha256(file_bytes).hexdigest()
        source_id = uuid4()
        started_at = datetime.now(UTC)
        source_created = False

        try:
            external_uri = await self._storage.save_upload(
                tenant_id=tenant_id,
                source_id=source_id,
                file_name=file_name,
                content=file_bytes,
            )
            source = await self._repository.create_source(
                tenant_id=tenant_id,
                exam_id=request.exam_id,
                source_type=request.source_type,
                title=request.title,
                external_uri=external_uri,
                content_hash=content_hash,
                catalog_version=request.catalog_version,
                status=KnowledgeSourceStatus.PROCESSING.value,
                file_name=file_name,
                mime_type=mime_type,
                metadata_json={
                    **request.metadata,
                    "subject_id": request.subject_id,
                    "topic_id": request.topic_id,
                    "concept_ids": request.concept_ids,
                },
                source_id=source_id,
            )
            source_created = True
            source_id = source.id

            await self._repository.update_source_status(
                source_id,
                status=KnowledgeSourceStatus.PROCESSING.value,
                ingestion_started_at=started_at,
            )

            text = self._extract_text(file_bytes=file_bytes, mime_type=mime_type, file_name=file_name)
            chunks = chunk_text(
                text,
                chunk_size_tokens=self._settings.knowledge_chunk_size_tokens,
                overlap_tokens=self._settings.knowledge_chunk_overlap_tokens,
            )
            if not chunks:
                raise ValidationError("No text chunks produced from uploaded content.")

            chunk_rows = [
                (
                    chunk.chunk_index,
                    chunk.content,
                    chunk.token_count,
                    self._chunk_metadata(request=request, tenant_id=tenant_id),
                )
                for chunk in chunks
            ]
            await self._repository.replace_chunks(source_id, chunk_rows)
            await self._repository.update_source_status(
                source_id,
                status=KnowledgeSourceStatus.PROCESSING.value,
                chunk_count=len(chunks),
            )

            if self._embed_task is not None:
                self._embed_task.delay(str(source_id))

            refreshed = await self._repository.get_source_by_id(source_id, tenant_id=tenant_id)
            if refreshed is None:
                raise NotFoundError("Knowledge source not found after ingestion.")
            logger.info(
                "knowledge_ingestion_started",
                source_id=str(source_id),
                chunk_count=len(chunks),
                tenant_id=str(tenant_id) if tenant_id else None,
            )
            return _to_source_response(refreshed)
        except ConflictError:
            raise
        except Exception as exc:
            if source_created:
                await self._repository.update_source_status(
                    source_id,
                    status=KnowledgeSourceStatus.FAILED.value,
                    last_error=str(exc),
                    ingestion_failure_count=1,
                    ingestion_completed_at=datetime.now(UTC),
                )
            logger.exception(
                "knowledge_ingestion_failed",
                source_id=str(source_id),
                error=str(exc),
            )
            raise ValidationError(f"Ingestion failed: {exc}") from exc

    def _extract_text(self, *, file_bytes: bytes, mime_type: str | None, file_name: str) -> str:
        normalized_mime = (mime_type or "").lower()
        if normalized_mime and normalized_mime not in _TEXT_MIME_TYPES and not file_name.lower().endswith(
            (".txt", ".md", ".markdown")
        ):
            raise ValidationError(
                f"Unsupported file type '{mime_type}'. Upload plain text or markdown for Phase 1."
            )
        try:
            return file_bytes.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValidationError("Uploaded file must be UTF-8 encoded text.") from exc

    def _chunk_metadata(
        self,
        *,
        request: CreateKnowledgeSourceRequest,
        tenant_id: UUID | None,
    ) -> dict[str, object]:
        return {
            "exam_id": request.exam_id,
            "tenant_id": str(tenant_id) if tenant_id else None,
            "subject_id": request.subject_id,
            "topic_id": request.topic_id,
            "concept_ids": request.concept_ids,
            "catalog_version": request.catalog_version,
        }


class KnowledgeEmbeddingService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: KnowledgeRepositoryPort,
        embedding_provider: object,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._embedding_provider = embedding_provider

    async def embed_pending_chunks(self, source_id: UUID) -> None:
        from prepos.application.knowledge.ports import EmbeddingProviderPort

        provider = self._embedding_provider
        assert isinstance(provider, EmbeddingProviderPort)

        source = await self._repository.get_source_by_id(source_id, tenant_id=None)
        if source is None:
            raise NotFoundError("Knowledge source not found.")

        indexed = source.indexed_chunk_count
        failures = source.embedding_failure_count

        while True:
            pending = await self._repository.list_chunks_without_embeddings(
                source_id,
                embedding_model=provider.model_name,
                limit=self._settings.embedding_batch_size,
            )
            if not pending:
                break

            texts = [chunk.content for chunk in pending]
            try:
                vectors = await provider.embed_texts(texts)
            except Exception as exc:
                failures += len(pending)
                await self._repository.update_source_status(
                    source_id,
                    status=KnowledgeSourceStatus.FAILED.value,
                    last_error=str(exc),
                    embedding_failure_count=failures,
                )
                logger.exception(
                    "knowledge_embedding_failed",
                    source_id=str(source_id),
                    batch_size=len(pending),
                )
                raise

            await self._repository.upsert_embeddings(
                chunk_ids=[chunk.id for chunk in pending],
                embedding_model=provider.model_name,
                embedding_dims=provider.dimensions,
                embeddings=vectors,
            )
            indexed += len(pending)
            await self._repository.update_source_status(
                source_id,
                status=KnowledgeSourceStatus.PROCESSING.value,
                indexed_chunk_count=indexed,
            )

        final_status = (
            KnowledgeSourceStatus.ACTIVE.value
            if indexed >= source.chunk_count and source.chunk_count > 0
            else KnowledgeSourceStatus.FAILED.value
        )
        await self._repository.update_source_status(
            source_id,
            status=final_status,
            indexed_chunk_count=indexed,
            ingestion_completed_at=datetime.now(UTC),
        )
        logger.info(
            "knowledge_indexing_completed",
            source_id=str(source_id),
            indexed_chunks=indexed,
            embedding_failures=failures,
        )


class KnowledgeSearchService:
    def __init__(
        self,
        *,
        settings: Settings,
        repository: KnowledgeRepositoryPort,
        embedding_provider: object,
    ) -> None:
        self._settings = settings
        self._repository = repository
        self._embedding_provider = embedding_provider

    async def search(
        self,
        *,
        tenant_id: UUID,
        request: KnowledgeSearchRequest,
    ) -> KnowledgeSearchResponse:
        from prepos.application.knowledge.ports import EmbeddingProviderPort

        provider = self._embedding_provider
        assert isinstance(provider, EmbeddingProviderPort)

        limit = request.limit or self._settings.knowledge_search_default_limit
        source_types = tuple(request.source_types) if request.source_types else None
        concept_ids = tuple(request.concept_ids) if request.concept_ids else None
        published_after, published_before = _published_bounds(
            request.published_after,
            request.published_before,
        )

        query_vectors = await provider.embed_texts([request.query])
        vector_hits = await self._repository.vector_search(
            query_embedding=query_vectors[0],
            embedding_model=provider.model_name,
            tenant_id=tenant_id,
            exam_id=request.exam_id,
            source_types=source_types,
            concept_ids=concept_ids,
            limit=limit * 3,
            published_after=published_after,
            published_before=published_before,
            year_from=request.year_from,
            year_to=request.year_to,
            paper=request.paper,
            exam_stage=request.exam_stage,
        )
        keyword_hits = await self._repository.keyword_search(
            query=request.query,
            tenant_id=tenant_id,
            exam_id=request.exam_id,
            source_types=source_types,
            concept_ids=concept_ids,
            limit=limit * 3,
            published_after=published_after,
            published_before=published_before,
            year_from=request.year_from,
            year_to=request.year_to,
            paper=request.paper,
            exam_stage=request.exam_stage,
        )

        fused = reciprocal_rank_fusion(
            [vector_hits, keyword_hits],
            k=self._settings.knowledge_rrf_k,
        )
        if not fused:
            return KnowledgeSearchResponse(
                chunks=[],
                query_embedding_model=provider.model_name,
            )

        candidate_ids = [chunk_id for chunk_id, _, _, _ in fused[: limit * 2]]
        hit_map = await self._repository.get_chunks_by_ids(candidate_ids)

        ranked: list[tuple[UUID, float, float, float]] = []
        prefer_pyq = request.prefer_pyq or is_pyq_boost_query(request.query)
        for chunk_id, fused_score, vector_part, keyword_part in fused:
            hit = hit_map.get(chunk_id)
            if hit is None:
                continue
            adjusted = apply_ranking_boosts(
                base_score=fused_score,
                published_at=hit.published_at,
                source_authority=hit.source_authority,
                source_type=hit.source_type,
                prefer_recency=request.prefer_recency,
            )
            adjusted = apply_pyq_ranking_boost(
                base_score=adjusted,
                source_type=hit.source_type,
                query=request.query,
                prefer_pyq=prefer_pyq,
            )
            ranked.append((chunk_id, adjusted, vector_part, keyword_part))

        ranked.sort(key=lambda item: item[1], reverse=True)
        top_ranked = ranked[:limit]
        if not top_ranked:
            return KnowledgeSearchResponse(
                chunks=[],
                query_embedding_model=provider.model_name,
            )

        max_score = max(score for _, score, _, _ in top_ranked) or 1.0
        chunks: list[KnowledgeSearchChunk] = []
        for chunk_id, fused_score, vector_part, keyword_part in top_ranked:
            hit = hit_map[chunk_id]
            chunks.append(
                KnowledgeSearchChunk(
                    chunk_id=hit.chunk_id,
                    content=hit.content,
                    score=round(fused_score / max_score, 4),
                    vector_score=round(vector_part / max_score, 4),
                    keyword_score=round(keyword_part / max_score, 4),
                    source=KnowledgeSourceSummary(
                        source_id=hit.source_id,
                        title=hit.source_title,
                        source_type=hit.source_type,
                        published_at=hit.published_at,
                        source_authority=hit.source_authority,
                    ),
                    metadata=hit.metadata_json,
                )
            )

        return KnowledgeSearchResponse(
            chunks=chunks,
            query_embedding_model=provider.model_name,
        )


class KnowledgeAdminService:
    def __init__(
        self,
        *,
        repository: KnowledgeRepositoryPort,
        ingestion_service: KnowledgeIngestionService,
    ) -> None:
        self._repository = repository
        self._ingestion_service = ingestion_service

    async def create_source(
        self,
        *,
        tenant_id: UUID | None,
        request: CreateKnowledgeSourceRequest,
        file_name: str,
        mime_type: str | None,
        file_bytes: bytes,
    ) -> KnowledgeSourceResponse:
        return await self._ingestion_service.ingest_upload(
            tenant_id=tenant_id,
            request=request,
            file_name=file_name,
            mime_type=mime_type,
            file_bytes=file_bytes,
        )

    async def list_sources(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> KnowledgeSourceListResponse:
        sources = await self._repository.list_sources(
            tenant_id=tenant_id,
            exam_id=exam_id,
            limit=limit,
            offset=offset,
        )
        return KnowledgeSourceListResponse(
            sources=[_to_source_response(source) for source in sources],
            total=len(sources),
        )

    async def get_source(
        self,
        *,
        tenant_id: UUID | None,
        source_id: UUID,
    ) -> KnowledgeSourceResponse:
        source = await self._repository.get_source_by_id(source_id, tenant_id=tenant_id)
        if source is None:
            raise NotFoundError("Knowledge source not found.")
        return _to_source_response(source)

    async def get_indexing_metrics(self, *, tenant_id: UUID | None) -> KnowledgeIndexingMetricsResponse:
        metrics = await self._repository.get_indexing_metrics(tenant_id=tenant_id)
        return KnowledgeIndexingMetricsResponse(**metrics)


def _to_source_response(source: KnowledgeSourceRecord) -> KnowledgeSourceResponse:
    return KnowledgeSourceResponse(
        id=source.id,
        tenant_id=source.tenant_id,
        exam_id=source.exam_id,
        source_type=source.source_type,
        title=source.title,
        external_uri=source.external_uri,
        content_hash=source.content_hash,
        catalog_version=source.catalog_version,
        status=source.status,
        file_name=source.file_name,
        mime_type=source.mime_type,
        chunk_count=source.chunk_count,
        indexed_chunk_count=source.indexed_chunk_count,
        embedding_failure_count=source.embedding_failure_count,
        ingestion_failure_count=source.ingestion_failure_count,
        last_error=source.last_error,
        ingestion_started_at=source.ingestion_started_at,
        ingestion_completed_at=source.ingestion_completed_at,
        published_at=source.published_at,
        source_authority=source.source_authority,
        exam_stage=source.exam_stage,
        importance=source.importance,
        metadata=source.metadata_json,
        created_at=source.created_at,
        updated_at=source.updated_at,
    )


def _published_bounds(
    published_after: object | None,
    published_before: object | None,
) -> tuple[datetime | None, datetime | None]:
    from datetime import date

    start = None
    end = None
    if isinstance(published_after, date):
        start = datetime.combine(published_after, datetime.min.time(), tzinfo=UTC)
    if isinstance(published_before, date):
        end = datetime.combine(published_before, datetime.min.time(), tzinfo=UTC) + timedelta(days=1)
    return start, end
