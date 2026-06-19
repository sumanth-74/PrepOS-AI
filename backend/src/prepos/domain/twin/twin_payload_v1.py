from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1
from prepos.domain.scoring.readiness_impact_v1 import compute_total_estimated_gain
from prepos.domain.scoring.readiness_v1_1 import READINESS_V1_1, ReadinessResultV1_1
from prepos.domain.twin.entities import PersistedTwinRecommendation
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1


@dataclass(frozen=True, slots=True)
class TwinReadinessPayloadInputs:
    result: ReadinessResultV1_1
    drivers: ReadinessDriversV1 | None


@dataclass(frozen=True, slots=True)
class TwinRevisionQueuePayloadInputs:
    due_revision_count: int
    high_risk_concept_count: int


@dataclass(frozen=True, slots=True)
class TwinRecommendationsPayloadInputs:
    recommendation_count: int
    last_recommendation_at: datetime | None
    top_recommendations: tuple[PersistedTwinRecommendation, ...]


def _decimal(value: Decimal | None) -> float | None:
    if value is None:
        return None
    return float(value)


def _iso(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def build_twin_payload_v1(
    *,
    readiness: TwinReadinessPayloadInputs,
    revision_queue: TwinRevisionQueuePayloadInputs,
    recommendations: TwinRecommendationsPayloadInputs,
    drivers: ReadinessDriversV1 | None,
) -> dict[str, object]:
    """Deterministic Twin profile payload; no LLM or free-text generation."""
    top_items: list[dict[str, object]] = []
    for item in recommendations.top_recommendations:
        top_items.append(
            {
                "concept_id": item.concept_id,
                "recommendation_type": item.recommendation_type,
                "recommendation_score": float(item.recommendation_score),
                "readiness_gain": float(item.readiness_gain),
            }
        )

    total_estimated_gain = compute_total_estimated_gain(
        tuple(item.readiness_gain for item in recommendations.top_recommendations),
    )

    payload: dict[str, object] = {
        "profile_version": TWIN_PROFILE_V1,
        "readiness": {
            "version": READINESS_V1_1,
            "overall_score": _decimal(readiness.result.overall_score),
            "knowledge_subscore": _decimal(readiness.result.knowledge_subscore),
            "retention_subscore": _decimal(readiness.result.retention_subscore),
            "confidence_subscore": _decimal(readiness.result.confidence_subscore),
            "coverage_subscore": _decimal(readiness.result.coverage_subscore),
            "rated_node_count": readiness.result.rated_node_count,
            "total_node_count": readiness.result.total_node_count,
            "unrated": readiness.result.unrated,
            "readiness_score": _decimal(readiness.result.overall_score),
        },
        "revision_queue": {
            "due_revision_count": revision_queue.due_revision_count,
            "high_risk_concept_count": revision_queue.high_risk_concept_count,
        },
        "recommendations": {
            "recommendation_count": recommendations.recommendation_count,
            "last_recommendation_at": _iso(recommendations.last_recommendation_at),
            "total_estimated_gain": float(total_estimated_gain),
            "top": top_items,
        },
        "drivers": {
            "version": drivers.version if drivers is not None else None,
            "largest_positive_driver": drivers.largest_positive_driver if drivers else None,
            "largest_negative_driver": drivers.largest_negative_driver if drivers else None,
            "top_positive_drivers": list(drivers.top_positive_drivers) if drivers else [],
            "top_negative_drivers": list(drivers.top_negative_drivers) if drivers else [],
        },
    }
    return payload


def build_readiness_payload_section(
    *,
    readiness: TwinReadinessPayloadInputs,
    drivers: ReadinessDriversV1 | None,
) -> tuple[dict[str, object], dict[str, object]]:
    full = build_twin_payload_v1(
        readiness=readiness,
        revision_queue=TwinRevisionQueuePayloadInputs(due_revision_count=0, high_risk_concept_count=0),
        recommendations=TwinRecommendationsPayloadInputs(
            recommendation_count=0,
            last_recommendation_at=None,
            top_recommendations=(),
        ),
        drivers=drivers,
    )
    readiness_section = full["readiness"]
    drivers_section = full["drivers"]
    assert isinstance(readiness_section, dict)
    assert isinstance(drivers_section, dict)
    return readiness_section, drivers_section


def build_recommendations_payload_section(
    recommendations: TwinRecommendationsPayloadInputs,
) -> dict[str, object]:
    full = build_twin_payload_v1(
        readiness=TwinReadinessPayloadInputs(
            result=ReadinessResultV1_1(
                overall_score=None,
                knowledge_subscore=None,
                retention_subscore=None,
                confidence_subscore=None,
                coverage_subscore=None,
                rated_node_count=0,
                total_node_count=0,
                unrated=True,
            ),
            drivers=None,
        ),
        revision_queue=TwinRevisionQueuePayloadInputs(due_revision_count=0, high_risk_concept_count=0),
        recommendations=recommendations,
        drivers=None,
    )
    recommendations_section = full["recommendations"]
    assert isinstance(recommendations_section, dict)
    return recommendations_section


def build_queue_payload_section(
    revision_queue: TwinRevisionQueuePayloadInputs,
) -> dict[str, object]:
    return {
        "due_revision_count": revision_queue.due_revision_count,
        "high_risk_concept_count": revision_queue.high_risk_concept_count,
    }


def build_study_plan_payload_section(
    *,
    generated_at: datetime | None,
    daily_item_count: int,
    weekly_item_count: int,
    total_estimated_gain: Decimal,
) -> dict[str, object]:
    return {
        "generated_at": _iso(generated_at),
        "daily_items": daily_item_count,
        "weekly_items": weekly_item_count,
        "total_estimated_gain": float(total_estimated_gain),
    }


def build_study_behavior_payload_section(
    *,
    completion_rate: Decimal,
    skip_rate: Decimal,
    average_minutes_variance: Decimal,
) -> dict[str, object]:
    return {
        "completion_rate": float(completion_rate),
        "skip_rate": float(skip_rate),
        "average_minutes_variance": float(average_minutes_variance),
    }


def build_goal_payload_section(
    *,
    target_readiness_score: Decimal,
    target_date: object,
) -> dict[str, object]:
    from datetime import date

    assert isinstance(target_date, date)
    return {
        "target_readiness_score": float(target_readiness_score),
        "target_date": target_date.isoformat(),
    }


def build_forecast_payload_section(
    *,
    current_readiness: Decimal,
    projected_readiness: Decimal,
    gap_to_goal: Decimal,
    on_track: bool,
    days_remaining: int,
    explanation: str = "",
) -> dict[str, object]:
    return {
        "current_readiness": float(current_readiness),
        "projected_readiness": float(projected_readiness),
        "gap_to_goal": float(gap_to_goal),
        "on_track": on_track,
        "days_remaining": days_remaining,
        "explanation": explanation,
    }


def build_predicted_outcome_payload_section(
    *,
    expected_score: Decimal,
    low_score: Decimal,
    high_score: Decimal,
    risk_level: str,
    explanation: str = "",
) -> dict[str, object]:
    from prepos.domain.scoring.predicted_score_v1 import PREDICTED_SCORE_V1

    return {
        "version": PREDICTED_SCORE_V1,
        "expected_score": float(expected_score),
        "low_score": float(low_score),
        "high_score": float(high_score),
        "risk_level": risk_level,
        "explanation": explanation,
    }


def build_simulations_payload_section(
    *,
    current_state: Decimal,
    complete_recommendations: Decimal,
    no_study: Decimal,
) -> dict[str, object]:
    return {
        "current_state": float(current_state),
        "complete_recommendations": float(complete_recommendations),
        "no_study": float(no_study),
    }


def build_trajectory_payload_section(
    *,
    required_gain: Decimal,
    expected_daily_progress: Decimal,
    expected_weekly_progress: Decimal,
) -> dict[str, object]:
    return {
        "required_gain": float(required_gain),
        "expected_daily_progress": float(expected_daily_progress),
        "expected_weekly_progress": float(expected_weekly_progress),
    }


def build_milestones_payload_section(
    milestones: tuple[dict[str, object], ...] | list[dict[str, object]],
) -> list[dict[str, object]]:
    return [dict(milestone) for milestone in milestones]


def build_milestone_status_payload_section(
    *,
    status: str,
    current_gap: Decimal,
    explanation: str = "",
) -> dict[str, object]:
    return {
        "status": status,
        "current_gap": float(current_gap),
        "explanation": explanation,
    }


def merge_twin_payload_sections(
    existing: dict[str, object],
    *,
    readiness: dict[str, object] | None = None,
    drivers: dict[str, object] | None = None,
    recommendations: dict[str, object] | None = None,
    revision_queue: dict[str, object] | None = None,
    study_plan: dict[str, object] | None = None,
    study_behavior: dict[str, object] | None = None,
    goal: dict[str, object] | None = None,
    forecast: dict[str, object] | None = None,
    predicted_outcome: dict[str, object] | None = None,
    simulations: dict[str, object] | None = None,
    trajectory: dict[str, object] | None = None,
    milestones: list[dict[str, object]] | None = None,
    milestone_status: dict[str, object] | None = None,
    forecast_probability: dict[str, object] | None = None,
    forecast_scenarios: dict[str, object] | None = None,
    score_distribution: dict[str, object] | None = None,
    decision: dict[str, object] | None = None,
    intervention: dict[str, object] | None = None,
    intervention_baseline: dict[str, object] | None = None,
    intervention_effectiveness: dict[str, object] | None = None,
    optimization: dict[str, object] | None = None,
    behavior_profile: dict[str, object] | None = None,
    personalization: dict[str, object] | None = None,
    mentor: dict[str, object] | None = None,
) -> dict[str, object]:
    merged = dict(existing)
    if readiness is not None:
        merged["readiness"] = readiness
    if drivers is not None:
        merged["drivers"] = drivers
    if recommendations is not None:
        merged["recommendations"] = recommendations
    if revision_queue is not None:
        merged["revision_queue"] = revision_queue
    if study_plan is not None:
        merged["study_plan"] = study_plan
    if study_behavior is not None:
        merged["study_behavior"] = study_behavior
    if goal is not None:
        merged["goal"] = goal
    if forecast is not None:
        merged["forecast"] = forecast
    if predicted_outcome is not None:
        merged["predicted_outcome"] = predicted_outcome
    if simulations is not None:
        merged["simulations"] = simulations
    if trajectory is not None:
        merged["trajectory"] = trajectory
    if milestones is not None:
        merged["milestones"] = milestones
    if milestone_status is not None:
        merged["milestone_status"] = milestone_status
    if forecast_probability is not None:
        merged["forecast_probability"] = forecast_probability
    if forecast_scenarios is not None:
        merged["forecast_scenarios"] = forecast_scenarios
    if score_distribution is not None:
        merged["score_distribution"] = score_distribution
    if decision is not None:
        merged["decision"] = decision
    if intervention is not None:
        merged["intervention"] = intervention
    if intervention_baseline is not None:
        merged["intervention_baseline"] = intervention_baseline
    if intervention_effectiveness is not None:
        merged["intervention_effectiveness"] = intervention_effectiveness
    if optimization is not None:
        merged["optimization"] = optimization
    if behavior_profile is not None:
        merged["behavior_profile"] = behavior_profile
    if personalization is not None:
        merged["personalization"] = personalization
    if mentor is not None:
        merged["mentor"] = mentor
    if "profile_version" not in merged:
        merged["profile_version"] = TWIN_PROFILE_V1
    return merged


def build_forecast_probability_payload_section(
    *,
    goal_probability: Decimal,
    goal_likelihood: str,
    explanation: str = "",
) -> dict[str, object]:
    from prepos.domain.scoring.forecast_probability_v1 import FORECAST_PROBABILITY_V1

    return {
        "version": FORECAST_PROBABILITY_V1,
        "goal_probability": float(goal_probability),
        "goal_likelihood": goal_likelihood,
        "explanation": explanation,
    }


def build_forecast_scenarios_payload_section(
    *,
    best_case: Decimal,
    expected: Decimal,
    worst_case: Decimal,
) -> dict[str, object]:
    return {
        "best_case": float(best_case),
        "expected": float(expected),
        "worst_case": float(worst_case),
    }


def build_score_distribution_payload_section(
    *,
    optimistic_score: Decimal,
    expected_score: Decimal,
    pessimistic_score: Decimal,
) -> dict[str, object]:
    return {
        "optimistic_score": float(optimistic_score),
        "expected_score": float(expected_score),
        "pessimistic_score": float(pessimistic_score),
    }


def build_decision_payload_section(
    *,
    decision_type: str,
    decision_score: Decimal,
    expected_readiness_gain: Decimal,
    expected_score_gain: Decimal,
    explanation: str,
) -> dict[str, object]:
    from prepos.domain.twin.decision_types_v1 import DECISION_ENGINE_V1

    return {
        "version": DECISION_ENGINE_V1,
        "decision_type": decision_type,
        "decision_score": float(decision_score),
        "expected_readiness_gain": float(expected_readiness_gain),
        "expected_score_gain": float(expected_score_gain),
        "explanation": explanation,
    }


def build_intervention_payload_section(
    *,
    intervention_type: str,
    intervention_score: Decimal,
    urgency: str,
    expected_readiness_gain: Decimal,
    title: str,
    description: str,
) -> dict[str, object]:
    from prepos.domain.twin.intervention_types_v1 import INTERVENTION_V1

    return {
        "version": INTERVENTION_V1,
        "intervention_type": intervention_type,
        "intervention_score": float(intervention_score),
        "urgency": urgency,
        "expected_readiness_gain": float(expected_readiness_gain),
        "title": title,
        "description": description,
    }


def build_intervention_baseline_payload_section(
    *,
    intervention_type: str,
    readiness_score: Decimal,
    predicted_score: Decimal,
    completion_rate: Decimal,
) -> dict[str, object]:
    from prepos.domain.twin.intervention_outcome_types_v1 import INTERVENTION_BASELINE_V1

    return {
        "version": INTERVENTION_BASELINE_V1,
        "intervention_type": intervention_type,
        "readiness_score": float(readiness_score),
        "predicted_score": float(predicted_score),
        "completion_rate": float(completion_rate),
    }


def build_intervention_effectiveness_payload_section(
    *,
    last_effectiveness_score: Decimal,
    outcome_status: str,
    explanation: str = "",
) -> dict[str, object]:
    from prepos.domain.twin.intervention_outcome_types_v1 import INTERVENTION_OUTCOME_V1

    return {
        "version": INTERVENTION_OUTCOME_V1,
        "last_effectiveness_score": float(last_effectiveness_score),
        "outcome_status": outcome_status,
        "explanation": explanation,
    }


def build_optimization_payload_section(
    *,
    best_intervention: str,
    historical_effectiveness: Decimal,
    optimized_intervention_score: Decimal | None = None,
) -> dict[str, object]:
    from prepos.domain.twin.intervention_outcome_types_v1 import INTERVENTION_OPTIMIZER_V1

    section: dict[str, object] = {
        "version": INTERVENTION_OPTIMIZER_V1,
        "best_intervention": best_intervention,
        "historical_effectiveness": float(historical_effectiveness),
    }
    if optimized_intervention_score is not None:
        section["optimized_intervention_score"] = float(optimized_intervention_score)
    return section


def build_behavior_profile_payload_section(
    *,
    consistency_score: Decimal,
    discipline_score: Decimal,
    revision_adherence_score: Decimal,
    weakness_recovery_score: Decimal,
    engagement_score: Decimal,
    learning_style: str,
    risk_profile: str,
    explanation: str = "",
) -> dict[str, object]:
    from prepos.domain.twin.behavior_profile_types_v1 import BEHAVIOR_PROFILE_V1

    return {
        "version": BEHAVIOR_PROFILE_V1,
        "consistency_score": float(consistency_score),
        "discipline_score": float(discipline_score),
        "revision_adherence_score": float(revision_adherence_score),
        "weakness_recovery_score": float(weakness_recovery_score),
        "engagement_score": float(engagement_score),
        "learning_style": learning_style,
        "risk_profile": risk_profile,
        "explanation": explanation,
    }


def extract_baseline_metrics(
    twin_payload: dict[str, object],
    *,
    readiness_score: Decimal | None,
) -> tuple[Decimal, Decimal, Decimal]:
    baseline = twin_payload.get("intervention_baseline")
    if isinstance(baseline, dict):
        readiness = baseline.get("readiness_score")
        predicted = baseline.get("predicted_score")
        completion = baseline.get("completion_rate")
        return (
            Decimal(str(readiness)) if readiness is not None else Decimal("0"),
            Decimal(str(predicted)) if predicted is not None else Decimal("0"),
            Decimal(str(completion)) if completion is not None else Decimal("0"),
        )

    predicted_outcome = twin_payload.get("predicted_outcome")
    study_behavior = twin_payload.get("study_behavior")
    predicted_score = Decimal("0")
    completion_rate = Decimal("0")
    if isinstance(predicted_outcome, dict):
        expected = predicted_outcome.get("expected_score")
        if expected is not None:
            predicted_score = Decimal(str(expected))
    if isinstance(study_behavior, dict):
        completion = study_behavior.get("completion_rate")
        if completion is not None:
            completion_rate = Decimal(str(completion))
    return readiness_score or Decimal("0"), predicted_score, completion_rate
