from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSearchResponse


class CreateCurrentAffairsArticleRequest(BaseModel):
    exam_id: str = Field(min_length=1, max_length=64)
    source_type: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    published_at: datetime | None = None
    source_authority: str | None = Field(default=None, max_length=64)
    exam_stage: str | None = Field(default=None, max_length=64)
    importance: str | None = Field(default=None, max_length=32)
    catalog_version: str | None = Field(default=None, max_length=32)
    subject_id: str | None = Field(default=None, max_length=64)
    topic_id: str | None = Field(default=None, max_length=64)
    concept_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)


class CurrentAffairsArticleResponse(BaseModel):
    id: UUID
    tenant_id: UUID | None
    exam_id: str
    source_type: str
    title: str
    status: str
    published_at: datetime | None
    source_authority: str | None
    exam_stage: str | None
    importance: str | None
    chunk_count: int
    indexed_chunk_count: int
    concept_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class CurrentAffairsArticleListResponse(BaseModel):
    articles: list[CurrentAffairsArticleResponse]
    total: int


class CurrentAffairsSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    exam_id: str = Field(min_length=1, max_length=64)
    source_types: list[str] = Field(default_factory=list)
    concept_ids: list[str] = Field(default_factory=list)
    published_after: date | None = None
    published_before: date | None = None
    prefer_recency: bool = True
    limit: int = Field(default=8, ge=1, le=50)


class CurrentAffairsSearchResponse(KnowledgeSearchResponse):
    recency_boost_applied: bool = False
    chunks: list[KnowledgeSearchChunk]


class CurrentAffairsIndexingMetricsResponse(BaseModel):
    total_articles: int
    active_articles: int
    processing_articles: int
    failed_articles: int
    total_chunks: int
    indexed_chunks: int


class CurrentAffairsAnalyticsResponse(BaseModel):
    current_affairs_qna_count: int
    article_citation_usage_count: int
    article_citation_usage_rate: float
    recency_retrieval_success_rate: float
    recency_boost_usage_rate: float
