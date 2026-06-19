from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from prepos.domain.student.entities import LearningGraphProvision, PreparationTwinProvision, Student


class StudentRepositoryPort(ABC):
    @abstractmethod
    async def get_by_id(self, tenant_id: UUID, student_id: UUID) -> Student | None:
        raise NotImplementedError

    @abstractmethod
    async def get_by_user_id(self, tenant_id: UUID, user_id: UUID) -> Student | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, student: Student) -> Student:
        raise NotImplementedError


class LearningGraphProvisionRepositoryPort(ABC):
    @abstractmethod
    async def get_by_student(self, tenant_id: UUID, student_id: UUID) -> LearningGraphProvision | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, provision: LearningGraphProvision) -> LearningGraphProvision:
        raise NotImplementedError


class PreparationTwinProvisionRepositoryPort(ABC):
    @abstractmethod
    async def get_by_student_exam(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwinProvision | None:
        raise NotImplementedError

    @abstractmethod
    async def save(self, twin: PreparationTwinProvision) -> PreparationTwinProvision:
        raise NotImplementedError


class StudentUnitOfWorkPort(ABC):
    student_repo: StudentRepositoryPort
    learning_graph_provision_repo: LearningGraphProvisionRepositoryPort
    preparation_twin_repo: PreparationTwinProvisionRepositoryPort

    @abstractmethod
    async def commit(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def rollback(self) -> None:
        raise NotImplementedError
