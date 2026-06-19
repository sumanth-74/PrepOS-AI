from __future__ import annotations

from abc import ABC, abstractmethod
from uuid import UUID

from prepos.application.twin.projection_ports import RecommendationSummary
from prepos.domain.twin.entities import PersistedTwinRecommendation, TwinRecommendation


class TwinRecommendationRepositoryPort(ABC):
    @abstractmethod
    async def replace_recommendations(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendations: tuple[TwinRecommendation, ...],
    ) -> tuple[PersistedTwinRecommendation, ...]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_recommendation(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        recommendation: TwinRecommendation,
    ) -> PersistedTwinRecommendation:
        raise NotImplementedError

    @abstractmethod
    async def delete_recommendation(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def list_recommendations(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        limit: int = 20,
    ) -> tuple[PersistedTwinRecommendation, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_recommendation_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        top_limit: int = 10,
    ) -> RecommendationSummary:
        raise NotImplementedError
