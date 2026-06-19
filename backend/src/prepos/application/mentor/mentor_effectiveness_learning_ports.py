from __future__ import annotations

from abc import ABC, abstractmethod
from decimal import Decimal
from uuid import UUID

from prepos.domain.mentor.mentor_effectiveness_learning_v1 import (
    ActionEffectivenessSample,
    MentorActionEffectiveness,
    MentorEffectivenessLearningResult,
)


class MentorEffectivenessLearningRepositoryPort(ABC):
    @abstractmethod
    async def list_learning_samples(
        self,
        tenant_id: UUID,
        *,
        student_id: UUID | None = None,
        exam_id: str | None = None,
    ) -> tuple[ActionEffectivenessSample, ...]:
        raise NotImplementedError

    @abstractmethod
    async def upsert_action_effectiveness(
        self,
        tenant_id: UUID,
        action_effectiveness: tuple[MentorActionEffectiveness, ...],
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def list_action_effectiveness(
        self,
        tenant_id: UUID,
    ) -> tuple[MentorActionEffectiveness, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_action_effectiveness(
        self,
        tenant_id: UUID,
        action_type: str,
    ) -> MentorActionEffectiveness | None:
        raise NotImplementedError

    @abstractmethod
    async def get_tenant_learning_summary(
        self,
        tenant_id: UUID,
    ) -> MentorEffectivenessLearningResult:
        raise NotImplementedError

    @abstractmethod
    async def get_student_learning_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> MentorEffectivenessLearningResult:
        raise NotImplementedError
