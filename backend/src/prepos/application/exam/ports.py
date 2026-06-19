from __future__ import annotations

from abc import ABC, abstractmethod

from prepos.domain.exam.entities import (
    CatalogVersion,
    Concept,
    ConceptRelationship,
    Exam,
    ExamTrack,
    Subject,
    Topic,
)


class ExamRepositoryPort(ABC):
    @abstractmethod
    async def get_exam(self, exam_id: str) -> Exam | None:
        raise NotImplementedError

    @abstractmethod
    async def get_exam_by_code(self, exam_code: str) -> Exam | None:
        raise NotImplementedError

    @abstractmethod
    async def list_exams(self, *, status: str | None = None) -> tuple[Exam, ...]:
        raise NotImplementedError

    @abstractmethod
    async def save_exam(self, exam: Exam) -> Exam:
        raise NotImplementedError

    @abstractmethod
    async def save_tracks(self, tracks: tuple[ExamTrack, ...]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_tracks(self, exam_id: str) -> tuple[ExamTrack, ...]:
        raise NotImplementedError


class SubjectRepositoryPort(ABC):
    @abstractmethod
    async def list_subjects(self, exam_id: str, *, status: str | None = None) -> tuple[Subject, ...]:
        raise NotImplementedError

    @abstractmethod
    async def save_subjects(self, subjects: tuple[Subject, ...]) -> None:
        raise NotImplementedError


class TopicRepositoryPort(ABC):
    @abstractmethod
    async def list_topics(
        self,
        exam_id: str,
        *,
        subject_id: str | None = None,
        status: str | None = None,
    ) -> tuple[Topic, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_topic(self, topic_id: str) -> Topic | None:
        raise NotImplementedError

    @abstractmethod
    async def save_topics(self, topics: tuple[Topic, ...]) -> None:
        raise NotImplementedError


class ConceptRepositoryPort(ABC):
    @abstractmethod
    async def get_concept(self, concept_id: str) -> Concept | None:
        raise NotImplementedError

    @abstractmethod
    async def list_concepts_by_topic(self, topic_id: str, *, status: str | None = None) -> tuple[Concept, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_concepts_by_exam(
        self,
        exam_id: str,
        *,
        status: str | None = None,
        catalog_version: str | None = None,
    ) -> tuple[Concept, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_children(self, parent_concept_id: str) -> tuple[Concept, ...]:
        raise NotImplementedError

    @abstractmethod
    async def search_concepts(
        self,
        *,
        exam_id: str,
        query: str | None = None,
        subject_id: str | None = None,
        topic_id: str | None = None,
        status: str | None = "active",
        catalog_version: str | None = None,
        offset: int = 0,
        limit: int = 20,
    ) -> tuple[tuple[Concept, ...], int]:
        raise NotImplementedError

    @abstractmethod
    async def save_concepts(self, concepts: tuple[Concept, ...]) -> None:
        raise NotImplementedError

    @abstractmethod
    async def count_active_by_exam(self, exam_id: str) -> int:
        raise NotImplementedError


class ConceptRelationshipRepositoryPort(ABC):
    @abstractmethod
    async def list_by_exam(self, exam_id: str, *, status: str | None = None) -> tuple[ConceptRelationship, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_prerequisites_for_concept(self, concept_id: str) -> tuple[ConceptRelationship, ...]:
        raise NotImplementedError

    @abstractmethod
    async def save_relationships(self, relationships: tuple[ConceptRelationship, ...]) -> None:
        raise NotImplementedError


class CatalogVersionRepositoryPort(ABC):
    @abstractmethod
    async def get_by_version(self, exam_id: str, version: str) -> CatalogVersion | None:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_published(self, exam_id: str) -> CatalogVersion | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, catalog_version: CatalogVersion) -> CatalogVersion:
        raise NotImplementedError

    @abstractmethod
    async def supersede_published(self, exam_id: str, except_version: str) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_versions(self, exam_id: str) -> tuple[CatalogVersion, ...]:
        raise NotImplementedError


class ExamCatalogUnitOfWorkPort(ABC):
    exam_repo: ExamRepositoryPort
    subject_repo: SubjectRepositoryPort
    topic_repo: TopicRepositoryPort
    concept_repo: ConceptRepositoryPort
    relationship_repo: ConceptRelationshipRepositoryPort
    catalog_version_repo: CatalogVersionRepositoryPort

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
