from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.domain.study_plan.behavior_metrics_v1 import StudyBehaviorMetrics
from prepos.domain.study_plan.entities import StudyPlan, StudyPlanExecutionRecord


@dataclass(frozen=True, slots=True)
class StudyPlanSummary:
    generated_at: datetime | None
    daily_item_count: int
    weekly_item_count: int
    total_estimated_gain: Decimal


@dataclass(frozen=True, slots=True)
class StudyBehaviorSummary:
    completion_rate: Decimal
    skip_rate: Decimal
    average_minutes_variance: Decimal


class StudyPlanRepositoryPort(ABC):
    @abstractmethod
    async def upsert_study_plan(self, plan: StudyPlan) -> StudyPlan:
        raise NotImplementedError

    @abstractmethod
    async def get_study_plan(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def get_study_plan_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> StudyPlan | None:
        raise NotImplementedError

    @abstractmethod
    async def get_study_plan_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlanSummary | None:
        raise NotImplementedError


class StudyPlanExecutionRepositoryPort(ABC):
    @abstractmethod
    async def insert_execution(self, record: StudyPlanExecutionRecord) -> StudyPlanExecutionRecord:
        raise NotImplementedError

    @abstractmethod
    async def list_executions(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> tuple[StudyPlanExecutionRecord, ...]:
        raise NotImplementedError

    @abstractmethod
    async def get_behavior_metrics(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorMetrics:
        raise NotImplementedError

    @abstractmethod
    async def get_behavior_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorSummary:
        raise NotImplementedError
