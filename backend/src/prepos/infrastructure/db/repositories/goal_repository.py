from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.goal.ports import GoalRepositoryPort
from prepos.domain.goal.entities import PreparationGoal
from prepos.infrastructure.db.models.goal import StudentPreparationGoalModel


def _map_row(row: StudentPreparationGoalModel) -> PreparationGoal:
    return PreparationGoal(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        target_readiness_score=row.target_readiness_score,
        target_date=row.target_date,
        daily_capacity_minutes=row.daily_capacity_minutes,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyGoalRepository(GoalRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

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
        now = datetime.now(UTC)
        goal_id = uuid4()
        stmt = insert(StudentPreparationGoalModel).values(
            id=goal_id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            target_readiness_score=target_readiness_score,
            target_date=target_date,
            daily_capacity_minutes=daily_capacity_minutes,
            created_at=now,
            updated_at=now,
        )
        upsert = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "student_id", "exam_id"],
            set_={
                "target_readiness_score": target_readiness_score,
                "target_date": target_date,
                "daily_capacity_minutes": daily_capacity_minutes,
                "updated_at": now,
            },
        ).returning(StudentPreparationGoalModel)
        result = await self._session.execute(upsert)
        return _map_row(result.scalar_one())

    async def get_goal(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationGoal | None:
        result = await self._session.execute(
            select(StudentPreparationGoalModel).where(
                StudentPreparationGoalModel.tenant_id == tenant_id,
                StudentPreparationGoalModel.student_id == student_id,
                StudentPreparationGoalModel.exam_id == exam_id,
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _map_row(row)
