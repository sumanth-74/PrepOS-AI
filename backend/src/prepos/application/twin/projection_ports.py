from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.study_plan.ports import StudyBehaviorSummary, StudyPlanSummary
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1
from prepos.domain.scoring.readiness_v1_1 import ReadinessResultV1_1
from prepos.domain.twin.entities import PersistedTwinRecommendation
from prepos.domain.twin.projection_metrics import TwinProjectionMetrics
from prepos.domain.twin.snapshot_entities import PreparationTwin


@dataclass(frozen=True, slots=True)
class ForecastSummary:
    target_readiness_score: Decimal
    target_date: object
    current_readiness: Decimal
    projected_readiness: Decimal
    gap_to_goal: Decimal
    on_track: bool
    days_remaining: int
    explanation: str


@dataclass(frozen=True, slots=True)
class DecisionSummary:
    decision_type: str
    decision_score: Decimal
    expected_readiness_gain: Decimal
    expected_score_gain: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class InterventionSummary:
    intervention_type: str
    intervention_score: Decimal
    urgency: str
    expected_readiness_gain: Decimal
    title: str
    description: str


@dataclass(frozen=True, slots=True)
class InterventionOutcomeSummary:
    last_effectiveness_score: Decimal
    outcome_status: str
    explanation: str
    best_intervention: str
    historical_effectiveness: Decimal
    optimized_intervention_score: Decimal
    readiness_delta: Decimal


@dataclass(frozen=True, slots=True)
class MentorSummary:
    mentor_status: str
    top_mentor_message: str
    mentor_payload: dict[str, object]


@dataclass(frozen=True, slots=True)
class MentorActionSummary:
    mentor_action_type: str
    mentor_action_priority: Decimal
    escalation_level: str
    mentor_payload_patch: dict[str, object]


@dataclass(frozen=True, slots=True)
class MentorCaseSummary:
    active_case_status: str | None
    active_case_priority: str | None
    mentor_payload_patch: dict[str, object]


@dataclass(frozen=True, slots=True)
class PersonalizationSummary:
    learning_style: str
    risk_profile: str
    top_multiplier: Decimal
    best_activity_type: str
    historical_effectiveness: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class BehaviorProfileSummary:
    consistency_score: Decimal
    discipline_score: Decimal
    revision_adherence_score: Decimal
    weakness_recovery_score: Decimal
    engagement_score: Decimal
    learning_style: str
    risk_profile: str
    explanation: str


@dataclass(frozen=True, slots=True)
class ForecastProbabilitySummary:
    goal_probability: Decimal
    goal_likelihood: str
    best_case: Decimal
    expected: Decimal
    worst_case: Decimal
    optimistic_score: Decimal
    expected_score: Decimal
    pessimistic_score: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class MilestoneSummary:
    required_gain: Decimal
    expected_daily_progress: Decimal
    expected_weekly_progress: Decimal
    milestones: tuple[dict[str, object], ...]
    milestone_status: str
    current_gap: Decimal
    next_milestone_date: object | None
    next_milestone_target: Decimal | None
    explanation: str


@dataclass(frozen=True, slots=True)
class PredictedScoreSummary:
    expected_score: Decimal
    low_score: Decimal
    high_score: Decimal
    risk_level: str
    current_state: Decimal
    complete_recommendations: Decimal
    no_study: Decimal
    explanation: str


@dataclass(frozen=True, slots=True)
class ReadinessSummary:
    snapshot: LearningGraphReadinessSnapshot
    readiness_result: ReadinessResultV1_1
    drivers: ReadinessDriversV1 | None


@dataclass(frozen=True, slots=True)
class RevisionQueueSummary:
    due_revision_count: int
    high_risk_concept_count: int


@dataclass(frozen=True, slots=True)
class RecommendationSummary:
    recommendation_count: int
    last_recommendation_at: datetime | None
    top_recommendations: tuple[PersistedTwinRecommendation, ...]


class ReadinessSummaryPort(ABC):
    @abstractmethod
    async def get_readiness_summary(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> ReadinessSummary:
        raise NotImplementedError


class RevisionQueueSummaryPort(ABC):
    @abstractmethod
    async def get_revision_queue_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> RevisionQueueSummary:
        raise NotImplementedError


class TwinRecommendationSummaryPort(ABC):
    @abstractmethod
    async def get_recommendation_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        top_limit: int = 10,
    ) -> RecommendationSummary:
        raise NotImplementedError


class StudyPlanSummaryPort(ABC):
    @abstractmethod
    async def get_study_plan_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlanSummary | None:
        raise NotImplementedError


class StudyBehaviorSummaryPort(ABC):
    @abstractmethod
    async def get_behavior_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorSummary:
        raise NotImplementedError


class ForecastSummaryPort(ABC):
    @abstractmethod
    async def get_forecast_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> ForecastSummary | None:
        raise NotImplementedError


class DecisionSummaryPort(ABC):
    @abstractmethod
    async def get_decision_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> DecisionSummary | None:
        raise NotImplementedError


class InterventionSummaryPort(ABC):
    @abstractmethod
    async def get_intervention_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> InterventionSummary | None:
        raise NotImplementedError


class InterventionOutcomeSummaryPort(ABC):
    @abstractmethod
    async def get_intervention_outcome_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> InterventionOutcomeSummary | None:
        raise NotImplementedError


class BehaviorProfileSummaryPort(ABC):
    @abstractmethod
    async def get_behavior_profile_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> BehaviorProfileSummary:
        raise NotImplementedError


class PersonalizationSummaryPort(ABC):
    @abstractmethod
    async def get_personalization_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> PersonalizationSummary:
        raise NotImplementedError


class MentorSummaryPort(ABC):
    @abstractmethod
    async def get_mentor_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorSummary | None:
        raise NotImplementedError


class MentorActionSummaryPort(ABC):
    @abstractmethod
    async def get_mentor_action_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorActionSummary | None:
        raise NotImplementedError


class MentorCaseSummaryPort(ABC):
    @abstractmethod
    async def get_mentor_case_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorCaseSummary | None:
        raise NotImplementedError


@dataclass(frozen=True, slots=True)
class MentorEffectivenessSummary:
    mentor_payload_patch: dict[str, object]


class MentorEffectivenessSummaryPort(ABC):
    @abstractmethod
    async def get_mentor_effectiveness_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorEffectivenessSummary | None:
        raise NotImplementedError


class ForecastProbabilitySummaryPort(ABC):
    @abstractmethod
    async def get_forecast_probability_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> ForecastProbabilitySummary | None:
        raise NotImplementedError


class MilestoneSummaryPort(ABC):
    @abstractmethod
    async def get_milestone_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MilestoneSummary | None:
        raise NotImplementedError


class PredictedScoreSummaryPort(ABC):
    @abstractmethod
    async def get_predicted_score_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> PredictedScoreSummary | None:
        raise NotImplementedError


class TwinProjectionRepositoryPort(ABC):
    @abstractmethod
    async def resolve_twin_id(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> UUID | None:
        raise NotImplementedError

    @abstractmethod
    async def upsert_projection(self, twin: PreparationTwin) -> PreparationTwin:
        raise NotImplementedError

    @abstractmethod
    async def get_projection(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> PreparationTwin | None:
        raise NotImplementedError

    @abstractmethod
    async def get_projection_for_student(
        self,
        tenant_id: UUID,
        student_id: UUID,
    ) -> PreparationTwin | None:
        raise NotImplementedError

    @abstractmethod
    async def is_stale_learning_graph_event(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        concept_id: str,
        row_version: int,
    ) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def persist_partial_projection(
        self,
        twin: PreparationTwin,
        *,
        learning_graph_node_version: tuple[str, int] | None = None,
        increment_revision: bool = True,
    ) -> PreparationTwin:
        raise NotImplementedError

    @abstractmethod
    async def record_projection_metric(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        rebuild_count: int = 0,
        skipped_rebuild_count: int = 0,
        incremental_update_count: int = 0,
        lock_contention_count: int = 0,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_projection_metrics(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> TwinProjectionMetrics | None:
        raise NotImplementedError
