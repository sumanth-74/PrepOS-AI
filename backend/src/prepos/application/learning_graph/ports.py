from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from prepos.domain.learning_graph.entities import (
    ConceptProgressNode,
    LearningGraphEvent,
    ScoreAuditLog,
    StudentGraphSummary,
)


class LearningGraphRepositoryPort(ABC):
    @abstractmethod
    async def get_node(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        raise NotImplementedError

    @abstractmethod
    async def save_node(self, node: ConceptProgressNode, *, expected_row_version: int) -> ConceptProgressNode:
        raise NotImplementedError

    @abstractmethod
    async def bulk_insert_nodes(self, nodes: tuple[ConceptProgressNode, ...]) -> int:
        raise NotImplementedError

    @abstractmethod
    async def count_nodes(self, tenant_id: UUID, student_id: UUID) -> int:
        raise NotImplementedError

    @abstractmethod
    async def append_graph_event(self, event: LearningGraphEvent) -> None:
        raise NotImplementedError

    @abstractmethod
    async def append_score_audit(self, entry: ScoreAuditLog) -> None:
        raise NotImplementedError

    @abstractmethod
    async def update_provision_count(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        provisioned_node_count: int,
        status: str,
    ) -> None:
        raise NotImplementedError


class LearningGraphReadRepositoryPort(ABC):
    @abstractmethod
    async def list_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[ConceptProgressNode, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_summary(self, tenant_id: UUID, student_id: UUID) -> StudentGraphSummary | None:
        raise NotImplementedError

    @abstractmethod
    async def list_weakest_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        limit: int = 10,
    ) -> tuple[ConceptProgressNode, ...]:
        raise NotImplementedError

    @abstractmethod
    async def list_rated_nodes(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> tuple[ConceptProgressNode, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_student_exam(self, tenant_id: UUID, student_id: UUID) -> tuple[str, str] | None:
        """Return (exam_id, catalog_version) from student + provision."""
        raise NotImplementedError

    @abstractmethod
    async def get_provision(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> tuple[int, int, str] | None:
        """Return (expected_node_count, provisioned_node_count, status) if exists."""
        raise NotImplementedError
