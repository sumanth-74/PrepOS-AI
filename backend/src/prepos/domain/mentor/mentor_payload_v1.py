from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from prepos.domain.mentor.case_management_v1 import MentorCase
from prepos.domain.mentor.coaching_recommendations_v1 import CoachingRecommendation
from prepos.domain.mentor.escalation_v1 import EscalationSignal
from prepos.domain.mentor.mentor_actions_v1 import MentorAction
from prepos.domain.mentor.mentor_insights_v1 import MentorInsight
from prepos.domain.mentor.mentor_summary_v1 import MentorSummary
from prepos.domain.mentor.mentor_types_v1 import MENTOR_V1, MentorActionType

if TYPE_CHECKING:
    from prepos.domain.mentor.mentor_insights_v1 import MentorInsightInputs


def serialize_mentor_action(action: MentorAction) -> dict[str, object]:
    return {
        "action_type": action.action_type.value,
        "priority_score": float(action.priority_score),
        "urgency": action.urgency.value,
        "expected_impact": float(action.expected_impact),
        "explanation": action.explanation,
    }


def serialize_escalation(escalation: EscalationSignal) -> dict[str, object]:
    return {
        "level": escalation.level.value,
        "reason": escalation.reason,
    }


def serialize_mentor_case(active_case: MentorCase) -> dict[str, object]:
    return {
        "case_status": active_case.status.value,
        "opened_at": active_case.opened_at.isoformat(),
        "priority": active_case.priority.value,
    }


def serialize_mentor_effectiveness(
    *,
    best_action: MentorActionType,
    effectiveness_score: Decimal,
    sample_size: int,
) -> dict[str, object]:
    return {
        "best_action": best_action.value,
        "effectiveness_score": float(effectiveness_score),
        "sample_size": sample_size,
    }


def build_mentor_payload_section(
    *,
    summary: MentorSummary,
    insights: tuple[MentorInsight, ...],
    recommendations: tuple[CoachingRecommendation, ...],
    mentor_action: MentorAction | None = None,
    escalation: EscalationSignal | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "version": MENTOR_V1,
        "summary": {
            "overall_status": summary.overall_status.value,
            "key_message": summary.key_message,
            "strongest_signal": summary.strongest_signal,
            "weakest_signal": summary.weakest_signal,
        },
        "insights": [
            {
                "insight_type": insight.insight_type.value,
                "priority": insight.priority.value,
                "title": insight.title,
                "message": insight.message,
                "supporting_signals": list(insight.supporting_signals),
            }
            for insight in insights
        ],
        "recommendations": [
            {
                "action": recommendation.action.value,
                "rationale": recommendation.rationale,
                "expected_gain": float(recommendation.expected_gain),
            }
            for recommendation in recommendations
        ],
    }
    if mentor_action is not None:
        payload["mentor_action"] = serialize_mentor_action(mentor_action)
    if escalation is not None:
        payload["escalation"] = serialize_escalation(escalation)
    return payload


def extract_mentor_inputs_from_projection(
    *,
    readiness_score: Decimal | None,
    due_revision_count: int,
    high_risk_concept_count: int,
    largest_negative_driver: str | None,
    twin_payload: dict[str, object],
) -> MentorInsightInputs:
    from prepos.domain.mentor.mentor_insights_v1 import (
        BehaviorProfileSignals,
        ForecastSignals,
        InterventionEffectivenessSignals,
        MentorInsightInputs,
        MilestoneSignals,
        OptimizationSignals,
        PersonalizationSignals,
        ReadinessSignals,
        StudyPlanSignals,
    )

    readiness_section = twin_payload.get("readiness")
    coverage_subscore = None
    if isinstance(readiness_section, dict):
        coverage = readiness_section.get("coverage_subscore")
        if coverage is not None:
            coverage_subscore = Decimal(str(coverage))

    forecast_probability = twin_payload.get("forecast_probability")
    goal_probability = None
    if isinstance(forecast_probability, dict):
        probability = forecast_probability.get("goal_probability")
        if probability is not None:
            goal_probability = Decimal(str(probability))

    forecast = twin_payload.get("forecast")
    gap_to_goal = None
    on_track = None
    if isinstance(forecast, dict):
        gap = forecast.get("gap_to_goal")
        track = forecast.get("on_track")
        gap_to_goal = Decimal(str(gap)) if gap is not None else None
        on_track = bool(track) if track is not None else None

    milestone_status_section = twin_payload.get("milestone_status")
    milestone_status = None
    current_gap = None
    if isinstance(milestone_status_section, dict):
        status = milestone_status_section.get("status")
        gap = milestone_status_section.get("current_gap")
        milestone_status = str(status) if status is not None else None
        current_gap = Decimal(str(gap)) if gap is not None else None

    intervention_effectiveness = twin_payload.get("intervention_effectiveness")
    last_effectiveness_score = None
    outcome_status = None
    if isinstance(intervention_effectiveness, dict):
        score = intervention_effectiveness.get("last_effectiveness_score")
        status = intervention_effectiveness.get("outcome_status")
        last_effectiveness_score = Decimal(str(score)) if score is not None else None
        outcome_status = str(status) if status is not None else None

    behavior_profile = twin_payload.get("behavior_profile")
    consistency_score = None
    discipline_score = None
    risk_profile = None
    learning_style = None
    if isinstance(behavior_profile, dict):
        consistency = behavior_profile.get("consistency_score")
        discipline = behavior_profile.get("discipline_score")
        risk = behavior_profile.get("risk_profile")
        style = behavior_profile.get("learning_style")
        consistency_score = Decimal(str(consistency)) if consistency is not None else None
        discipline_score = Decimal(str(discipline)) if discipline is not None else None
        risk_profile = str(risk) if risk is not None else None
        learning_style = str(style) if style is not None else None

    personalization = twin_payload.get("personalization")
    best_activity_type = None
    top_multiplier = None
    personalization_effectiveness = None
    if isinstance(personalization, dict):
        activity = personalization.get("best_activity_type")
        multiplier = personalization.get("top_multiplier")
        effectiveness = personalization.get("historical_effectiveness")
        best_activity_type = str(activity) if activity is not None else None
        top_multiplier = Decimal(str(multiplier)) if multiplier is not None else None
        personalization_effectiveness = (
            Decimal(str(effectiveness)) if effectiveness is not None else None
        )

    study_plan = twin_payload.get("study_plan")
    total_estimated_gain = None
    daily_item_count = 0
    if isinstance(study_plan, dict):
        gain = study_plan.get("total_estimated_gain")
        daily_items = study_plan.get("daily_items")
        total_estimated_gain = Decimal(str(gain)) if gain is not None else None
        daily_item_count = int(daily_items) if daily_items is not None else 0

    study_behavior = twin_payload.get("study_behavior")
    completion_rate = None
    if isinstance(study_behavior, dict):
        completion = study_behavior.get("completion_rate")
        completion_rate = Decimal(str(completion)) if completion is not None else None

    optimization = twin_payload.get("optimization")
    best_intervention = None
    historical_effectiveness = None
    optimized_intervention_score = None
    if isinstance(optimization, dict):
        best = optimization.get("best_intervention")
        historical = optimization.get("historical_effectiveness")
        optimized = optimization.get("optimized_intervention_score")
        best_intervention = str(best) if best is not None else None
        historical_effectiveness = Decimal(str(historical)) if historical is not None else None
        optimized_intervention_score = Decimal(str(optimized)) if optimized is not None else None

    return MentorInsightInputs(
        readiness=ReadinessSignals(
            readiness_score=readiness_score,
            coverage_subscore=coverage_subscore,
            largest_negative_driver=largest_negative_driver,
        ),
        forecast=ForecastSignals(
            goal_probability=goal_probability,
            gap_to_goal=gap_to_goal,
            on_track=on_track,
        ),
        milestones=MilestoneSignals(
            milestone_status=milestone_status,
            current_gap=current_gap,
        ),
        intervention_effectiveness=InterventionEffectivenessSignals(
            last_effectiveness_score=last_effectiveness_score,
            historical_effectiveness=historical_effectiveness,
            outcome_status=outcome_status,
        ),
        behavior_profile=BehaviorProfileSignals(
            consistency_score=consistency_score,
            discipline_score=discipline_score,
            risk_profile=risk_profile,
            learning_style=learning_style,
        ),
        personalization=PersonalizationSignals(
            best_activity_type=best_activity_type,
            top_multiplier=top_multiplier,
            historical_effectiveness=personalization_effectiveness,
        ),
        study_plan=StudyPlanSignals(
            total_estimated_gain=total_estimated_gain,
            daily_item_count=daily_item_count,
            completion_rate=completion_rate,
        ),
        optimization=OptimizationSignals(
            best_intervention=best_intervention,
            historical_effectiveness=historical_effectiveness,
            optimized_intervention_score=optimized_intervention_score,
        ),
        due_revision_count=due_revision_count,
        high_risk_concept_count=high_risk_concept_count,
    )
