from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.planning.ports import PlanningRepositoryPort
from prepos.infrastructure.db.models.adaptive_study_plan import (
    PlanningEventModel,
    StudyPlanItemModel,
    StudyPlanRevisionModel,
    StudyPlanVersionModel,
)


class SqlAlchemyPlanningRepository(PlanningRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def archive_active_plans(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        now: datetime,
    ) -> None:
        stmt = (
            update(StudyPlanVersionModel)
            .where(
                StudyPlanVersionModel.tenant_id == tenant_id,
                StudyPlanVersionModel.user_id == user_id,
                StudyPlanVersionModel.exam_id == exam_id,
                StudyPlanVersionModel.status == "active",
            )
            .values(status="archived", updated_at=now)
        )
        await self._session.execute(stmt)

    async def create_plan_version(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        student_id: UUID,
        exam_id: str,
        generated_at: datetime,
        valid_from: date,
        valid_to: date,
        readiness_snapshot: float | None,
        forecast_snapshot: float | None,
        status: str,
        now: datetime,
    ) -> UUID:
        plan_id = uuid4()
        self._session.add(
            StudyPlanVersionModel(
                id=plan_id,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                exam_id=exam_id,
                generated_at=generated_at,
                valid_from=valid_from,
                valid_to=valid_to,
                readiness_snapshot=readiness_snapshot,
                forecast_snapshot=forecast_snapshot,
                status=status,
                created_at=now,
                updated_at=now,
            )
        )
        await self._session.flush()
        return plan_id

    async def create_plan_items(
        self,
        *,
        plan_id: UUID,
        items: list[dict[str, object]],
        now: datetime,
    ) -> list[UUID]:
        ids: list[UUID] = []
        for item in items:
            item_id = uuid4()
            ids.append(item_id)
            self._session.add(
                StudyPlanItemModel(
                    id=item_id,
                    plan_id=plan_id,
                    concept_id=str(item["concept_id"]),
                    activity_type=str(item["activity_type"]),
                    priority_score=item["priority_score"],  # type: ignore[arg-type]
                    estimated_minutes=int(item["estimated_minutes"]),
                    estimated_readiness_gain=item["estimated_readiness_gain"],  # type: ignore[arg-type]
                    confidence=str(item["confidence"]),
                    scheduled_date=item["scheduled_date"],  # type: ignore[arg-type]
                    source_reason=str(item["source_reason"]),
                    completion_status="pending",
                    created_at=now,
                    updated_at=now,
                )
            )
        await self._session.flush()
        return ids

    async def create_revision(
        self,
        *,
        plan_id: UUID,
        concept_id: str,
        revision_reason: str,
        old_priority: float | None,
        new_priority: float | None,
        now: datetime,
    ) -> UUID:
        revision_id = uuid4()
        self._session.add(
            StudyPlanRevisionModel(
                id=revision_id,
                plan_id=plan_id,
                concept_id=concept_id,
                revision_reason=revision_reason,
                old_priority=old_priority,
                new_priority=new_priority,
                created_at=now,
            )
        )
        await self._session.flush()
        return revision_id

    async def get_current_plan(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
    ) -> dict[str, object] | None:
        stmt = (
            select(StudyPlanVersionModel)
            .where(
                StudyPlanVersionModel.tenant_id == tenant_id,
                StudyPlanVersionModel.user_id == user_id,
                StudyPlanVersionModel.exam_id == exam_id,
                StudyPlanVersionModel.status == "active",
            )
            .order_by(StudyPlanVersionModel.generated_at.desc())
            .limit(1)
        )
        result = await self._session.execute(stmt)
        plan = result.scalar_one_or_none()
        if plan is None:
            return None
        items_stmt = (
            select(StudyPlanItemModel)
            .where(StudyPlanItemModel.plan_id == plan.id)
            .order_by(StudyPlanItemModel.scheduled_date.asc(), StudyPlanItemModel.priority_score.desc())
        )
        items_result = await self._session.execute(items_stmt)
        items = items_result.scalars().all()
        revisions_stmt = (
            select(StudyPlanRevisionModel)
            .where(StudyPlanRevisionModel.plan_id == plan.id)
            .order_by(StudyPlanRevisionModel.created_at.desc())
            .limit(20)
        )
        revisions_result = await self._session.execute(revisions_stmt)
        revisions = revisions_result.scalars().all()
        return {
            "plan": plan,
            "items": items,
            "revisions": revisions,
        }

    async def list_plan_history(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        exam_id: str,
        limit: int,
    ) -> list[dict[str, object]]:
        stmt = (
            select(StudyPlanVersionModel)
            .where(
                StudyPlanVersionModel.tenant_id == tenant_id,
                StudyPlanVersionModel.user_id == user_id,
                StudyPlanVersionModel.exam_id == exam_id,
            )
            .order_by(StudyPlanVersionModel.generated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        plans = result.scalars().all()
        history: list[dict[str, object]] = []
        for plan in plans:
            count_stmt = select(func.count()).select_from(StudyPlanItemModel).where(
                StudyPlanItemModel.plan_id == plan.id
            )
            completed_stmt = select(func.count()).select_from(StudyPlanItemModel).where(
                StudyPlanItemModel.plan_id == plan.id,
                StudyPlanItemModel.completion_status == "completed",
            )
            total = int((await self._session.execute(count_stmt)).scalar_one())
            completed = int((await self._session.execute(completed_stmt)).scalar_one())
            history.append({"plan": plan, "item_count": total, "completed_count": completed})
        return history

    async def get_plan_item(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
    ) -> dict[str, object] | None:
        stmt = (
            select(StudyPlanItemModel, StudyPlanVersionModel)
            .join(StudyPlanVersionModel, StudyPlanItemModel.plan_id == StudyPlanVersionModel.id)
            .where(
                StudyPlanItemModel.id == item_id,
                StudyPlanVersionModel.tenant_id == tenant_id,
            )
        )
        result = await self._session.execute(stmt)
        row = result.first()
        if row is None:
            return None
        item, plan = row
        return {"item": item, "plan": plan}

    async def mark_item_completed(
        self,
        *,
        tenant_id: UUID,
        item_id: UUID,
        now: datetime,
    ) -> dict[str, object] | None:
        row = await self.get_plan_item(tenant_id=tenant_id, item_id=item_id)
        if row is None:
            return None
        item: StudyPlanItemModel = row["item"]  # type: ignore[assignment]
        item.completion_status = "completed"
        item.updated_at = now
        await self._session.flush()
        return row

    async def list_revisions(self, *, plan_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(StudyPlanRevisionModel)
            .where(StudyPlanRevisionModel.plan_id == plan_id)
            .order_by(StudyPlanRevisionModel.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return [{"revision": revision} for revision in result.scalars()]

    async def record_event(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID | None,
        student_id: UUID | None,
        plan_id: UUID | None,
        item_id: UUID | None,
        concept_id: str | None,
        event_type: str,
        priority_score: float | None,
        estimated_gain: float | None,
        metadata_json: dict[str, object],
        created_at: datetime,
    ) -> UUID:
        event_id = uuid4()
        self._session.add(
            PlanningEventModel(
                id=event_id,
                tenant_id=tenant_id,
                user_id=user_id,
                student_id=student_id,
                plan_id=plan_id,
                item_id=item_id,
                concept_id=concept_id,
                event_type=event_type,
                priority_score=priority_score,
                estimated_gain=estimated_gain,
                metadata_json=metadata_json,
                created_at=created_at,
            )
        )
        await self._session.flush()
        return event_id

    async def get_admin_metrics(self, *, tenant_id: UUID) -> dict[str, object]:
        total_stmt = select(func.count()).select_from(StudyPlanVersionModel).where(
            StudyPlanVersionModel.tenant_id == tenant_id
        )
        active_stmt = select(func.count()).select_from(StudyPlanVersionModel).where(
            StudyPlanVersionModel.tenant_id == tenant_id,
            StudyPlanVersionModel.status == "active",
        )
        since = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
        recent_stmt = select(func.count()).select_from(StudyPlanVersionModel).where(
            StudyPlanVersionModel.tenant_id == tenant_id,
            StudyPlanVersionModel.generated_at >= since - timedelta(days=30),
        )
        completed_stmt = select(func.count()).select_from(StudyPlanItemModel).join(
            StudyPlanVersionModel, StudyPlanItemModel.plan_id == StudyPlanVersionModel.id
        ).where(
            StudyPlanVersionModel.tenant_id == tenant_id,
            StudyPlanItemModel.completion_status == "completed",
        )
        total_items_stmt = select(func.count()).select_from(StudyPlanItemModel).join(
            StudyPlanVersionModel, StudyPlanItemModel.plan_id == StudyPlanVersionModel.id
        ).where(StudyPlanVersionModel.tenant_id == tenant_id)

        total_plans = int((await self._session.execute(total_stmt)).scalar_one())
        active_plans = int((await self._session.execute(active_stmt)).scalar_one())
        recent_plans = int((await self._session.execute(recent_stmt)).scalar_one())
        completed_items = int((await self._session.execute(completed_stmt)).scalar_one())
        total_items = int((await self._session.execute(total_items_stmt)).scalar_one())

        concept_stmt = (
            select(StudyPlanItemModel.concept_id, func.count())
            .join(StudyPlanVersionModel, StudyPlanItemModel.plan_id == StudyPlanVersionModel.id)
            .where(StudyPlanVersionModel.tenant_id == tenant_id)
            .group_by(StudyPlanItemModel.concept_id)
            .order_by(func.count().desc())
            .limit(5)
        )
        concept_rows = (await self._session.execute(concept_stmt)).all()

        event_stmt = (
            select(PlanningEventModel.event_type, func.count())
            .where(PlanningEventModel.tenant_id == tenant_id)
            .group_by(PlanningEventModel.event_type)
        )
        event_rows = (await self._session.execute(event_stmt)).all()

        completion_rate = round(completed_items / total_items, 4) if total_items else 0.0
        return {
            "total_plans": total_plans,
            "active_plans": active_plans,
            "plans_generated_last_30_days": recent_plans,
            "average_completion_rate": completion_rate,
            "average_adherence": completion_rate,
            "top_scheduled_concepts": [
                {"concept_id": concept_id, "count": count} for concept_id, count in concept_rows
            ],
            "event_counts": [{"event_type": event_type, "count": count} for event_type, count in event_rows],
        }

    async def export_rows(self, *, tenant_id: UUID, limit: int) -> list[dict[str, object]]:
        stmt = (
            select(
                StudyPlanItemModel,
                StudyPlanVersionModel.id.label("plan_id"),
            )
            .join(StudyPlanVersionModel, StudyPlanItemModel.plan_id == StudyPlanVersionModel.id)
            .where(StudyPlanVersionModel.tenant_id == tenant_id)
            .order_by(StudyPlanItemModel.scheduled_date.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows: list[dict[str, object]] = []
        for item, plan_id in result.all():
            rows.append(
                {
                    "plan_id": plan_id,
                    "concept_id": item.concept_id,
                    "priority_score": float(item.priority_score),
                    "scheduled_date": item.scheduled_date.isoformat(),
                    "completion_status": item.completion_status,
                    "event_type": "plan_item",
                }
            )
        return rows
