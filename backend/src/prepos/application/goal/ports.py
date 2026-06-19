from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from uuid import UUID

from prepos.domain.goal.entities import PreparationGoal


class GoalRepositoryPort(ABC):
    @abstractmethod
    async def upsert_goal(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        target_readiness_score: Decimal,
        target_date: date,
        daily_capacity_minutes: int,
    ) -> PreparationGoal:
        raise NotImplementedError

    @abstractmethod
    async def get_goal(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationGoal | None:
        raise NotImplementedError
