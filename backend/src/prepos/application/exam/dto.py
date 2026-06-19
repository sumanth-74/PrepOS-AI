from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ExamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    exam_id: str
    exam_code: str
    exam_name: str
    exam_type: str
    prelims_weight: Decimal
    mains_weight: Decimal
    interview_weight: Decimal
    domain_catalog_version: str
    essay_included: bool
    status: str


class ExamTrackResponse(BaseModel):
    track_id: str
    track_code: str
    track_name: str
    stage: str
    subject_ids: list[str]
    sort_order: int
    status: str


class SubjectResponse(BaseModel):
    subject_id: str
    subject_name: str
    subject_slug: str
    prelims_applicable: bool
    mains_applicable: bool
    sort_order: int
    status: str


class TopicResponse(BaseModel):
    topic_id: str
    subject_id: str
    topic_name: str
    topic_slug: str
    prelims_relevance: int
    mains_relevance: int
    sort_order: int
    status: str


class ConceptResponse(BaseModel):
    concept_id: str
    topic_id: str
    subject_id: str
    concept_name: str
    concept_slug: str
    concept_type: str
    prelims_relevance: int
    mains_relevance: int
    parent_concept_id: str | None = None
    current_affairs_linkable: bool
    pyq_mappable: bool
    exam_stages: list[str]
    difficulty: int
    status: str
    domain_catalog_version: str


class ConceptRelationshipResponse(BaseModel):
    id: str
    source_id: str
    source_type: str
    target_id: str
    target_type: str
    relationship_type: str
    weight: Decimal
    status: str


class TopicTreeResponse(BaseModel):
    topic: TopicResponse
    concepts: list[ConceptResponse]


class SubjectTreeResponse(BaseModel):
    subject: SubjectResponse
    topics: list[TopicTreeResponse]


class ExamTreeResponse(BaseModel):
    exam: ExamResponse
    tracks: list[ExamTrackResponse]
    subjects: list[SubjectTreeResponse]
    catalog_version: str


class PaginatedConceptsResponse(BaseModel):
    items: list[ConceptResponse]
    total: int
    offset: int
    limit: int


class ConceptAncestorsResponse(BaseModel):
    concept: ConceptResponse
    ancestors: list[ConceptResponse]
    topic: TopicResponse
    subject: SubjectResponse


class ConceptDescendantsResponse(BaseModel):
    concept: ConceptResponse
    descendants: list[ConceptResponse]


class CatalogVersionResponse(BaseModel):
    id: UUID
    exam_id: str
    version: str
    status: str
    published_at: datetime | None
    concepts_added: int
    concepts_deprecated: int
    change_summary: str | None


class CreateExamRequest(BaseModel):
    exam_id: str = Field(min_length=3, max_length=64)
    exam_code: str = Field(min_length=3, max_length=64)
    exam_name: str = Field(min_length=3, max_length=512)
    exam_type: str = "competitive_civil_services"
    prelims_weight: Decimal = Decimal("0.25")
    mains_weight: Decimal = Decimal("0.55")
    interview_weight: Decimal = Decimal("0.20")
    essay_included: bool = True


class PublishCatalogRequest(BaseModel):
    change_summary: str | None = None


class SeedImportResponse(BaseModel):
    exam_id: str
    catalog_version: str
    concepts_imported: int
    relationships_imported: int
    idempotent: bool
