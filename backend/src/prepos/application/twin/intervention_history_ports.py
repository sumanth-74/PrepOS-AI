from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry


class InterventionHistoryRepositoryPort(ABC):
    @abstractmethod
    async def save_outcome(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        intervention_type: str,
        effectiveness_score: Decimal,
        readiness_delta: Decimal,
        predicted_score_delta: Decimal,
        completion_delta: Decimal,
        outcome_status: str,
        created_at: datetime,
    ) -> StudentInterventionHistoryEntry:
        raise NotImplementedError

    @abstractmethod
    async def get_latest_outcome(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudentInterventionHistoryEntry | None:
        raise NotImplementedError

    @abstractmethod
    async def get_average_effectiveness_by_type(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> dict[str, Decimal]:
        raise NotImplementedError

    @abstractmethod
    async def list_outcomes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[StudentInterventionHistoryEntry, ...]:
        raise NotImplementedError
