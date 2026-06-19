from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.domain.twin.intervention_history_entities import StudentInterventionHistoryEntry
from prepos.infrastructure.db.models.student import StudentInterventionHistoryModel


def _map_row(row: StudentInterventionHistoryModel) -> StudentInterventionHistoryEntry:
    return StudentInterventionHistoryEntry(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        intervention_type=row.intervention_type,
        effectiveness_score=row.effectiveness_score,
        readiness_delta=row.readiness_delta,
        predicted_score_delta=row.predicted_score_delta,
        completion_delta=row.completion_delta,
        outcome_status=row.outcome_status,
        created_at=row.created_at,
    )


class SqlAlchemyInterventionHistoryRepository(InterventionHistoryRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        row = StudentInterventionHistoryModel(
            id=uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            intervention_type=intervention_type,
            effectiveness_score=effectiveness_score,
            readiness_delta=readiness_delta,
            predicted_score_delta=predicted_score_delta,
            completion_delta=completion_delta,
            outcome_status=outcome_status,
            created_at=created_at,
        )
        self._session.add(row)
        await self._session.flush()
        return _map_row(row)

    async def get_latest_outcome(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudentInterventionHistoryEntry | None:
        stmt = (
            select(StudentInterventionHistoryModel)
            .where(
                StudentInterventionHistoryModel.tenant_id == tenant_id,
                StudentInterventionHistoryModel.student_id == student_id,
                StudentInterventionHistoryModel.exam_id == exam_id,
            )
            .order_by(StudentInterventionHistoryModel.created_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _map_row(row)

    async def get_average_effectiveness_by_type(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> dict[str, Decimal]:
        stmt = (
            select(
                StudentInterventionHistoryModel.intervention_type,
                func.avg(StudentInterventionHistoryModel.effectiveness_score),
            )
            .where(
                StudentInterventionHistoryModel.tenant_id == tenant_id,
                StudentInterventionHistoryModel.student_id == student_id,
                StudentInterventionHistoryModel.exam_id == exam_id,
            )
            .group_by(StudentInterventionHistoryModel.intervention_type)
        )
        result = await self._session.execute(stmt)
        averages: dict[str, Decimal] = {}
        for intervention_type, average in result.all():
            if average is None:
                continue
            averages[str(intervention_type)] = Decimal(str(average)).quantize(Decimal("0.01"))
        return averages

    async def list_outcomes(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[StudentInterventionHistoryEntry, ...]:
        stmt = (
            select(StudentInterventionHistoryModel)
            .where(
                StudentInterventionHistoryModel.tenant_id == tenant_id,
                StudentInterventionHistoryModel.student_id == student_id,
                StudentInterventionHistoryModel.exam_id == exam_id,
            )
            .order_by(StudentInterventionHistoryModel.created_at.asc())
        )
        result = await self._session.execute(stmt)
        return tuple(_map_row(row) for row in result.scalars().all())
