from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast
from uuid import UUID, uuid4

from sqlalchemy import ColumnElement, and_, delete, func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.domain.revision_queue.entities import RevisionQueueItem
from prepos.domain.revision_queue.value_objects import RevisionQueueStatus
from prepos.infrastructure.db.models.revision_queue import StudentRevisionQueueModel

_HIGH_RISK_WEAKNESS = Decimal("70")


def _map_row(row: StudentRevisionQueueModel) -> RevisionQueueItem:
    return RevisionQueueItem(
        id=row.id,
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        concept_id=row.concept_id,
        next_review_at=row.next_review_at,
        retention_score=row.retention_score,
        importance_score=row.importance_score,
        weakness_score=row.weakness_score,
        priority_score=row.priority_score,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyRevisionQueueRepository(RevisionQueueRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_queue_item(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        next_review_at: datetime,
        retention_score: Decimal | None,
        importance_score: Decimal,
        weakness_score: Decimal | None,
        priority_score: Decimal,
        status: str,
    ) -> RevisionQueueItem:
        now = datetime.now(UTC)
        row_id = uuid4()
        stmt = insert(StudentRevisionQueueModel).values(
            id=row_id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            concept_id=concept_id,
            next_review_at=next_review_at,
            retention_score=retention_score,
            importance_score=importance_score,
            weakness_score=weakness_score,
            priority_score=priority_score,
            status=status,
            created_at=now,
            updated_at=now,
        )
        upsert_stmt = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "student_id", "concept_id"],
            set_={
                "exam_id": exam_id,
                "next_review_at": next_review_at,
                "retention_score": retention_score,
                "importance_score": importance_score,
                "weakness_score": weakness_score,
                "priority_score": priority_score,
                "status": status,
                "updated_at": now,
            },
        ).returning(StudentRevisionQueueModel)
        result = await self._session.execute(upsert_stmt)
        row = result.scalar_one()
        return _map_row(row)

    async def delete_queue_item(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> bool:
        result = cast(
            CursorResult[Any],
            await self._session.execute(
                delete(StudentRevisionQueueModel).where(
                    StudentRevisionQueueModel.tenant_id == tenant_id,
                    StudentRevisionQueueModel.student_id == student_id,
                    StudentRevisionQueueModel.concept_id == concept_id,
                )
            ),
        )
        return int(result.rowcount or 0) > 0

    def _base_filters(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None,
    ) -> list[ColumnElement[bool]]:
        filters: list[ColumnElement[bool]] = [
            StudentRevisionQueueModel.tenant_id == tenant_id,
            StudentRevisionQueueModel.student_id == student_id,
        ]
        if exam_id is not None:
            filters.append(StudentRevisionQueueModel.exam_id == exam_id)
        return filters

    async def list_due(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> tuple[RevisionQueueItem, ...]:
        filters = self._base_filters(tenant_id, student_id, exam_id=exam_id)
        filters.append(StudentRevisionQueueModel.status == RevisionQueueStatus.DUE)
        result = await self._session.execute(
            select(StudentRevisionQueueModel)
            .where(and_(*filters))
            .order_by(
                StudentRevisionQueueModel.priority_score.desc(),
                StudentRevisionQueueModel.next_review_at.asc(),
            )
            .limit(limit)
        )
        return tuple(_map_row(row) for row in result.scalars().all())

    async def list_upcoming(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 50,
    ) -> tuple[RevisionQueueItem, ...]:
        filters = self._base_filters(tenant_id, student_id, exam_id=exam_id)
        filters.append(StudentRevisionQueueModel.status == RevisionQueueStatus.SCHEDULED)
        result = await self._session.execute(
            select(StudentRevisionQueueModel)
            .where(and_(*filters))
            .order_by(
                StudentRevisionQueueModel.next_review_at.asc(),
                StudentRevisionQueueModel.priority_score.desc(),
            )
            .limit(limit)
        )
        return tuple(_map_row(row) for row in result.scalars().all())

    async def list_queue(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        limit: int = 100,
    ) -> tuple[RevisionQueueItem, ...]:
        filters = self._base_filters(tenant_id, student_id, exam_id=exam_id)
        filters.append(
            StudentRevisionQueueModel.status.in_(
                [RevisionQueueStatus.DUE, RevisionQueueStatus.SCHEDULED]
            )
        )
        result = await self._session.execute(
            select(StudentRevisionQueueModel)
            .where(and_(*filters))
            .order_by(
                StudentRevisionQueueModel.priority_score.desc(),
                StudentRevisionQueueModel.next_review_at.asc(),
            )
            .limit(limit)
        )
        return tuple(_map_row(row) for row in result.scalars().all())

    async def count_due(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
    ) -> int:
        filters = self._base_filters(tenant_id, student_id, exam_id=exam_id)
        filters.append(StudentRevisionQueueModel.status == RevisionQueueStatus.DUE)
        result = await self._session.execute(
            select(func.count()).select_from(StudentRevisionQueueModel).where(and_(*filters))
        )
        return int(result.scalar_one())

    async def count_high_risk(
        self,
        tenant_id: UUID,
        student_id: UUID,
        *,
        exam_id: str | None = None,
        weakness_threshold: Decimal | None = None,
    ) -> int:
        threshold = weakness_threshold or _HIGH_RISK_WEAKNESS
        filters = self._base_filters(tenant_id, student_id, exam_id=exam_id)
        filters.append(StudentRevisionQueueModel.weakness_score >= threshold)
        filters.append(
            StudentRevisionQueueModel.status.in_(
                [RevisionQueueStatus.DUE, RevisionQueueStatus.SCHEDULED]
            )
        )
        result = await self._session.execute(
            select(func.count()).select_from(StudentRevisionQueueModel).where(and_(*filters))
        )
        return int(result.scalar_one())
