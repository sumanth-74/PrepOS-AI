from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from prepos.application.twin.projection_ports import (
    BehaviorProfileSummaryPort,
    DecisionSummaryPort,
    ForecastProbabilitySummaryPort,
    ForecastSummaryPort,
    InterventionOutcomeSummaryPort,
    InterventionSummaryPort,
    MentorActionSummaryPort,
    MentorCaseSummaryPort,
    MentorEffectivenessSummaryPort,
    MentorSummaryPort,
    MilestoneSummaryPort,
    PersonalizationSummaryPort,
    PredictedScoreSummaryPort,
    ReadinessSummaryPort,
    RevisionQueueSummaryPort,
    StudyBehaviorSummaryPort,
    StudyPlanSummaryPort,
    TwinProjectionRepositoryPort,
    TwinRecommendationSummaryPort,
)
from prepos.domain.study_plan.value_objects import ActivityType
from prepos.domain.twin.behavior_profile_types_v1 import LearningStyle, RiskProfile
from prepos.domain.twin.personalized_scoring_v1 import (
    PersonalizationSummary,
    build_personalization_payload_section,
)
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.projection_sections import TwinProjectionSection
from prepos.domain.twin.snapshot_entities import PreparationTwin
from prepos.domain.twin.snapshot_events import TwinSnapshotUpdated
from prepos.domain.twin.twin_events import TwinUpdated
from prepos.domain.twin.twin_payload_v1 import (
    TwinReadinessPayloadInputs,
    TwinRecommendationsPayloadInputs,
    TwinRevisionQueuePayloadInputs,
    build_behavior_profile_payload_section,
    build_decision_payload_section,
    build_forecast_payload_section,
    build_forecast_probability_payload_section,
    build_forecast_scenarios_payload_section,
    build_goal_payload_section,
    build_intervention_baseline_payload_section,
    build_intervention_effectiveness_payload_section,
    build_intervention_payload_section,
    build_milestone_status_payload_section,
    build_milestones_payload_section,
    build_optimization_payload_section,
    build_predicted_outcome_payload_section,
    build_queue_payload_section,
    build_readiness_payload_section,
    build_recommendations_payload_section,
    build_score_distribution_payload_section,
    build_simulations_payload_section,
    build_study_behavior_payload_section,
    build_study_plan_payload_section,
    build_trajectory_payload_section,
    extract_baseline_metrics,
    merge_twin_payload_sections,
)
from prepos.events.outbox.publisher import OutboxPublisher


class TwinProjectionBuilder:
    """Incremental Preparation Twin projection builder."""

    def __init__(
        self,
        *,
        readiness_port: ReadinessSummaryPort,
        queue_port: RevisionQueueSummaryPort,
        recommendation_port: TwinRecommendationSummaryPort,
        study_plan_port: StudyPlanSummaryPort,
        behavior_port: StudyBehaviorSummaryPort,
        forecast_port: ForecastSummaryPort,
        predicted_score_port: PredictedScoreSummaryPort,
        milestone_port: MilestoneSummaryPort,
        forecast_probability_port: ForecastProbabilitySummaryPort,
        decision_port: DecisionSummaryPort,
        intervention_port: InterventionSummaryPort,
        intervention_outcome_port: InterventionOutcomeSummaryPort,
        behavior_profile_port: BehaviorProfileSummaryPort,
        personalization_port: PersonalizationSummaryPort,
        mentor_port: MentorSummaryPort,
        mentor_action_port: MentorActionSummaryPort,
        mentor_case_port: MentorCaseSummaryPort,
        mentor_effectiveness_port: MentorEffectivenessSummaryPort,
        projection_repo: TwinProjectionRepositoryPort,
        outbox: OutboxPublisher,
    ) -> None:
        self._readiness_port = readiness_port
        self._queue_port = queue_port
        self._recommendation_port = recommendation_port
        self._study_plan_port = study_plan_port
        self._behavior_port = behavior_port
        self._forecast_port = forecast_port
        self._predicted_score_port = predicted_score_port
        self._milestone_port = milestone_port
        self._forecast_probability_port = forecast_probability_port
        self._decision_port = decision_port
        self._intervention_port = intervention_port
        self._intervention_outcome_port = intervention_outcome_port
        self._behavior_profile_port = behavior_profile_port
        self._personalization_port = personalization_port
        self._mentor_port = mentor_port
        self._mentor_action_port = mentor_action_port
        self._mentor_case_port = mentor_case_port
        self._mentor_effectiveness_port = mentor_effectiveness_port
        self._projection_repo = projection_repo
        self._outbox = outbox

    async def apply_incremental_update(
        self,
        *,
        section: TwinProjectionSection,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        concept_id: str | None = None,
        learning_graph_row_version: int | None = None,
        current_time: datetime | None = None,
    ) -> PreparationTwin | None:
        now = current_time or datetime.now(UTC)
        if (
            section == TwinProjectionSection.READINESS
            and concept_id is not None
            and learning_graph_row_version is not None
            and await self._projection_repo.is_stale_learning_graph_event(
                tenant_id,
                student_id,
                exam_id,
                concept_id,
                learning_graph_row_version,
            )
        ):
            await self._projection_repo.record_projection_metric(
                tenant_id,
                student_id,
                exam_id,
                skipped_rebuild_count=1,
            )
            return None
        if section == TwinProjectionSection.READINESS:
            return await self._update_readiness_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                concept_id=concept_id,
                learning_graph_row_version=learning_graph_row_version,
                current_time=now,
            )
        if section == TwinProjectionSection.RECOMMENDATIONS:
            return await self._update_recommendations_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.QUEUE:
            return await self._update_queue_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.FORECAST:
            return await self._update_forecast_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.PREDICTED_SCORE:
            return await self._update_predicted_score_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.MILESTONES:
            return await self._update_milestones_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.FORECAST_PROBABILITY:
            return await self._update_forecast_probability_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.DECISION:
            return await self._update_decision_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.INTERVENTION:
            return await self._update_intervention_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.INTERVENTION_OUTCOME:
            return await self._update_intervention_outcome_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.BEHAVIOR_PROFILE:
            return await self._update_behavior_profile_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.PERSONALIZATION:
            return await self._update_personalization_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.MENTOR:
            return await self._update_mentor_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.MENTOR_ACTION:
            return await self._update_mentor_action_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.MENTOR_CASE:
            return await self._update_mentor_case_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.MENTOR_EFFECTIVENESS:
            return await self._update_mentor_effectiveness_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        if section == TwinProjectionSection.STUDY_PLAN:
            return await self._update_study_plan_section(
                tenant_id=tenant_id,
                student_id=student_id,
                exam_id=exam_id,
                correlation_id=correlation_id,
                causation_id=causation_id,
                current_time=now,
            )
        return None

    async def _load_existing_shell(
        self,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        now: datetime,
    ) -> PreparationTwin:
        existing = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        if existing is not None:
            return existing
        twin_id = await self._projection_repo.resolve_twin_id(tenant_id, student_id, exam_id)
        return PreparationTwin(
            id=twin_id or uuid4(),
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=None,
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
            rated_node_count=0,
            due_revision_count=0,
            high_risk_concept_count=0,
            largest_positive_driver=None,
            largest_negative_driver=None,
            recommendation_count=0,
            last_recommendation_at=None,
            twin_payload={"profile_version": TWIN_PROFILE_V1},
            generated_at=now,
        )

    async def _update_readiness_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        concept_id: str | None,
        learning_graph_row_version: int | None,
        current_time: datetime,
    ) -> PreparationTwin:
        readiness = await self._readiness_port.get_readiness_summary(
            tenant_id=tenant_id,
            student_id=student_id,
            current_time=current_time,
        )
        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        readiness_section, drivers_section = build_readiness_payload_section(
            readiness=TwinReadinessPayloadInputs(
                result=readiness.readiness_result,
                drivers=readiness.drivers,
            ),
            drivers=readiness.drivers,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            readiness=readiness_section,
            drivers=drivers_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=readiness.readiness_result.overall_score,
            average_mastery=readiness.snapshot.average_mastery,
            average_retention=readiness.snapshot.average_retention,
            average_confidence=readiness.snapshot.average_confidence,
            rated_node_count=readiness.snapshot.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=readiness.drivers.largest_positive_driver if readiness.drivers else None,
            largest_negative_driver=readiness.drivers.largest_negative_driver if readiness.drivers else None,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        lg_version = (
            (concept_id, learning_graph_row_version)
            if concept_id is not None and learning_graph_row_version is not None
            else None
        )
        persisted = await self._projection_repo.persist_partial_projection(
            updated,
            learning_graph_node_version=lg_version,
        )
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_recommendations_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin:
        recommendation_summary = await self._recommendation_port.get_recommendation_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        recommendations_section = build_recommendations_payload_section(
            TwinRecommendationsPayloadInputs(
                recommendation_count=recommendation_summary.recommendation_count,
                last_recommendation_at=recommendation_summary.last_recommendation_at,
                top_recommendations=recommendation_summary.top_recommendations,
            )
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            recommendations=recommendations_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=recommendation_summary.recommendation_count,
            last_recommendation_at=recommendation_summary.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_queue_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin:
        queue_summary = await self._queue_port.get_revision_queue_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        queue_section = build_queue_payload_section(
            TwinRevisionQueuePayloadInputs(
                due_revision_count=queue_summary.due_revision_count,
                high_risk_concept_count=queue_summary.high_risk_concept_count,
            )
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            revision_queue=queue_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=queue_summary.due_revision_count,
            high_risk_concept_count=queue_summary.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_study_plan_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._study_plan_port.get_study_plan_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        study_plan_section = build_study_plan_payload_section(
            generated_at=summary.generated_at,
            daily_item_count=summary.daily_item_count,
            weekly_item_count=summary.weekly_item_count,
            total_estimated_gain=summary.total_estimated_gain,
        )
        behavior = await self._behavior_port.get_behavior_summary(
            tenant_id,
            student_id,
            exam_id,
        )
        study_behavior_section = build_study_behavior_payload_section(
            completion_rate=behavior.completion_rate,
            skip_rate=behavior.skip_rate,
            average_minutes_variance=behavior.average_minutes_variance,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            study_plan=study_plan_section,
            study_behavior=study_behavior_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_forecast_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._forecast_port.get_forecast_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        goal_section = build_goal_payload_section(
            target_readiness_score=summary.target_readiness_score,
            target_date=summary.target_date,
        )
        forecast_section = build_forecast_payload_section(
            current_readiness=summary.current_readiness,
            projected_readiness=summary.projected_readiness,
            gap_to_goal=summary.gap_to_goal,
            on_track=summary.on_track,
            days_remaining=summary.days_remaining,
            explanation=summary.explanation,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            goal=goal_section,
            forecast=forecast_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_predicted_score_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._predicted_score_port.get_predicted_score_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        predicted_outcome = build_predicted_outcome_payload_section(
            expected_score=summary.expected_score,
            low_score=summary.low_score,
            high_score=summary.high_score,
            risk_level=summary.risk_level,
            explanation=summary.explanation,
        )
        simulations = build_simulations_payload_section(
            current_state=summary.current_state,
            complete_recommendations=summary.complete_recommendations,
            no_study=summary.no_study,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            predicted_outcome=predicted_outcome,
            simulations=simulations,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_milestones_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._milestone_port.get_milestone_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        trajectory = build_trajectory_payload_section(
            required_gain=summary.required_gain,
            expected_daily_progress=summary.expected_daily_progress,
            expected_weekly_progress=summary.expected_weekly_progress,
        )
        milestones = build_milestones_payload_section(summary.milestones)
        milestone_status = build_milestone_status_payload_section(
            status=summary.milestone_status,
            current_gap=summary.current_gap,
            explanation=summary.explanation,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            trajectory=trajectory,
            milestones=milestones,
            milestone_status=milestone_status,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_forecast_probability_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._forecast_probability_port.get_forecast_probability_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        forecast_probability = build_forecast_probability_payload_section(
            goal_probability=summary.goal_probability,
            goal_likelihood=summary.goal_likelihood,
            explanation=summary.explanation,
        )
        forecast_scenarios = build_forecast_scenarios_payload_section(
            best_case=summary.best_case,
            expected=summary.expected,
            worst_case=summary.worst_case,
        )
        score_distribution = build_score_distribution_payload_section(
            optimistic_score=summary.optimistic_score,
            expected_score=summary.expected_score,
            pessimistic_score=summary.pessimistic_score,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            forecast_probability=forecast_probability,
            forecast_scenarios=forecast_scenarios,
            score_distribution=score_distribution,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_decision_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._decision_port.get_decision_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        decision_section = build_decision_payload_section(
            decision_type=summary.decision_type,
            decision_score=summary.decision_score,
            expected_readiness_gain=summary.expected_readiness_gain,
            expected_score_gain=summary.expected_score_gain,
            explanation=summary.explanation,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            decision=decision_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=summary.decision_type,
            decision_score=summary.decision_score,
            expected_readiness_gain=summary.expected_readiness_gain,
            expected_score_gain=summary.expected_score_gain,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_intervention_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._intervention_port.get_intervention_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        intervention_section = build_intervention_payload_section(
            intervention_type=summary.intervention_type,
            intervention_score=summary.intervention_score,
            urgency=summary.urgency,
            expected_readiness_gain=summary.expected_readiness_gain,
            title=summary.title,
            description=summary.description,
        )
        baseline_section = None
        if existing.intervention_type != summary.intervention_type:
            readiness, predicted, completion = extract_baseline_metrics(
                existing.twin_payload,
                readiness_score=existing.readiness_score,
            )
            baseline_section = build_intervention_baseline_payload_section(
                intervention_type=summary.intervention_type,
                readiness_score=readiness,
                predicted_score=predicted,
                completion_rate=completion,
            )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            intervention=intervention_section,
            intervention_baseline=baseline_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=summary.intervention_type,
            intervention_score=summary.intervention_score,
            intervention_urgency=summary.urgency,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_intervention_outcome_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._intervention_outcome_port.get_intervention_outcome_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        effectiveness_section = build_intervention_effectiveness_payload_section(
            last_effectiveness_score=summary.last_effectiveness_score,
            outcome_status=summary.outcome_status,
            explanation=summary.explanation,
        )
        optimization_section = build_optimization_payload_section(
            best_intervention=summary.best_intervention,
            historical_effectiveness=summary.historical_effectiveness,
            optimized_intervention_score=summary.optimized_intervention_score,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            intervention_effectiveness=effectiveness_section,
            optimization=optimization_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_behavior_profile_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin:
        summary = await self._behavior_profile_port.get_behavior_profile_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        behavior_profile_section = build_behavior_profile_payload_section(
            consistency_score=summary.consistency_score,
            discipline_score=summary.discipline_score,
            revision_adherence_score=summary.revision_adherence_score,
            weakness_recovery_score=summary.weakness_recovery_score,
            engagement_score=summary.engagement_score,
            learning_style=summary.learning_style,
            risk_profile=summary.risk_profile,
            explanation=summary.explanation,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            behavior_profile=behavior_profile_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=summary.learning_style,
            risk_profile=summary.risk_profile,
            consistency_score=summary.consistency_score,
            discipline_score=summary.discipline_score,
            engagement_score=summary.engagement_score,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_personalization_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin:
        summary = await self._personalization_port.get_personalization_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        personalization_section = build_personalization_payload_section(
            summary=PersonalizationSummary(
                learning_style=LearningStyle(summary.learning_style),
                risk_profile=RiskProfile(summary.risk_profile),
                top_multiplier=summary.top_multiplier,
                best_activity_type=ActivityType(summary.best_activity_type),
                historical_effectiveness=summary.historical_effectiveness,
            ),
            explanation=summary.explanation,
        )
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            personalization=personalization_section,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=existing.learning_style,
            risk_profile=existing.risk_profile,
            consistency_score=existing.consistency_score,
            discipline_score=existing.discipline_score,
            engagement_score=existing.engagement_score,
            best_activity_type=summary.best_activity_type,
            top_multiplier=summary.top_multiplier,
            historical_effectiveness=summary.historical_effectiveness,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_mentor_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._mentor_port.get_mentor_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            mentor=summary.mentor_payload,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=existing.learning_style,
            risk_profile=existing.risk_profile,
            consistency_score=existing.consistency_score,
            discipline_score=existing.discipline_score,
            engagement_score=existing.engagement_score,
            best_activity_type=existing.best_activity_type,
            top_multiplier=existing.top_multiplier,
            historical_effectiveness=existing.historical_effectiveness,
            mentor_status=summary.mentor_status,
            top_mentor_message=summary.top_mentor_message,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_mentor_action_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._mentor_action_port.get_mentor_action_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        mentor_payload = existing.twin_payload.get("mentor")
        merged_mentor = dict(mentor_payload) if isinstance(mentor_payload, dict) else {}
        merged_mentor.update(summary.mentor_payload_patch)
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            mentor=merged_mentor,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=existing.learning_style,
            risk_profile=existing.risk_profile,
            consistency_score=existing.consistency_score,
            discipline_score=existing.discipline_score,
            engagement_score=existing.engagement_score,
            best_activity_type=existing.best_activity_type,
            top_multiplier=existing.top_multiplier,
            historical_effectiveness=existing.historical_effectiveness,
            mentor_status=existing.mentor_status,
            top_mentor_message=existing.top_mentor_message,
            mentor_action_type=summary.mentor_action_type,
            mentor_action_priority=summary.mentor_action_priority,
            escalation_level=summary.escalation_level,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_mentor_case_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._mentor_case_port.get_mentor_case_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        mentor_payload = existing.twin_payload.get("mentor")
        merged_mentor = dict(mentor_payload) if isinstance(mentor_payload, dict) else {}
        if summary.mentor_payload_patch:
            merged_mentor.update(summary.mentor_payload_patch)
        elif "mentor_case" in merged_mentor:
            merged_mentor.pop("mentor_case", None)
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            mentor=merged_mentor,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=existing.learning_style,
            risk_profile=existing.risk_profile,
            consistency_score=existing.consistency_score,
            discipline_score=existing.discipline_score,
            engagement_score=existing.engagement_score,
            best_activity_type=existing.best_activity_type,
            top_multiplier=existing.top_multiplier,
            historical_effectiveness=existing.historical_effectiveness,
            mentor_status=existing.mentor_status,
            top_mentor_message=existing.top_mentor_message,
            mentor_action_type=existing.mentor_action_type,
            mentor_action_priority=existing.mentor_action_priority,
            escalation_level=existing.escalation_level,
            active_case_status=summary.active_case_status,
            active_case_priority=summary.active_case_priority,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _update_mentor_effectiveness_section(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime,
    ) -> PreparationTwin | None:
        summary = await self._mentor_effectiveness_port.get_mentor_effectiveness_summary(
            tenant_id,
            student_id,
            exam_id,
            current_time=current_time,
        )
        if summary is None:
            return None

        existing = await self._load_existing_shell(tenant_id, student_id, exam_id, current_time)
        mentor_payload = existing.twin_payload.get("mentor")
        merged_mentor = dict(mentor_payload) if isinstance(mentor_payload, dict) else {}
        if summary.mentor_payload_patch:
            merged_mentor.update(summary.mentor_payload_patch)
        elif "mentor_effectiveness" in merged_mentor:
            merged_mentor.pop("mentor_effectiveness", None)
        twin_payload = merge_twin_payload_sections(
            existing.twin_payload,
            mentor=merged_mentor,
        )
        updated = PreparationTwin(
            id=existing.id,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            profile_version=TWIN_PROFILE_V1,
            readiness_score=existing.readiness_score,
            average_mastery=existing.average_mastery,
            average_retention=existing.average_retention,
            average_confidence=existing.average_confidence,
            rated_node_count=existing.rated_node_count,
            due_revision_count=existing.due_revision_count,
            high_risk_concept_count=existing.high_risk_concept_count,
            largest_positive_driver=existing.largest_positive_driver,
            largest_negative_driver=existing.largest_negative_driver,
            recommendation_count=existing.recommendation_count,
            last_recommendation_at=existing.last_recommendation_at,
            twin_payload=twin_payload,
            generated_at=current_time,
            decision_type=existing.decision_type,
            decision_score=existing.decision_score,
            expected_readiness_gain=existing.expected_readiness_gain,
            expected_score_gain=existing.expected_score_gain,
            intervention_type=existing.intervention_type,
            intervention_score=existing.intervention_score,
            intervention_urgency=existing.intervention_urgency,
            learning_style=existing.learning_style,
            risk_profile=existing.risk_profile,
            consistency_score=existing.consistency_score,
            discipline_score=existing.discipline_score,
            engagement_score=existing.engagement_score,
            best_activity_type=existing.best_activity_type,
            top_multiplier=existing.top_multiplier,
            historical_effectiveness=existing.historical_effectiveness,
            mentor_status=existing.mentor_status,
            top_mentor_message=existing.top_mentor_message,
            mentor_action_type=existing.mentor_action_type,
            mentor_action_priority=existing.mentor_action_priority,
            escalation_level=existing.escalation_level,
            active_case_status=existing.active_case_status,
            active_case_priority=existing.active_case_priority,
        )
        persisted = await self._projection_repo.persist_partial_projection(updated)
        await self._emit_events(
            persisted,
            correlation_id=correlation_id,
            causation_id=causation_id,
            occurred_at=current_time,
        )
        return persisted

    async def _emit_events(
        self,
        persisted: PreparationTwin,
        *,
        correlation_id: str,
        causation_id: str | None,
        occurred_at: datetime,
    ) -> None:
        await self._outbox.enqueue_twin_updated(
            TwinUpdated(
                tenant_id=persisted.tenant_id,
                student_id=persisted.student_id,
                exam_id=persisted.exam_id,
                profile_version=persisted.profile_version,
                generated_at=persisted.generated_at,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=occurred_at,
            )
        )
        await self._outbox.enqueue_twin_snapshot_updated(
            TwinSnapshotUpdated(
                tenant_id=persisted.tenant_id,
                student_id=persisted.student_id,
                exam_id=persisted.exam_id,
                readiness_score=persisted.readiness_score,
                due_revision_count=persisted.due_revision_count,
                high_risk_concept_count=persisted.high_risk_concept_count,
                correlation_id=correlation_id,
                causation_id=causation_id,
                occurred_at=occurred_at,
            )
        )

    async def build_and_persist(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str,
        correlation_id: str,
        causation_id: str | None,
        current_time: datetime | None = None,
    ) -> PreparationTwin:
        """Full rebuild retained for backward compatibility and tests."""
        now = current_time or datetime.now(UTC)
        await self.apply_incremental_update(
            section=TwinProjectionSection.READINESS,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            current_time=now,
        )
        await self.apply_incremental_update(
            section=TwinProjectionSection.RECOMMENDATIONS,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            current_time=now,
        )
        result = await self.apply_incremental_update(
            section=TwinProjectionSection.QUEUE,
            tenant_id=tenant_id,
            student_id=student_id,
            exam_id=exam_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            current_time=now,
        )
        assert result is not None
        return result
