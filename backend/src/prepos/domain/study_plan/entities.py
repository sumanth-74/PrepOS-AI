from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.scoring.common import round_score
from prepos.domain.study_plan.value_objects import ActivityType, ExecutionStatus


@dataclass(frozen=True, slots=True)
class DailyPlanItem:
    concept_id: str
    activity_type: ActivityType
    estimated_minutes: int
    priority_score: Decimal
    adaptive_priority: Decimal
    readiness_gain: Decimal
    adjustment_explanation: str = ""


@dataclass(frozen=True, slots=True)
class StudyPlanExecutionRecord:
    id: UUID
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    concept_id: str
    activity_type: ActivityType
    planned_minutes: int
    actual_minutes: int
    status: ExecutionStatus
    completed_at: datetime


@dataclass(frozen=True, slots=True)
class WeeklyPlanItem:
    concept_id: str
    target_sessions: int
    estimated_minutes: int
    readiness_gain: Decimal


@dataclass(frozen=True, slots=True)
class StudyPlan:
    tenant_id: UUID
    student_id: UUID
    exam_id: str
    generated_at: datetime
    daily_plan: tuple[DailyPlanItem, ...]
    weekly_plan: tuple[WeeklyPlanItem, ...]

    @property
    def total_estimated_gain(self) -> Decimal:
        return round_score(
            sum((item.readiness_gain for item in self.weekly_plan), start=Decimal("0")),
        )
