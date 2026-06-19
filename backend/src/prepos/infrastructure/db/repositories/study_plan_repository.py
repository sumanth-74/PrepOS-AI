from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.study_plan.ports import StudyPlanRepositoryPort, StudyPlanSummary
from prepos.domain.study_plan.entities import DailyPlanItem, StudyPlan, WeeklyPlanItem
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.infrastructure.db.models.study_plan import StudentStudyPlanModel


def _daily_to_json(items: tuple[DailyPlanItem, ...]) -> list[dict[str, object]]:
    return [
        {
            "concept_id": item.concept_id,
            "activity_type": item.activity_type.value,
            "estimated_minutes": item.estimated_minutes,
            "priority_score": float(item.priority_score),
            "adaptive_priority": float(item.adaptive_priority),
            "readiness_gain": float(item.readiness_gain),
            "adjustment_explanation": item.adjustment_explanation,
        }
        for item in items
    ]


def _weekly_to_json(items: tuple[WeeklyPlanItem, ...]) -> list[dict[str, object]]:
    return [
        {
            "concept_id": item.concept_id,
            "target_sessions": item.target_sessions,
            "estimated_minutes": item.estimated_minutes,
            "readiness_gain": float(item.readiness_gain),
        }
        for item in items
    ]


def _map_daily(items: list[dict[str, object]]) -> tuple[DailyPlanItem, ...]:
    mapped: list[DailyPlanItem] = []
    for item in items:
        priority_score = Decimal(str(item["priority_score"]))
        adaptive_raw = item.get("adaptive_priority")
        adaptive_priority = Decimal(str(adaptive_raw)) if adaptive_raw is not None else priority_score
        explanation_raw = item.get("adjustment_explanation")
        adjustment_explanation = str(explanation_raw) if explanation_raw is not None else ""
        mapped.append(
            DailyPlanItem(
                concept_id=str(item["concept_id"]),
                activity_type=ActivityType(str(item["activity_type"])),
                estimated_minutes=int(str(item["estimated_minutes"])),
                priority_score=priority_score,
                adaptive_priority=adaptive_priority,
                readiness_gain=Decimal(str(item["readiness_gain"])),
                adjustment_explanation=adjustment_explanation,
            )
        )
    return tuple(mapped)


def _map_weekly(items: list[dict[str, object]]) -> tuple[WeeklyPlanItem, ...]:
    mapped: list[WeeklyPlanItem] = []
    for item in items:
        mapped.append(
            WeeklyPlanItem(
                concept_id=str(item["concept_id"]),
                target_sessions=int(str(item["target_sessions"])),
                estimated_minutes=int(str(item["estimated_minutes"])),
                readiness_gain=Decimal(str(item["readiness_gain"])),
            )
        )
    return tuple(mapped)


def _map_row(row: StudentStudyPlanModel) -> StudyPlan:
    return StudyPlan(
        tenant_id=row.tenant_id,
        student_id=row.student_id,
        exam_id=row.exam_id,
        generated_at=row.generated_at,
        daily_plan=_map_daily(list(row.daily_plan_json or [])),
        weekly_plan=_map_weekly(list(row.weekly_plan_json or [])),
    )


class SqlAlchemyStudyPlanRepository(StudyPlanRepositoryPort):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_study_plan(self, plan: StudyPlan) -> StudyPlan:
        now = datetime.now(UTC)
        plan_id = uuid4()
        total_gain = plan.total_estimated_gain
        stmt = insert(StudentStudyPlanModel).values(
            id=plan_id,
            tenant_id=plan.tenant_id,
            student_id=plan.student_id,
            exam_id=plan.exam_id,
            generated_at=plan.generated_at,
            daily_plan_json=_daily_to_json(plan.daily_plan),
            weekly_plan_json=_weekly_to_json(plan.weekly_plan),
            total_estimated_gain=total_gain,
            created_at=now,
            updated_at=now,
        )
        upsert = stmt.on_conflict_do_update(
            index_elements=["tenant_id", "student_id", "exam_id"],
            set_={
                "generated_at": plan.generated_at,
                "daily_plan_json": _daily_to_json(plan.daily_plan),
                "weekly_plan_json": _weekly_to_json(plan.weekly_plan),
                "total_estimated_gain": total_gain,
                "updated_at": now,
            },
        ).returning(StudentStudyPlanModel)
        result = await self._session.execute(upsert)
        return _map_row(result.scalar_one())

    async def _get_model(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudentStudyPlanModel | None:
        result = await self._session.execute(
            select(StudentStudyPlanModel).where(
                StudentStudyPlanModel.tenant_id == tenant_id,
                StudentStudyPlanModel.student_id == student_id,
                StudentStudyPlanModel.exam_id == exam_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_study_plan(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlan | None:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None:
            return None
        return _map_row(row)

    async def get_study_plan_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> StudyPlan | None:
        result = await self._session.execute(
            select(StudentStudyPlanModel)
            .where(
                StudentStudyPlanModel.tenant_id == tenant_id,
                StudentStudyPlanModel.student_id == student_id,
            )
            .order_by(StudentStudyPlanModel.generated_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        return _map_row(row)

    async def get_study_plan_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlanSummary | None:
        row = await self._get_model(tenant_id, student_id, exam_id)
        if row is None:
            return None
        daily_count = len(row.daily_plan_json or [])
        weekly_count = len(row.weekly_plan_json or [])
        return StudyPlanSummary(
            generated_at=row.generated_at,
            daily_item_count=daily_count,
            weekly_item_count=weekly_count,
            total_estimated_gain=row.total_estimated_gain,
        )
