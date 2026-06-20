from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RetrievalQualityMetrics(BaseModel):
    recall_at_5: float
    recall_at_8: float
    precision_at_5: float
    precision_at_8: float
    mrr: float
    ndcg: float
    evaluation_count: int


class FaithfulnessMetrics(BaseModel):
    avg_support_score: float
    avg_citation_coverage: float
    evaluation_count: int


class HallucinationMetrics(BaseModel):
    avg_hallucination_score: float
    high_hallucination_rate: float
    evaluation_count: int


class CitationCoverageMetrics(BaseModel):
    avg_citation_coverage: float
    avg_citation_count: float
    evaluation_count: int


class SourceQualityItem(BaseModel):
    source_type: str
    query_count: int
    citation_count: int
    avg_confidence_score: float
    avg_support_score: float
    avg_hallucination_score: float


class SourceQualityMetrics(BaseModel):
    sources: list[SourceQualityItem]


class RagQualityTrendPoint(BaseModel):
    date: str
    avg_support_score: float
    avg_hallucination_score: float
    avg_citation_coverage: float


class RagQualityResponse(BaseModel):
    retrieval: RetrievalQualityMetrics
    faithfulness: FaithfulnessMetrics
    hallucination: HallucinationMetrics
    citation_coverage: CitationCoverageMetrics
    source_quality: SourceQualityMetrics
    trends: list[RagQualityTrendPoint] = Field(default_factory=list)
