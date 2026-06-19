from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.goal.forecast_service import ForecastService
from prepos.application.goal.milestone_service import MilestoneService, _serialize_milestones
from prepos.application.learning_graph.read_services import LearningGraphReadService
from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.application.mentor.mentor_case_service import MentorCaseService
from prepos.application.mentor.mentor_effectiveness_learning_service import (
    MentorEffectivenessLearningService,
)
from prepos.application.mentor.mentor_service import MentorService
from prepos.application.revision_queue.ports import RevisionQueueRepositoryPort
from prepos.application.scoring.forecast_probability_service import ForecastProbabilityService
from prepos.application.scoring.predicted_score_service import PredictedScoreService
from prepos.application.study_plan.ports import (
    StudyBehaviorSummary,
    StudyPlanExecutionRepositoryPort,
    StudyPlanRepositoryPort,
    StudyPlanSummary,
)
from prepos.application.twin.behavior_profile_service import BehaviorProfileService
from prepos.application.twin.decision_service import TwinDecisionService
from prepos.application.twin.intervention_history_ports import InterventionHistoryRepositoryPort
from prepos.application.twin.intervention_optimization_service import InterventionOptimizationService
from prepos.application.twin.intervention_service import TwinInterventionService
from prepos.application.twin.personalization_service import PersonalizationService
from prepos.application.twin.ports import TwinRecommendationRepositoryPort
from prepos.application.twin.projection_ports import (
    BehaviorProfileSummary,
    BehaviorProfileSummaryPort,
    DecisionSummary,
    DecisionSummaryPort,
    ForecastProbabilitySummary,
    ForecastProbabilitySummaryPort,
    ForecastSummary,
    ForecastSummaryPort,
    InterventionOutcomeSummary,
    InterventionOutcomeSummaryPort,
    InterventionSummary,
    InterventionSummaryPort,
    MentorActionSummary,
    MentorActionSummaryPort,
    MentorCaseSummary,
    MentorCaseSummaryPort,
    MentorEffectivenessSummary,
    MentorEffectivenessSummaryPort,
    MentorSummary,
    MentorSummaryPort,
    MilestoneSummary,
    MilestoneSummaryPort,
    PersonalizationSummary,
    PersonalizationSummaryPort,
    PredictedScoreSummary,
    PredictedScoreSummaryPort,
    ReadinessSummary,
    ReadinessSummaryPort,
    RecommendationSummary,
    RevisionQueueSummary,
    RevisionQueueSummaryPort,
    StudyBehaviorSummaryPort,
    StudyPlanSummaryPort,
    TwinRecommendationSummaryPort,
)
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.twin.intervention_outcome_explanations_v1 import explain_intervention_outcome_v1
from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType


class LearningGraphReadinessSummaryAdapter(ReadinessSummaryPort):
    def __init__(self, *, read_service: LearningGraphReadService) -> None:
        self._read_service = read_service

    async def get_readiness_summary(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        current_time: datetime | None = None,
    ) -> ReadinessSummary:
        now = current_time or datetime.now(UTC)
        snapshot_response = await self._read_service.get_readiness_snapshot(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=now,
        )
        lg_snapshot = LearningGraphReadinessSnapshot(
            average_mastery=snapshot_response.average_mastery,
            average_retention=snapshot_response.average_retention,
            average_confidence=snapshot_response.average_confidence,
            rated_node_count=snapshot_response.rated_node_count,
            total_node_count=snapshot_response.total_node_count,
        )
        readiness_result, drivers = compute_readiness_from_snapshot(lg_snapshot)
        return ReadinessSummary(
            snapshot=lg_snapshot,
            readiness_result=readiness_result,
            drivers=drivers,
        )


class RevisionQueueSummaryAdapter(RevisionQueueSummaryPort):
    def __init__(self, *, queue_repo: RevisionQueueRepositoryPort) -> None:
        self._queue_repo = queue_repo

    async def get_revision_queue_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> RevisionQueueSummary:
        due_revision_count = await self._queue_repo.count_due(
            tenant_id,
            student_id,
            exam_id=exam_id,
        )
        high_risk_concept_count = await self._queue_repo.count_high_risk(
            tenant_id,
            student_id,
            exam_id=exam_id,
        )
        return RevisionQueueSummary(
            due_revision_count=due_revision_count,
            high_risk_concept_count=high_risk_concept_count,
        )


class TwinRecommendationSummaryAdapter(TwinRecommendationSummaryPort):
    def __init__(self, *, recommendation_repo: TwinRecommendationRepositoryPort) -> None:
        self._recommendation_repo = recommendation_repo

    async def get_recommendation_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        top_limit: int = 10,
    ) -> RecommendationSummary:
        return await self._recommendation_repo.get_recommendation_summary(
            tenant_id,
            student_id,
            exam_id,
            top_limit=top_limit,
        )


class StudyPlanSummaryAdapter(StudyPlanSummaryPort):
    def __init__(self, *, study_plan_repo: StudyPlanRepositoryPort) -> None:
        self._study_plan_repo = study_plan_repo

    async def get_study_plan_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyPlanSummary | None:
        return await self._study_plan_repo.get_study_plan_summary(
            tenant_id,
            student_id,
            exam_id,
        )


class StudyBehaviorSummaryAdapter(StudyBehaviorSummaryPort):
    def __init__(self, *, execution_repo: StudyPlanExecutionRepositoryPort) -> None:
        self._execution_repo = execution_repo

    async def get_behavior_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
    ) -> StudyBehaviorSummary:
        return await self._execution_repo.get_behavior_summary(
            tenant_id,
            student_id,
            exam_id,
        )


class ForecastSummaryAdapter(ForecastSummaryPort):
    def __init__(self, *, forecast_service: ForecastService) -> None:
        self._forecast_service = forecast_service

    async def get_forecast_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> ForecastSummary | None:
        snapshot = await self._forecast_service.compute_forecast(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        return ForecastSummary(
            target_readiness_score=snapshot.target_readiness_score,
            target_date=snapshot.target_date,
            current_readiness=snapshot.current_readiness,
            projected_readiness=snapshot.projected_readiness,
            gap_to_goal=snapshot.gap_to_goal,
            on_track=snapshot.on_track,
            days_remaining=snapshot.days_remaining,
            explanation=snapshot.explanation,
        )


class DecisionSummaryAdapter(DecisionSummaryPort):
    def __init__(self, *, decision_service: TwinDecisionService) -> None:
        self._decision_service = decision_service

    async def get_decision_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> DecisionSummary | None:
        snapshot = await self._decision_service.compute_decision(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        decision = snapshot.decision
        return DecisionSummary(
            decision_type=decision.decision_type.value,
            decision_score=decision.decision_score,
            expected_readiness_gain=decision.expected_readiness_gain,
            expected_score_gain=decision.expected_score_gain,
            explanation=decision.explanation,
        )


class InterventionSummaryAdapter(InterventionSummaryPort):
    def __init__(self, *, intervention_service: TwinInterventionService) -> None:
        self._intervention_service = intervention_service

    async def get_intervention_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> InterventionSummary | None:
        snapshot = await self._intervention_service.compute_intervention(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        intervention = snapshot.intervention
        return InterventionSummary(
            intervention_type=intervention.intervention_type.value,
            intervention_score=intervention.intervention_score,
            urgency=intervention.urgency.value,
            expected_readiness_gain=intervention.expected_readiness_gain,
            title=intervention.title,
            description=intervention.description,
        )


class InterventionOutcomeSummaryAdapter(InterventionOutcomeSummaryPort):
    def __init__(
        self,
        *,
        optimization_service: InterventionOptimizationService,
        history_repo: InterventionHistoryRepositoryPort,
    ) -> None:
        self._optimization_service = optimization_service
        self._history_repo = history_repo

    async def get_intervention_outcome_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> InterventionOutcomeSummary | None:
        snapshot = await self._optimization_service.compute_optimization(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None
        latest = await self._history_repo.get_latest_outcome(tenant_id, student_id, exam_id)
        readiness_delta = latest.readiness_delta if latest is not None else Decimal("0")
        explanation = explain_intervention_outcome_v1(
            intervention_type=TwinInterventionType(latest.intervention_type if latest else snapshot.best_intervention),
            readiness_delta=readiness_delta,
            outcome_status=InterventionOutcomeStatus(snapshot.outcome_status),
        )
        return InterventionOutcomeSummary(
            last_effectiveness_score=snapshot.last_effectiveness_score,
            outcome_status=snapshot.outcome_status,
            explanation=explanation,
            best_intervention=snapshot.best_intervention,
            historical_effectiveness=snapshot.historical_effectiveness,
            optimized_intervention_score=snapshot.optimized_intervention_score,
            readiness_delta=readiness_delta,
        )


class BehaviorProfileSummaryAdapter(BehaviorProfileSummaryPort):
    def __init__(self, *, behavior_profile_service: BehaviorProfileService) -> None:
        self._behavior_profile_service = behavior_profile_service

    async def get_behavior_profile_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> BehaviorProfileSummary:
        snapshot = await self._behavior_profile_service.compute_profile(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        profile = snapshot.profile
        return BehaviorProfileSummary(
            consistency_score=profile.consistency_score,
            discipline_score=profile.discipline_score,
            revision_adherence_score=profile.revision_adherence_score,
            weakness_recovery_score=profile.weakness_recovery_score,
            engagement_score=profile.engagement_score,
            learning_style=profile.learning_style.value,
            risk_profile=profile.risk_profile.value,
            explanation=snapshot.explanation,
        )


class PersonalizationSummaryAdapter(PersonalizationSummaryPort):
    def __init__(self, *, personalization_service: PersonalizationService) -> None:
        self._personalization_service = personalization_service

    async def get_personalization_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> PersonalizationSummary:
        snapshot = await self._personalization_service.compute_personalization(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        summary = snapshot.summary
        return PersonalizationSummary(
            learning_style=summary.learning_style.value,
            risk_profile=summary.risk_profile.value,
            top_multiplier=summary.top_multiplier,
            best_activity_type=summary.best_activity_type.value,
            historical_effectiveness=summary.historical_effectiveness,
            explanation=snapshot.explanation,
        )


class MentorSummaryAdapter(MentorSummaryPort):
    def __init__(self, *, mentor_service: MentorService) -> None:
        self._mentor_service = mentor_service

    async def get_mentor_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorSummary | None:
        snapshot = await self._mentor_service.compute_mentor(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None
        return MentorSummary(
            mentor_status=snapshot.summary.overall_status.value,
            top_mentor_message=snapshot.summary.key_message,
            mentor_payload=snapshot.mentor_payload,
        )


class MentorActionSummaryAdapter(MentorActionSummaryPort):
    def __init__(self, *, mentor_service: MentorService) -> None:
        self._mentor_service = mentor_service

    async def get_mentor_action_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorActionSummary | None:
        snapshot = await self._mentor_service.compute_mentor_action(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        if snapshot is None:
            return None
        return MentorActionSummary(
            mentor_action_type=snapshot.action.action_type.value,
            mentor_action_priority=snapshot.action.priority_score,
            escalation_level=snapshot.escalation.level.value,
            mentor_payload_patch=snapshot.mentor_payload_patch,
        )


class MentorCaseSummaryAdapter(MentorCaseSummaryPort):
    def __init__(self, *, mentor_case_service: MentorCaseService) -> None:
        self._mentor_case_service = mentor_case_service

    async def get_mentor_case_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorCaseSummary | None:
        mentor_case, active_status, active_priority = (
            await self._mentor_case_service.get_active_case_payload(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
            )
        )
        patch: dict[str, object] = {}
        if mentor_case is not None:
            patch["mentor_case"] = mentor_case
        return MentorCaseSummary(
            active_case_status=active_status,
            active_case_priority=active_priority,
            mentor_payload_patch=patch,
        )


class MentorEffectivenessSummaryAdapter(MentorEffectivenessSummaryPort):
    def __init__(self, *, learning_service: MentorEffectivenessLearningService) -> None:
        self._learning_service = learning_service

    async def get_mentor_effectiveness_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MentorEffectivenessSummary | None:
        patch = await self._learning_service.get_student_effectiveness_payload(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
        )
        return MentorEffectivenessSummary(mentor_payload_patch=patch)


class ForecastProbabilitySummaryAdapter(ForecastProbabilitySummaryPort):
    def __init__(self, *, forecast_probability_service: ForecastProbabilityService) -> None:
        self._forecast_probability_service = forecast_probability_service

    async def get_forecast_probability_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> ForecastProbabilitySummary | None:
        snapshot = await self._forecast_probability_service.compute_forecast_probability(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        return ForecastProbabilitySummary(
            goal_probability=snapshot.goal_probability,
            goal_likelihood=snapshot.goal_likelihood.value,
            best_case=snapshot.best_case,
            expected=snapshot.expected,
            worst_case=snapshot.worst_case,
            optimistic_score=snapshot.optimistic_score,
            expected_score=snapshot.expected_score,
            pessimistic_score=snapshot.pessimistic_score,
            explanation=snapshot.explanation,
        )


class MilestoneSummaryAdapter(MilestoneSummaryPort):
    def __init__(self, *, milestone_service: MilestoneService) -> None:
        self._milestone_service = milestone_service

    async def get_milestone_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> MilestoneSummary | None:
        snapshot = await self._milestone_service.compute_milestones(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        return MilestoneSummary(
            required_gain=snapshot.required_gain,
            expected_daily_progress=snapshot.expected_daily_progress,
            expected_weekly_progress=snapshot.expected_weekly_progress,
            milestones=_serialize_milestones(snapshot.milestones),
            milestone_status=snapshot.milestone_status.value,
            current_gap=snapshot.current_gap,
            next_milestone_date=snapshot.next_milestone_date,
            next_milestone_target=snapshot.next_milestone_target,
            explanation=snapshot.explanation,
        )


class PredictedScoreSummaryAdapter(PredictedScoreSummaryPort):
    def __init__(self, *, predicted_score_service: PredictedScoreService) -> None:
        self._predicted_score_service = predicted_score_service

    async def get_predicted_score_summary(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        *,
        current_time: datetime | None = None,
    ) -> PredictedScoreSummary | None:
        snapshot = await self._predicted_score_service.compute_predicted_score(
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            current_time=current_time,
        )
        if snapshot is None:
            return None
        return PredictedScoreSummary(
            expected_score=snapshot.expected_score,
            low_score=snapshot.low_score,
            high_score=snapshot.high_score,
            risk_level=snapshot.risk_level.value,
            current_state=snapshot.current_state,
            complete_recommendations=snapshot.complete_recommendations,
            no_study=snapshot.no_study,
            explanation=snapshot.explanation,
        )
