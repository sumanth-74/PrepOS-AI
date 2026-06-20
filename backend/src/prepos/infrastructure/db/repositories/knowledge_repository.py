from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

import structlog
from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.knowledge.ports import (
    KnowledgeChunkRecord,
    KnowledgeRepositoryPort,
    KnowledgeSearchHit,
    KnowledgeSourceRecord,
)
from prepos.core.exceptions import ConflictError, NotFoundError
from prepos.infrastructure.db.models.knowledge import (
    KnowledgeChunkEmbeddingModel,
    KnowledgeChunkModel,
    KnowledgeSourceModel,
)

logger = structlog.get_logger(__name__)


class SqlAlchemyKnowledgeRepository(KnowledgeRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_source(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
        source_type: str,
        title: str,
        external_uri: str | None,
        content_hash: str,
        catalog_version: str | None,
        status: str,
        file_name: str | None,
        mime_type: str | None,
        metadata_json: dict[str, object],
        source_id: UUID | None = None,
        published_at: datetime | None = None,
        source_authority: str | None = None,
        exam_stage: str | None = None,
        importance: str | None = None,
    ) -> KnowledgeSourceRecord:
        model = KnowledgeSourceModel(
            id=source_id or uuid4(),
            tenant_id=tenant_id,
            exam_id=exam_id,
            source_type=source_type,
            title=title,
            external_uri=external_uri,
            content_hash=content_hash,
            catalog_version=catalog_version,
            status=status,
            file_name=file_name,
            mime_type=mime_type,
            published_at=published_at,
            source_authority=source_authority,
            exam_stage=exam_stage,
            importance=importance,
            metadata_json=metadata_json,
        )
        self._session.add(model)
        try:
            await self._session.flush()
        except IntegrityError as exc:
            raise ConflictError("Knowledge source with the same content hash already exists.") from exc
        return _to_source_record(model)

    async def get_source_by_id(
        self,
        source_id: UUID,
        *,
        tenant_id: UUID | None,
    ) -> KnowledgeSourceRecord | None:
        stmt = select(KnowledgeSourceModel).where(KnowledgeSourceModel.id == source_id)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    KnowledgeSourceModel.tenant_id.is_(None),
                    KnowledgeSourceModel.tenant_id == tenant_id,
                )
            )
        result = await self._session.execute(stmt)
        model = result.scalar_one_or_none()
        return _to_source_record(model) if model else None

    async def list_sources(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        source_types: tuple[str, ...] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeSourceRecord]:
        stmt = select(KnowledgeSourceModel)
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    KnowledgeSourceModel.tenant_id.is_(None),
                    KnowledgeSourceModel.tenant_id == tenant_id,
                )
            )
        if exam_id:
            stmt = stmt.where(KnowledgeSourceModel.exam_id == exam_id)
        if source_types:
            stmt = stmt.where(KnowledgeSourceModel.source_type.in_(source_types))
        stmt = stmt.order_by(
            KnowledgeSourceModel.published_at.desc().nullslast(),
            KnowledgeSourceModel.created_at.desc(),
        ).limit(limit).offset(offset)
        result = await self._session.execute(stmt)
        return [_to_source_record(model) for model in result.scalars().all()]

    async def update_source_status(
        self,
        source_id: UUID,
        *,
        status: str,
        last_error: str | None = None,
        chunk_count: int | None = None,
        indexed_chunk_count: int | None = None,
        embedding_failure_count: int | None = None,
        ingestion_failure_count: int | None = None,
        ingestion_started_at: datetime | None = None,
        ingestion_completed_at: datetime | None = None,
    ) -> None:
        model = await self._session.get(KnowledgeSourceModel, source_id)
        if model is None:
            raise NotFoundError("Knowledge source not found.")
        model.status = status
        if last_error is not None:
            model.last_error = last_error
        if chunk_count is not None:
            model.chunk_count = chunk_count
        if indexed_chunk_count is not None:
            model.indexed_chunk_count = indexed_chunk_count
        if embedding_failure_count is not None:
            model.embedding_failure_count = embedding_failure_count
        if ingestion_failure_count is not None:
            model.ingestion_failure_count = ingestion_failure_count
        if ingestion_started_at is not None:
            model.ingestion_started_at = ingestion_started_at
        if ingestion_completed_at is not None:
            model.ingestion_completed_at = ingestion_completed_at
        model.updated_at = datetime.now(UTC)
        await self._session.flush()

    async def update_current_affairs_metadata(
        self,
        source_id: UUID,
        *,
        published_at: datetime | None,
        source_authority: str | None,
        exam_stage: str | None,
        importance: str | None,
    ) -> None:
        model = await self._session.get(KnowledgeSourceModel, source_id)
        if model is None:
            raise NotFoundError("Knowledge source not found.")
        model.published_at = published_at
        model.source_authority = source_authority
        model.exam_stage = exam_stage
        model.importance = importance
        model.updated_at = datetime.now(UTC)
        await self._session.flush()

    async def replace_chunks(
        self,
        source_id: UUID,
        chunks: list[tuple[int, str, int, dict[str, object]]],
    ) -> list[KnowledgeChunkRecord]:
        await self._session.execute(
            delete(KnowledgeChunkModel).where(KnowledgeChunkModel.source_id == source_id)
        )
        records: list[KnowledgeChunkRecord] = []
        for chunk_index, content, token_count, metadata_json in chunks:
            model = KnowledgeChunkModel(
                source_id=source_id,
                chunk_index=chunk_index,
                content=content,
                token_count=token_count,
                metadata_json=metadata_json,
            )
            self._session.add(model)
            await self._session.flush()
            records.append(_to_chunk_record(model))
        return records

    async def list_chunks_for_source(self, source_id: UUID) -> list[KnowledgeChunkRecord]:
        stmt = (
            select(KnowledgeChunkModel)
            .where(KnowledgeChunkModel.source_id == source_id)
            .order_by(KnowledgeChunkModel.chunk_index)
        )
        result = await self._session.execute(stmt)
        return [_to_chunk_record(row) for row in result.scalars()]

    async def update_chunk_metadata(self, chunk_id: UUID, metadata_json: dict[str, object]) -> None:
        stmt = select(KnowledgeChunkModel).where(KnowledgeChunkModel.id == chunk_id)
        result = await self._session.execute(stmt)
        chunk = result.scalar_one_or_none()
        if chunk is None:
            raise NotFoundError("Knowledge chunk not found.")
        chunk.metadata_json = metadata_json
        await self._session.flush()

    async def list_chunks_without_embeddings(
        self,
        source_id: UUID,
        *,
        embedding_model: str,
        limit: int,
    ) -> list[KnowledgeChunkRecord]:
        embedded_ids = select(KnowledgeChunkEmbeddingModel.chunk_id).where(
            KnowledgeChunkEmbeddingModel.embedding_model == embedding_model
        )
        stmt = (
            select(KnowledgeChunkModel)
            .where(KnowledgeChunkModel.source_id == source_id)
            .where(KnowledgeChunkModel.id.not_in(embedded_ids))
            .order_by(KnowledgeChunkModel.chunk_index.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [_to_chunk_record(model) for model in result.scalars().all()]

    async def upsert_embeddings(
        self,
        *,
        chunk_ids: list[UUID],
        embedding_model: str,
        embedding_dims: int,
        embeddings: list[list[float]],
    ) -> None:
        if len(chunk_ids) != len(embeddings):
            raise ValueError("chunk_ids and embeddings length mismatch.")

        for chunk_id, vector in zip(chunk_ids, embeddings, strict=True):
            stmt = insert(KnowledgeChunkEmbeddingModel).values(
                id=uuid4(),
                chunk_id=chunk_id,
                embedding_model=embedding_model,
                embedding_dims=embedding_dims,
                embedding=vector,
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=["chunk_id", "embedding_model"],
                set_={
                    "embedding_dims": embedding_dims,
                    "embedding": vector,
                },
            )
            await self._session.execute(stmt)
        await self._session.flush()

    async def vector_search(
        self,
        *,
        query_embedding: list[float],
        embedding_model: str,
        tenant_id: UUID,
        exam_id: str,
        source_types: tuple[str, ...] | None,
        concept_ids: tuple[str, ...] | None,
        limit: int,
        published_after: datetime | None = None,
        published_before: datetime | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        paper: str | None = None,
        exam_stage: str | None = None,
    ) -> list[tuple[UUID, float]]:
        filters = [
            "ks.exam_id = :exam_id",
            "(ks.tenant_id IS NULL OR ks.tenant_id = :tenant_id)",
            "kce.embedding_model = :embedding_model",
        ]
        params: dict[str, object] = {
            "exam_id": exam_id,
            "tenant_id": str(tenant_id),
            "embedding_model": embedding_model,
            "limit": limit,
            "query_embedding": _vector_literal(query_embedding),
        }
        if source_types:
            filters.append("ks.source_type = ANY(:source_types)")
            params["source_types"] = list(source_types)
        if concept_ids:
            filters.append("kc.metadata_json -> 'concept_ids' ?| :concept_ids")
            params["concept_ids"] = list(concept_ids)
        if published_after is not None:
            filters.append("ks.published_at >= :published_after")
            params["published_after"] = published_after
        if published_before is not None:
            filters.append("ks.published_at < :published_before")
            params["published_before"] = published_before
        _append_pyq_filters(filters, params, year_from=year_from, year_to=year_to, paper=paper, exam_stage=exam_stage)

        sql = f"""
            SELECT kc.id AS chunk_id,
                   1 - (kce.embedding <=> :query_embedding::vector) AS score
            FROM knowledge_chunk_embeddings kce
            JOIN knowledge_chunks kc ON kc.id = kce.chunk_id
            JOIN knowledge_sources ks ON ks.id = kc.source_id
            WHERE {" AND ".join(filters)}
            ORDER BY kce.embedding <=> :query_embedding::vector
            LIMIT :limit
        """
        result = await self._session.execute(text(sql), params)
        return [(UUID(str(row.chunk_id)), float(row.score)) for row in result]

    async def keyword_search(
        self,
        *,
        query: str,
        tenant_id: UUID,
        exam_id: str,
        source_types: tuple[str, ...] | None,
        concept_ids: tuple[str, ...] | None,
        limit: int,
        published_after: datetime | None = None,
        published_before: datetime | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        paper: str | None = None,
        exam_stage: str | None = None,
    ) -> list[tuple[UUID, float]]:
        filters = [
            "ks.exam_id = :exam_id",
            "(ks.tenant_id IS NULL OR ks.tenant_id = :tenant_id)",
            "kc.content_tsv @@ plainto_tsquery('english', :query)",
        ]
        params: dict[str, object] = {
            "exam_id": exam_id,
            "tenant_id": str(tenant_id),
            "query": query,
            "limit": limit,
        }
        if source_types:
            filters.append("ks.source_type = ANY(:source_types)")
            params["source_types"] = list(source_types)
        if concept_ids:
            filters.append("kc.metadata_json -> 'concept_ids' ?| :concept_ids")
            params["concept_ids"] = list(concept_ids)
        if published_after is not None:
            filters.append("ks.published_at >= :published_after")
            params["published_after"] = published_after
        if published_before is not None:
            filters.append("ks.published_at < :published_before")
            params["published_before"] = published_before
        _append_pyq_filters(filters, params, year_from=year_from, year_to=year_to, paper=paper, exam_stage=exam_stage)

        sql = f"""
            SELECT kc.id AS chunk_id,
                   ts_rank_cd(kc.content_tsv, plainto_tsquery('english', :query)) AS score
            FROM knowledge_chunks kc
            JOIN knowledge_sources ks ON ks.id = kc.source_id
            WHERE {" AND ".join(filters)}
            ORDER BY score DESC
            LIMIT :limit
        """
        result = await self._session.execute(text(sql), params)
        return [(UUID(str(row.chunk_id)), float(row.score)) for row in result]

    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> dict[UUID, KnowledgeSearchHit]:
        if not chunk_ids:
            return {}

        stmt = (
            select(KnowledgeChunkModel, KnowledgeSourceModel)
            .join(KnowledgeSourceModel, KnowledgeSourceModel.id == KnowledgeChunkModel.source_id)
            .where(KnowledgeChunkModel.id.in_(chunk_ids))
        )
        result = await self._session.execute(stmt)
        hits: dict[UUID, KnowledgeSearchHit] = {}
        for chunk, source in result.all():
            hits[chunk.id] = KnowledgeSearchHit(
                chunk_id=chunk.id,
                content=chunk.content,
                score=0.0,
                vector_score=0.0,
                keyword_score=0.0,
                source_id=source.id,
                source_title=source.title,
                source_type=source.source_type,
                published_at=source.published_at,
                source_authority=source.source_authority,
                metadata_json=chunk.metadata_json,
            )
        return hits

    async def get_indexing_metrics(
        self,
        *,
        tenant_id: UUID | None,
        source_types: tuple[str, ...] | None = None,
    ) -> dict[str, int]:
        stmt = select(
            func.count(KnowledgeSourceModel.id),
            func.count(KnowledgeSourceModel.id).filter(KnowledgeSourceModel.status == "active"),
            func.count(KnowledgeSourceModel.id).filter(KnowledgeSourceModel.status == "processing"),
            func.count(KnowledgeSourceModel.id).filter(KnowledgeSourceModel.status == "failed"),
            func.coalesce(func.sum(KnowledgeSourceModel.chunk_count), 0),
            func.coalesce(func.sum(KnowledgeSourceModel.indexed_chunk_count), 0),
            func.coalesce(func.sum(KnowledgeSourceModel.embedding_failure_count), 0),
            func.coalesce(func.sum(KnowledgeSourceModel.ingestion_failure_count), 0),
        )
        if tenant_id is not None:
            stmt = stmt.where(
                or_(
                    KnowledgeSourceModel.tenant_id.is_(None),
                    KnowledgeSourceModel.tenant_id == tenant_id,
                )
            )
        if source_types:
            stmt = stmt.where(KnowledgeSourceModel.source_type.in_(source_types))
        result = await self._session.execute(stmt)
        row = result.one()
        return {
            "total_sources": int(row[0]),
            "active_sources": int(row[1]),
            "processing_sources": int(row[2]),
            "failed_sources": int(row[3]),
            "total_chunks": int(row[4]),
            "indexed_chunks": int(row[5]),
            "embedding_failures": int(row[6]),
            "ingestion_failures": int(row[7]),
        }


def _to_source_record(model: KnowledgeSourceModel) -> KnowledgeSourceRecord:
    return KnowledgeSourceRecord(
        id=model.id,
        tenant_id=model.tenant_id,
        exam_id=model.exam_id,
        source_type=model.source_type,
        title=model.title,
        external_uri=model.external_uri,
        content_hash=model.content_hash,
        catalog_version=model.catalog_version,
        status=model.status,
        file_name=model.file_name,
        mime_type=model.mime_type,
        chunk_count=model.chunk_count,
        indexed_chunk_count=model.indexed_chunk_count,
        embedding_failure_count=model.embedding_failure_count,
        ingestion_failure_count=model.ingestion_failure_count,
        last_error=model.last_error,
        ingestion_started_at=model.ingestion_started_at,
        ingestion_completed_at=model.ingestion_completed_at,
        published_at=model.published_at,
        source_authority=model.source_authority,
        exam_stage=model.exam_stage,
        importance=model.importance,
        metadata_json=dict(model.metadata_json or {}),
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


def _to_chunk_record(model: KnowledgeChunkModel) -> KnowledgeChunkRecord:
    return KnowledgeChunkRecord(
        id=model.id,
        source_id=model.source_id,
        chunk_index=model.chunk_index,
        content=model.content,
        token_count=model.token_count,
        metadata_json=dict(model.metadata_json or {}),
    )


def _date_bounds(
    published_after: date | None,
    published_before: date | None,
) -> tuple[datetime | None, datetime | None]:
    start = (
        datetime.combine(published_after, datetime.min.time(), tzinfo=UTC)
        if published_after is not None
        else None
    )
    end = (
        datetime.combine(published_before, datetime.min.time(), tzinfo=UTC) + timedelta(days=1)
        if published_before is not None
        else None
    )
    return start, end


def _vector_literal(values: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in values) + "]"


def _append_pyq_filters(
    filters: list[str],
    params: dict[str, object],
    *,
    year_from: int | None,
    year_to: int | None,
    paper: str | None,
    exam_stage: str | None,
) -> None:
    if year_from is not None:
        filters.append("(kc.metadata_json ->> 'year')::int >= :year_from")
        params["year_from"] = year_from
    if year_to is not None:
        filters.append("(kc.metadata_json ->> 'year')::int <= :year_to")
        params["year_to"] = year_to
    if paper is not None:
        filters.append("lower(kc.metadata_json ->> 'paper') = lower(:paper)")
        params["paper"] = paper
    if exam_stage is not None:
        filters.append(
            "(lower(kc.metadata_json ->> 'exam_stage') = lower(:exam_stage) OR lower(ks.exam_stage) = lower(:exam_stage))"
        )
        params["exam_stage"] = exam_stage
