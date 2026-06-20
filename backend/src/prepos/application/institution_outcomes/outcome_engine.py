from __future__ import annotations

from prepos.application.institution_outcomes.outcome_models import InitiativeInput, MetricSnapshot, OutcomeItem, OutcomeState

OUTCOME_ENGINE_V1 = "outcome_engine_v1"


def measure_outcome(
    *,
    initiative: InitiativeInput,
    outcome_type: str | None = None,
) -> OutcomeItem:
    readiness_gain = initiative.after.readiness - initiative.before.readiness
    forecast_gain = initiative.after.forecast - initiative.before.forecast
    cohort_health_gain = initiative.after.cohort_health - initiative.before.cohort_health
    risk_reduction = float(initiative.before.risk_count - initiative.after.risk_count)

    expected_gain = (
        initiative.expected_readiness_gain * 0.40
        + initiative.expected_forecast_gain * 0.30
        + initiative.expected_cohort_health_gain * 0.20
        + initiative.expected_risk_reduction * 0.10
    )
    actual_gain = (
        readiness_gain * 0.40
        + forecast_gain * 0.30
        + cohort_health_gain * 0.20
        + risk_reduction * 0.10
    )
    variance = actual_gain - expected_gain

    resolved_type = outcome_type or _outcome_type_for_initiative(initiative.initiative_type)
    return OutcomeItem(
        initiative_id=initiative.initiative_id,
        outcome_type=resolved_type,
        subject_key=initiative.initiative_id.hex,
        before=OutcomeState(
            readiness=round(initiative.before.readiness, 2),
            forecast=round(initiative.before.forecast, 2),
            cohort_health=round(initiative.before.cohort_health, 2),
            risk_count=initiative.before.risk_count,
        ),
        after=OutcomeState(
            readiness=round(initiative.after.readiness, 2),
            forecast=round(initiative.after.forecast, 2),
            cohort_health=round(initiative.after.cohort_health, 2),
            risk_count=initiative.after.risk_count,
        ),
        actual_gain=round(actual_gain, 2),
        expected_gain=round(expected_gain, 2),
        variance=round(variance, 2),
        readiness_gain=round(readiness_gain, 2),
        forecast_gain=round(forecast_gain, 2),
        cohort_health_gain=round(cohort_health_gain, 2),
        risk_reduction=round(risk_reduction, 2),
    )


def measure_outcomes(initiatives: list[InitiativeInput]) -> list[OutcomeItem]:
    return [measure_outcome(initiative=initiative) for initiative in initiatives]


def aggregate_outcome_metrics(outcomes: list[OutcomeItem]) -> dict[str, float]:
    if not outcomes:
        return {
            "average_readiness_uplift": 0.0,
            "average_forecast_uplift": 0.0,
            "average_risk_reduction": 0.0,
        }
    count = len(outcomes)
    return {
        "average_readiness_uplift": round(sum(item.readiness_gain for item in outcomes) / count, 2),
        "average_forecast_uplift": round(sum(item.forecast_gain for item in outcomes) / count, 2),
        "average_risk_reduction": round(sum(item.risk_reduction for item in outcomes) / count, 2),
    }


def _outcome_type_for_initiative(initiative_type: str) -> str:
    mapping = {
        "revision_campaign": "revision_campaign",
        "mentor_training": "mentor_intervention_program",
        "current_affairs_boost": "current_affairs_campaign",
        "forecast_recovery": "forecast_recovery_program",
        "weak_concept_program": "weak_concept_remediation",
        "pyq_focus_program": "pyq_campaign",
    }
    return mapping.get(initiative_type, initiative_type)


def default_expected_gains(initiative_type: str) -> dict[str, float | int]:
    defaults: dict[str, dict[str, float | int]] = {
        "revision_campaign": {
            "readiness_gain": 6.0,
            "forecast_gain": 4.0,
            "cohort_health_gain": 5.0,
            "risk_reduction": 8,
        },
        "mentor_training": {
            "readiness_gain": 5.0,
            "forecast_gain": 5.0,
            "cohort_health_gain": 4.0,
            "risk_reduction": 10,
        },
        "current_affairs_boost": {
            "readiness_gain": 4.0,
            "forecast_gain": 3.0,
            "cohort_health_gain": 3.0,
            "risk_reduction": 4,
        },
        "forecast_recovery": {
            "readiness_gain": 3.0,
            "forecast_gain": 8.0,
            "cohort_health_gain": 4.0,
            "risk_reduction": 6,
        },
        "weak_concept_program": {
            "readiness_gain": 7.0,
            "forecast_gain": 5.0,
            "cohort_health_gain": 6.0,
            "risk_reduction": 9,
        },
        "pyq_focus_program": {
            "readiness_gain": 5.0,
            "forecast_gain": 6.0,
            "cohort_health_gain": 4.0,
            "risk_reduction": 5,
        },
    }
    return defaults.get(
        initiative_type,
        {"readiness_gain": 5.0, "forecast_gain": 3.0, "cohort_health_gain": 4.0, "risk_reduction": 5},
    )
