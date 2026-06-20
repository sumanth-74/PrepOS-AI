from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from prepos.application.knowledge.dto import KnowledgeSearchChunk, KnowledgeSearchResponse


class CreatePyqUploadRequest(BaseModel):
    exam_id: str = Field(min_length=1, max_length=64)
    title: str = Field(min_length=1, max_length=512)
    catalog_version: str | None = Field(default=None, max_length=32)


class PyqQuestionResponse(BaseModel):
    id: UUID
    tenant_id: UUID | None
    exam_id: str
    year: int
    exam_stage: str
    paper: str
    question_text: str
    answer_text: str | None
    source_reference: str | None
    difficulty: int | None
    importance: str | None
    concept_ids: list[str]
    knowledge_source_id: UUID | None
    knowledge_chunk_id: UUID | None
    metadata: dict[str, object]
    created_at: datetime
    updated_at: datetime


class PyqUploadResponse(BaseModel):
    knowledge_source_id: UUID
    questions_ingested: int
    questions: list[PyqQuestionResponse]


class PyqSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    exam_id: str = Field(min_length=1, max_length=64)
    concept_ids: list[str] = Field(default_factory=list)
    year_from: int | None = Field(default=None, ge=1990, le=2100)
    year_to: int | None = Field(default=None, ge=1990, le=2100)
    paper: str | None = Field(default=None, max_length=64)
    exam_stage: str | None = Field(default=None, max_length=32)
    limit: int = Field(default=8, ge=1, le=50)
    prefer_pyq: bool = False


class PyqSearchResponse(BaseModel):
    chunks: list[KnowledgeSearchChunk]
    query_embedding_model: str
    pyq_boost_applied: bool


class PyqTrendItem(BaseModel):
    concept_id: str
    pyq_count: int
    first_appearance_year: int | None
    last_appearance_year: int | None
    frequency_score: float
    trend_score: float


class PyqTrendsResponse(BaseModel):
    exam_id: str
    trends: list[PyqTrendItem]
    total_questions: int


class PyqMappingReviewItem(BaseModel):
    question: PyqQuestionResponse
    mappings: list[dict[str, object]]


class PyqCoverageResponse(BaseModel):
    exam_id: str
    total_questions: int
    mapped_questions: int
    unmapped_questions: int
    top_concepts: list[PyqTrendItem]


class PyqIndexingMetricsResponse(BaseModel):
    total_questions: int
    indexed_questions: int
    total_knowledge_chunks: int
    indexed_knowledge_chunks: int


class PyqAnalyticsResponse(BaseModel):
    pyq_queries: int
    pyq_citation_rate: float
    pyq_topic_frequency_avg: float
    pyq_revision_recommendations: int
