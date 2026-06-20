from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    exam_id: str = Field(min_length=1, max_length=64)
    concept_ids: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    limit: int = Field(default=8, ge=1, le=50)
    hybrid_alpha: float | None = Field(default=None, ge=0.0, le=1.0)
    published_after: date | None = None
    published_before: date | None = None
    prefer_recency: bool = False
    year_from: int | None = Field(default=None, ge=1990, le=2100)
    year_to: int | None = Field(default=None, ge=1990, le=2100)
    paper: str | None = Field(default=None, max_length=64)
    exam_stage: str | None = Field(default=None, max_length=32)
    prefer_pyq: bool = False


class KnowledgeSourceSummary(BaseModel):
    source_id: UUID
    title: str
    source_type: str
    published_at: datetime | None = None
    source_authority: str | None = None


class KnowledgeSearchChunk(BaseModel):
    chunk_id: UUID
    content: str
    score: float
    vector_score: float
    keyword_score: float
    source: KnowledgeSourceSummary
    metadata: dict[str, object]


class KnowledgeSearchResponse(BaseModel):
    chunks: list[KnowledgeSearchChunk]
    query_embedding_model: str


class CreateKnowledgeSourceRequest(BaseModel):
    exam_id: str = Field(min_length=1, max_length=64)
    source_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    catalog_version: str | None = Field(default=None, max_length=32)
    subject_id: str | None = Field(default=None, max_length=64)
    topic_id: str | None = Field(default=None, max_length=64)
    concept_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class KnowledgeSourceResponse(BaseModel):
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
    published_at: datetime | None = None
    source_authority: str | None = None
    exam_stage: str | None = None
    importance: str | None = None
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class KnowledgeSourceListResponse(BaseModel):
    sources: list[KnowledgeSourceResponse]
    total: int


class KnowledgeIndexingMetricsResponse(BaseModel):
    total_sources: int
    active_sources: int
    processing_sources: int
    failed_sources: int
    total_chunks: int
    indexed_chunks: int
    embedding_failures: int
    ingestion_failures: int


class KnowledgeAskRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    exam_id: str = Field(min_length=1, max_length=64)
    limit: int = Field(default=8, ge=1, le=50)
    concept_ids: list[str] = Field(default_factory=list)
    source_types: list[str] = Field(default_factory=list)
    hybrid_alpha: float | None = Field(default=None, ge=0.0, le=1.0)
    retrieval_hints: list[str] = Field(default_factory=list)
    student_context: str | None = None
    published_after: date | None = None
    published_before: date | None = None
    prefer_recency: bool = False
    current_affairs_mode: bool = False
    pyq_mode: bool = False
    year_from: int | None = Field(default=None, ge=1990, le=2100)
    year_to: int | None = Field(default=None, ge=1990, le=2100)
    paper: str | None = Field(default=None, max_length=64)
    exam_stage: str | None = Field(default=None, max_length=32)
    prefer_pyq: bool = False
    frequency_summary: str | None = None


class KnowledgeAskCitation(BaseModel):
    chunk_id: UUID
    source_title: str
    source_type: str | None = None
    published_at: datetime | None = None
    pyq_year: int | None = None
    pyq_paper: str | None = None


class KnowledgeAskResponse(BaseModel):
    answer: str
    citations: list[KnowledgeAskCitation]
    confidence: str
