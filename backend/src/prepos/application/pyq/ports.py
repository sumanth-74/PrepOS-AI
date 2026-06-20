from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True, slots=True)
class PyqQuestionRecord:
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
    knowledge_source_id: UUID | None
    knowledge_chunk_id: UUID | None
    concept_ids: tuple[str, ...]
    metadata_json: dict[str, object]
    created_at: datetime
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class PyqMappingRecord:
    id: UUID
    pyq_id: UUID
    concept_id: str
    confidence_score: float
    created_at: datetime


@dataclass(frozen=True, slots=True)
class PyqStatisticRecord:
    exam_id: str
    concept_id: str
    pyq_count: int
    first_appearance_year: int | None
    last_appearance_year: int | None
    frequency_score: float
    trend_score: float
    updated_at: datetime


@dataclass(frozen=True, slots=True)
class CreatePyqQuestionInput:
    year: int
    exam_stage: str
    paper: str
    question_text: str
    answer_text: str | None
    source_reference: str | None
    difficulty: int | None
    importance: str | None
    concept_ids: tuple[str, ...]
    confidence_score: float
    metadata_json: dict[str, object]
    knowledge_source_id: UUID | None
    knowledge_chunk_id: UUID | None


class PyqRepositoryPort(ABC):
    @abstractmethod
    async def create_questions_batch(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
        questions: list[CreatePyqQuestionInput],
    ) -> list[PyqQuestionRecord]:
        raise NotImplementedError

    @abstractmethod
    async def get_question_by_id(
        self,
        question_id: UUID,
        *,
        tenant_id: UUID | None,
    ) -> PyqQuestionRecord | None:
        raise NotImplementedError

    @abstractmethod
    async def list_questions(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        year_from: int | None = None,
        year_to: int | None = None,
        paper: str | None = None,
        exam_stage: str | None = None,
        concept_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[PyqQuestionRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_mapping_hits(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str,
    ) -> list[tuple[str, int, float]]:
        """Return (concept_id, year, confidence_score) tuples."""
        raise NotImplementedError

    @abstractmethod
    async def replace_statistics(
        self,
        *,
        exam_id: str,
        statistics: list[PyqStatisticRecord],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_statistics(
        self,
        *,
        exam_id: str,
        limit: int = 50,
    ) -> list[PyqStatisticRecord]:
        raise NotImplementedError

    @abstractmethod
    async def list_mappings_for_review(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> list[tuple[PyqQuestionRecord, list[PyqMappingRecord]]]:
        raise NotImplementedError

    @abstractmethod
    async def count_questions(
        self,
        *,
        tenant_id: UUID | None,
        exam_id: str | None = None,
    ) -> int:
        raise NotImplementedError
