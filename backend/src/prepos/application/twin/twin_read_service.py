from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from prepos.application.twin.projection_ports import TwinProjectionRepositoryPort
from prepos.application.twin.twin_dto import (
    TwinDashboardResponse,
    TwinGoalSummaryResponse,
    TwinMentorCaseSummaryResponse,
    TwinMentorEffectivenessSummaryResponse,
    TwinProjectionMetricsResponse,
    TwinResponse,
)
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.snapshot_entities import PreparationTwin


def _driver_lists(twin_payload: dict[str, object]) -> tuple[list[str], list[str]]:
    drivers = twin_payload.get("drivers")
    if not isinstance(drivers, dict):
        return [], []
    top_positive = drivers.get("top_positive_drivers")
    top_negative = drivers.get("top_negative_drivers")
    positive = [str(item) for item in top_positive] if isinstance(top_positive, list) else []
    negative = [str(item) for item in top_negative] if isinstance(top_negative, list) else []
    return positive, negative


def _study_behavior_metrics(twin_payload: dict[str, object]) -> tuple[Decimal | None, Decimal | None]:
    study_behavior = twin_payload.get("study_behavior")
    if not isinstance(study_behavior, dict):
        return None, None
    completion = study_behavior.get("completion_rate")
    skip = study_behavior.get("skip_rate")
    completion_rate = Decimal(str(completion)) if completion is not None else None
    skip_rate = Decimal(str(skip)) if skip is not None else None
    return completion_rate, skip_rate


def _forecast_metrics(
    twin_payload: dict[str, object],
) -> tuple[Decimal | None, Decimal | None, bool | None]:
    forecast = twin_payload.get("forecast")
    if not isinstance(forecast, dict):
        return None, None, None
    projected = forecast.get("projected_readiness")
    gap = forecast.get("gap_to_goal")
    on_track = forecast.get("on_track")
    projected_readiness = Decimal(str(projected)) if projected is not None else None
    gap_to_goal = Decimal(str(gap)) if gap is not None else None
    on_track_value = bool(on_track) if on_track is not None else None
    return projected_readiness, gap_to_goal, on_track_value


def _predicted_outcome_metrics(
    twin_payload: dict[str, object],
) -> tuple[Decimal | None, Decimal | None, Decimal | None, str | None]:
    predicted_outcome = twin_payload.get("predicted_outcome")
    if not isinstance(predicted_outcome, dict):
        return None, None, None, None
    expected = predicted_outcome.get("expected_score")
    low = predicted_outcome.get("low_score")
    high = predicted_outcome.get("high_score")
    risk = predicted_outcome.get("risk_level")
    expected_score = Decimal(str(expected)) if expected is not None else None
    low_score = Decimal(str(low)) if low is not None else None
    high_score = Decimal(str(high)) if high is not None else None
    risk_level = str(risk) if risk is not None else None
    return expected_score, low_score, high_score, risk_level


def _predicted_payload_sections(
    twin_payload: dict[str, object],
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    predicted_outcome = twin_payload.get("predicted_outcome")
    simulations = twin_payload.get("simulations")
    outcome = dict(predicted_outcome) if isinstance(predicted_outcome, dict) else None
    sims = dict(simulations) if isinstance(simulations, dict) else None
    return outcome, sims


def _milestone_metrics(
    twin_payload: dict[str, object],
) -> tuple[str | None, Decimal | None, date | None, Decimal | None]:
    milestone_status_section = twin_payload.get("milestone_status")
    trajectory = twin_payload.get("trajectory")
    milestones = twin_payload.get("milestones")

    status: str | None = None
    if isinstance(milestone_status_section, dict):
        raw_status = milestone_status_section.get("status")
        status = str(raw_status) if raw_status is not None else None

    expected_weekly_progress: Decimal | None = None
    if isinstance(trajectory, dict):
        weekly = trajectory.get("expected_weekly_progress")
        expected_weekly_progress = Decimal(str(weekly)) if weekly is not None else None

    next_milestone_date: date | None = None
    next_milestone_target: Decimal | None = None
    if isinstance(milestones, list):
        today = date.today()
        for item in milestones:
            if not isinstance(item, dict):
                continue
            raw_date = item.get("target_date")
            if raw_date is None:
                continue
            milestone_date = date.fromisoformat(str(raw_date))
            if milestone_date >= today:
                next_milestone_date = milestone_date
                target = item.get("target_readiness")
                next_milestone_target = Decimal(str(target)) if target is not None else None
                break

    return status, expected_weekly_progress, next_milestone_date, next_milestone_target


def _forecast_probability_metrics(
    twin_payload: dict[str, object],
) -> tuple[Decimal | None, str | None, Decimal | None, Decimal | None]:
    forecast_probability = twin_payload.get("forecast_probability")
    forecast_scenarios = twin_payload.get("forecast_scenarios")

    goal_probability: Decimal | None = None
    goal_likelihood: str | None = None
    if isinstance(forecast_probability, dict):
        probability = forecast_probability.get("goal_probability")
        likelihood = forecast_probability.get("goal_likelihood")
        goal_probability = Decimal(str(probability)) if probability is not None else None
        goal_likelihood = str(likelihood) if likelihood is not None else None

    best_case: Decimal | None = None
    worst_case: Decimal | None = None
    if isinstance(forecast_scenarios, dict):
        best = forecast_scenarios.get("best_case")
        worst = forecast_scenarios.get("worst_case")
        best_case = Decimal(str(best)) if best is not None else None
        worst_case = Decimal(str(worst)) if worst is not None else None

    return goal_probability, goal_likelihood, best_case, worst_case


def _decision_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, Decimal | None, Decimal | None, dict[str, object] | None]:
    if twin.decision_type is not None:
        decision_payload = twin_payload.get("decision")
        decision = dict(decision_payload) if isinstance(decision_payload, dict) else None
        return (
            twin.decision_type,
            twin.expected_readiness_gain,
            twin.expected_score_gain,
            decision,
        )

    decision_payload = twin_payload.get("decision")
    if not isinstance(decision_payload, dict):
        return None, None, None, None
    decision_type = decision_payload.get("decision_type")
    readiness_gain = decision_payload.get("expected_readiness_gain")
    score_gain = decision_payload.get("expected_score_gain")
    return (
        str(decision_type) if decision_type is not None else None,
        Decimal(str(readiness_gain)) if readiness_gain is not None else None,
        Decimal(str(score_gain)) if score_gain is not None else None,
        dict(decision_payload),
    )


def _intervention_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, str | None, Decimal | None, dict[str, object] | None]:
    if twin.intervention_type is not None:
        intervention_payload = twin_payload.get("intervention")
        intervention = dict(intervention_payload) if isinstance(intervention_payload, dict) else None
        return (
            twin.intervention_type,
            twin.intervention_urgency,
            twin.intervention_score,
            intervention,
        )

    intervention_payload = twin_payload.get("intervention")
    if not isinstance(intervention_payload, dict):
        return None, None, None, None
    intervention_type = intervention_payload.get("intervention_type")
    urgency = intervention_payload.get("urgency")
    score = intervention_payload.get("intervention_score")
    return (
        str(intervention_type) if intervention_type is not None else None,
        str(urgency) if urgency is not None else None,
        Decimal(str(score)) if score is not None else None,
        dict(intervention_payload),
    )


def _intervention_outcome_metrics(
    twin_payload: dict[str, object],
) -> tuple[Decimal | None, str | None, str | None, Decimal | None, dict[str, object] | None, dict[str, object] | None]:
    effectiveness = twin_payload.get("intervention_effectiveness")
    optimization = twin_payload.get("optimization")

    last_effectiveness_score: Decimal | None = None
    outcome_status: str | None = None
    if isinstance(effectiveness, dict):
        score = effectiveness.get("last_effectiveness_score")
        status = effectiveness.get("outcome_status")
        last_effectiveness_score = Decimal(str(score)) if score is not None else None
        outcome_status = str(status) if status is not None else None

    best_intervention: str | None = None
    historical_effectiveness: Decimal | None = None
    if isinstance(optimization, dict):
        best = optimization.get("best_intervention")
        historical = optimization.get("historical_effectiveness")
        best_intervention = str(best) if best is not None else None
        historical_effectiveness = Decimal(str(historical)) if historical is not None else None

    effectiveness_payload = dict(effectiveness) if isinstance(effectiveness, dict) else None
    optimization_payload = dict(optimization) if isinstance(optimization, dict) else None
    return (
        last_effectiveness_score,
        outcome_status,
        best_intervention,
        historical_effectiveness,
        effectiveness_payload,
        optimization_payload,
    )


def _behavior_profile_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, str | None, Decimal | None, dict[str, object] | None]:
    if twin.learning_style is not None:
        profile_payload = twin_payload.get("behavior_profile")
        profile = dict(profile_payload) if isinstance(profile_payload, dict) else None
        return (
            twin.learning_style,
            twin.risk_profile,
            twin.consistency_score,
            profile,
        )

    profile_payload = twin_payload.get("behavior_profile")
    if not isinstance(profile_payload, dict):
        return None, None, None, None
    learning_style = profile_payload.get("learning_style")
    risk_profile = profile_payload.get("risk_profile")
    consistency = profile_payload.get("consistency_score")
    return (
        str(learning_style) if learning_style is not None else None,
        str(risk_profile) if risk_profile is not None else None,
        Decimal(str(consistency)) if consistency is not None else None,
        dict(profile_payload),
    )


def _personalization_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, Decimal | None, dict[str, object] | None]:
    if twin.best_activity_type is not None:
        personalization_payload = twin_payload.get("personalization")
        payload = dict(personalization_payload) if isinstance(personalization_payload, dict) else None
        return twin.best_activity_type, twin.top_multiplier, payload

    personalization_payload = twin_payload.get("personalization")
    if not isinstance(personalization_payload, dict):
        return None, None, None
    best_activity = personalization_payload.get("best_activity_type")
    top_multiplier = personalization_payload.get("top_multiplier")
    return (
        str(best_activity) if best_activity is not None else None,
        Decimal(str(top_multiplier)) if top_multiplier is not None else None,
        dict(personalization_payload),
    )


def _mentor_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, str | None, dict[str, object] | None]:
    if twin.mentor_status is not None:
        mentor_payload = twin_payload.get("mentor")
        payload = dict(mentor_payload) if isinstance(mentor_payload, dict) else None
        return twin.mentor_status, twin.top_mentor_message, payload

    mentor_payload = twin_payload.get("mentor")
    if not isinstance(mentor_payload, dict):
        return None, None, None
    summary = mentor_payload.get("summary")
    if isinstance(summary, dict):
        status = summary.get("overall_status")
        message = summary.get("key_message")
        return (
            str(status) if status is not None else None,
            str(message) if message is not None else None,
            dict(mentor_payload),
        )
    return None, None, dict(mentor_payload)


def _mentor_action_dashboard_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[str | None, Decimal | None, str | None]:
    if twin.mentor_action_type is not None:
        return twin.mentor_action_type, twin.mentor_action_priority, twin.escalation_level

    mentor_payload = twin_payload.get("mentor")
    if not isinstance(mentor_payload, dict):
        return None, None, None
    action = mentor_payload.get("mentor_action")
    escalation = mentor_payload.get("escalation")
    action_type = None
    priority_score = None
    if isinstance(action, dict):
        raw_type = action.get("action_type")
        raw_score = action.get("priority_score")
        action_type = str(raw_type) if raw_type is not None else None
        priority_score = Decimal(str(raw_score)) if raw_score is not None else None
    escalation_level = None
    if isinstance(escalation, dict):
        raw_level = escalation.get("level")
        escalation_level = str(raw_level) if raw_level is not None else None
    return action_type, priority_score, escalation_level


def _mentor_action_payload_metrics(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> tuple[dict[str, object] | None, dict[str, object] | None]:
    mentor_payload = twin_payload.get("mentor")
    if isinstance(mentor_payload, dict):
        action = mentor_payload.get("mentor_action")
        escalation = mentor_payload.get("escalation")
        action_payload = dict(action) if isinstance(action, dict) else None
        escalation_payload = dict(escalation) if isinstance(escalation, dict) else None
        if action_payload is not None or escalation_payload is not None:
            return action_payload, escalation_payload
    return None, None


def _study_plan_summary(twin_payload: dict[str, object]) -> tuple[int, int, Decimal | None]:
    study_plan = twin_payload.get("study_plan")
    if not isinstance(study_plan, dict):
        return 0, 0, None
    daily_items = study_plan.get("daily_items")
    weekly_items = study_plan.get("weekly_items")
    gain = study_plan.get("total_estimated_gain")
    daily_count = int(daily_items) if daily_items is not None else 0
    weekly_count = int(weekly_items) if weekly_items is not None else 0
    plan_gain = Decimal(str(gain)) if gain is not None else None
    return daily_count, weekly_count, plan_gain


def _total_estimated_gain(twin_payload: dict[str, object]) -> Decimal | None:
    _, _, study_plan_gain = _study_plan_summary(twin_payload)
    if study_plan_gain is not None:
        return study_plan_gain
    recommendations = twin_payload.get("recommendations")
    if not isinstance(recommendations, dict):
        return None
    gain = recommendations.get("total_estimated_gain")
    if gain is None:
        return None
    return Decimal(str(gain))


def _goal_summary(twin_payload: dict[str, object]) -> TwinGoalSummaryResponse | None:
    goal = twin_payload.get("goal")
    if not isinstance(goal, dict):
        return None
    target = goal.get("target_readiness_score")
    target_date_raw = goal.get("target_date")
    if target is None and target_date_raw is None:
        return None
    target_date = date.fromisoformat(str(target_date_raw)) if target_date_raw is not None else None
    return TwinGoalSummaryResponse(
        target_readiness_score=Decimal(str(target)) if target is not None else None,
        target_date=target_date,
    )


def _mentor_case_summary(
    twin: PreparationTwin,
    twin_payload: dict[str, object],
) -> TwinMentorCaseSummaryResponse | None:
    mentor_payload = twin_payload.get("mentor")
    mentor_case = mentor_payload.get("mentor_case") if isinstance(mentor_payload, dict) else None
    if isinstance(mentor_case, dict):
        status = mentor_case.get("case_status")
        priority = mentor_case.get("priority")
        opened_at_raw = mentor_case.get("opened_at")
        opened_at = datetime.fromisoformat(str(opened_at_raw)) if opened_at_raw else None
        return TwinMentorCaseSummaryResponse(
            case_status=str(status) if status is not None else None,
            priority=str(priority) if priority is not None else None,
            opened_at=opened_at,
        )
    if twin.active_case_status is not None or twin.active_case_priority is not None:
        return TwinMentorCaseSummaryResponse(
            case_status=twin.active_case_status,
            priority=twin.active_case_priority,
            opened_at=None,
        )
    return None


def _mentor_effectiveness_summary(
    twin_payload: dict[str, object],
) -> TwinMentorEffectivenessSummaryResponse | None:
    mentor_payload = twin_payload.get("mentor")
    if not isinstance(mentor_payload, dict):
        return None
    effectiveness = mentor_payload.get("mentor_effectiveness")
    if not isinstance(effectiveness, dict):
        return None
    best_action = effectiveness.get("best_action")
    score = effectiveness.get("effectiveness_score")
    sample_size = effectiveness.get("sample_size")
    if best_action is None and score is None and sample_size is None:
        return None
    return TwinMentorEffectivenessSummaryResponse(
        best_action=str(best_action) if best_action is not None else None,
        effectiveness_score=Decimal(str(score)) if score is not None else None,
        sample_size=int(sample_size) if sample_size is not None else None,
    )


class TwinReadService:
    def __init__(self, *, projection_repo: TwinProjectionRepositoryPort) -> None:
        self._projection_repo = projection_repo

    async def get_twin(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
    ) -> TwinResponse:
        if exam_id is not None:
            twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        else:
            twin = await self._projection_repo.get_projection_for_student(tenant_id, student_id)

        if twin is None:
            return TwinResponse(profile_version=TWIN_PROFILE_V1)

        total_gain = _total_estimated_gain(twin.twin_payload)
        predicted_outcome, simulations = _predicted_payload_sections(twin.twin_payload)
        _, _, _, decision = _decision_metrics(twin, twin.twin_payload)
        _, _, _, intervention = _intervention_metrics(twin, twin.twin_payload)
        _, _, _, _, effectiveness, optimization = _intervention_outcome_metrics(twin.twin_payload)
        _, _, _, behavior_profile = _behavior_profile_metrics(twin, twin.twin_payload)
        _, _, personalization = _personalization_metrics(twin, twin.twin_payload)
        _, _, mentor = _mentor_metrics(twin, twin.twin_payload)
        mentor_action, escalation = _mentor_action_payload_metrics(twin, twin.twin_payload)
        return TwinResponse(
            profile_version=twin.profile_version,
            projection_version=twin.projection_revision,
            readiness_score=twin.readiness_score,
            average_mastery=twin.average_mastery,
            average_retention=twin.average_retention,
            average_confidence=twin.average_confidence,
            rated_node_count=twin.rated_node_count,
            due_revision_count=twin.due_revision_count,
            high_risk_concept_count=twin.high_risk_concept_count,
            largest_positive_driver=twin.largest_positive_driver,
            largest_negative_driver=twin.largest_negative_driver,
            recommendation_count=twin.recommendation_count,
            last_recommendation_at=twin.last_recommendation_at,
            total_estimated_gain=total_gain,
            predicted_outcome=predicted_outcome,
            simulations=simulations,
            decision=decision,
            intervention=intervention,
            intervention_effectiveness=effectiveness,
            optimization=optimization,
            behavior_profile=behavior_profile,
            personalization=personalization,
            mentor=mentor,
            mentor_action=mentor_action,
            escalation=escalation,
            twin_payload=twin.twin_payload,
            generated_at=twin.generated_at,
        )

    async def get_dashboard(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
    ) -> TwinDashboardResponse:
        if exam_id is not None:
            twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        else:
            twin = await self._projection_repo.get_projection_for_student(tenant_id, student_id)

        if twin is None:
            return TwinDashboardResponse()

        top_positive, top_negative = _driver_lists(twin.twin_payload)
        today_plan_count, weekly_plan_count, plan_gain = _study_plan_summary(twin.twin_payload)
        completion_rate, skip_rate = _study_behavior_metrics(twin.twin_payload)
        projected_readiness, gap_to_goal, on_track = _forecast_metrics(twin.twin_payload)
        expected_score, low_score, high_score, risk_level = _predicted_outcome_metrics(twin.twin_payload)
        milestone_status, expected_weekly_progress, next_milestone_date, next_milestone_target = (
            _milestone_metrics(twin.twin_payload)
        )
        goal_probability, goal_likelihood, best_case_readiness, worst_case_readiness = (
            _forecast_probability_metrics(twin.twin_payload)
        )
        current_decision, expected_readiness_gain, expected_score_gain, _ = _decision_metrics(
            twin,
            twin.twin_payload,
        )
        current_intervention, intervention_urgency, intervention_score, _ = _intervention_metrics(
            twin,
            twin.twin_payload,
        )
        last_effectiveness_score, _, best_intervention, historical_effectiveness, _, _ = (
            _intervention_outcome_metrics(twin.twin_payload)
        )
        learning_style, risk_profile, consistency_score, _ = _behavior_profile_metrics(
            twin,
            twin.twin_payload,
        )
        best_activity_type, top_multiplier, _ = _personalization_metrics(twin, twin.twin_payload)
        mentor_status, top_mentor_message, _ = _mentor_metrics(twin, twin.twin_payload)
        mentor_action, mentor_action_priority, escalation_level = _mentor_action_dashboard_metrics(
            twin,
            twin.twin_payload,
        )
        goal_summary = _goal_summary(twin.twin_payload)
        mentor_case = _mentor_case_summary(twin, twin.twin_payload)
        mentor_effectiveness = _mentor_effectiveness_summary(twin.twin_payload)
        return TwinDashboardResponse(
            readiness_score=twin.readiness_score,
            due_revision_count=twin.due_revision_count,
            high_risk_concept_count=twin.high_risk_concept_count,
            recommendation_count=twin.recommendation_count,
            largest_positive_driver=twin.largest_positive_driver,
            largest_negative_driver=twin.largest_negative_driver,
            top_positive_drivers=top_positive,
            top_negative_drivers=top_negative,
            total_estimated_gain=plan_gain or _total_estimated_gain(twin.twin_payload),
            today_plan_count=today_plan_count,
            weekly_plan_count=weekly_plan_count,
            completion_rate=completion_rate,
            skip_rate=skip_rate,
            projected_readiness=projected_readiness,
            gap_to_goal=gap_to_goal,
            on_track=on_track,
            expected_score=expected_score,
            low_score=low_score,
            high_score=high_score,
            risk_level=risk_level,
            milestone_status=milestone_status,
            expected_weekly_progress=expected_weekly_progress,
            next_milestone_date=next_milestone_date,
            next_milestone_target=next_milestone_target,
            goal_probability=goal_probability,
            goal_likelihood=goal_likelihood,
            best_case_readiness=best_case_readiness,
            worst_case_readiness=worst_case_readiness,
            current_decision=current_decision,
            expected_readiness_gain=expected_readiness_gain,
            expected_score_gain=expected_score_gain,
            current_intervention=current_intervention,
            intervention_urgency=intervention_urgency,
            intervention_score=intervention_score,
            best_intervention=best_intervention,
            historical_effectiveness=historical_effectiveness,
            last_effectiveness_score=last_effectiveness_score,
            learning_style=learning_style,
            risk_profile=risk_profile,
            consistency_score=consistency_score,
            best_activity_type=best_activity_type,
            top_multiplier=top_multiplier,
            mentor_status=mentor_status,
            top_mentor_message=top_mentor_message,
            mentor_action=mentor_action,
            mentor_action_priority=mentor_action_priority,
            escalation_level=escalation_level,
            goal_summary=goal_summary,
            mentor_case=mentor_case,
            mentor_effectiveness=mentor_effectiveness,
            generated_at=twin.generated_at,
        )

    async def get_metrics(
        self,
        *,
        tenant_id: UUID,
        student_id: UUID,
        exam_id: str | None = None,
    ) -> TwinProjectionMetricsResponse:
        if exam_id is not None:
            twin = await self._projection_repo.get_projection(tenant_id, student_id, exam_id)
        else:
            twin = await self._projection_repo.get_projection_for_student(tenant_id, student_id)

        if twin is None:
            return TwinProjectionMetricsResponse()

        return TwinProjectionMetricsResponse(
            rebuild_count=twin.rebuild_count,
            skipped_rebuild_count=twin.skipped_rebuild_count,
            incremental_update_count=twin.incremental_update_count,
            lock_contention_count=twin.lock_contention_count,
        )
