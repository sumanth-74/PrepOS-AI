from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class KnowledgeChunkMetadata:
    exam_id: str
    tenant_id: UUID | None
    subject_id: str | None = None
    topic_id: str | None = None
    concept_ids: tuple[str, ...] = ()
    catalog_version: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeSourceRecord:
    id: UUID
    tenant_id: UUID | None
    exam_id: str
    source_type: str
    title: str
    external_uri: str | None
    content_hash: str
    catalog_version: str | None
    status: str
    file_name: str | None
    mime_type: str | None
    chunk_count: int
    indexed_chunk_count: int
    embedding_failure_count: int
    ingestion_failure_count: int
    last_error: str | None
    ingestion_started_at: datetime | None
    ingestion_completed_at: datetime | None
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None = None
    source_authority: str | None = None
    exam_stage: str | None = None
    importance: str | None = None


@dataclass(frozen=True, slots=True)
class KnowledgeChunkRecord:
    id: UUID
    source_id: UUID
    chunk_index: int
    content: str
    token_count: int
    metadata_json: dict[str, object]


@dataclass(frozen=True, slots=True)
class KnowledgeSearchHit:
    chunk_id: UUID
    content: str
    score: float
    vector_score: float
    keyword_score: float
    source_id: UUID
    source_title: str
    source_type: str
    metadata_json: dict[str, object]
    published_at: datetime | None = None
    source_authority: str | None = None


class EmbeddingProviderPort(ABC):
    @property
    @abstractmethod
    def model_name(self) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def dimensions(self) -> int:
        raise NotImplementedError

    @abstractmethod
    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError


class KnowledgeStoragePort(ABC):
    @abstractmethod
    async def save_upload(
        self,
        *,
        tenant_id: UUID | None,
        source_id: UUID,
        file_name: str,
        content: bytes,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def read_text(self, external_uri: str) -> str:
        raise NotImplementedError


class KnowledgeRepositoryPort(ABC):
    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def get_source_by_id(
        self,
        source_id: UUID,
        *,
        tenant_id: UUID | None,
    ) -> KnowledgeSourceRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_sources(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        source_types: tuple[str, ...] | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[KnowledgeSourceRecord]:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def update_current_affairs_metadata(
        self,
        source_id: UUID,
        *,
        published_at: datetime | None,
        source_authority: str | None,
        exam_stage: str | None,
        importance: str | None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def replace_chunks(
        self,
        source_id: UUID,
        chunks: list[tuple[int, str, int, dict[str, object]]],
    ) -> list[KnowledgeChunkRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_chunks_for_source(self, source_id: UUID) -> list[KnowledgeChunkRecord]:
        raise NotImplementedError

    @abstractmethod
    async def update_chunk_metadata(self, chunk_id: UUID, metadata_json: dict[str, object]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_chunks_without_embeddings(
        self,
        source_id: UUID,
        *,
        embedding_model: str,
        limit: int,
    ) -> list[KnowledgeChunkRecord]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_embeddings(
        self,
        *,
        chunk_ids: list[UUID],
        embedding_model: str,
        embedding_dims: int,
        embeddings: list[list[float]],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
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
        raise NotImplementedError

    @abstractmethod
    async def get_chunks_by_ids(self, chunk_ids: list[UUID]) -> dict[UUID, KnowledgeSearchHit]:
        raise NotImplementedError

    @abstractmethod
    async def get_indexing_metrics(
        self,
        *,
        tenant_id: UUID | None,
        source_types: tuple[str, ...] | None = None,
    ) -> dict[str, int]:
        raise NotImplementedError
