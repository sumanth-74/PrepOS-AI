from __future__ import annotations

from prepos.application.interventions.intervention_models import InterventionScoreBreakdown


def explain_intervention(
    *,
    intervention_type: str,
    concept: str | None,
    reason: str,
    predicted_gain: float,
    priority_score: float,
    score_breakdown: InterventionScoreBreakdown,
    forecast_improvement: float,
) -> list[str]:
    label = concept or intervention_type.replace("_", " ")
    lines = [
        f"Recommended {intervention_type.replace('_', ' ')} for {label}.",
        reason + ".",
        f"Priority score {priority_score:.1f}/100 from forecast risk ({score_breakdown.forecast_risk:.1f}), "
        f"weakness ({score_breakdown.weakness:.1f}), historical failure ({score_breakdown.historical_failure:.1f}), "
        f"PYQ importance ({score_breakdown.pyq_importance:.1f}), and memory signal ({score_breakdown.memory_signal:.1f}).",
        f"Predicted readiness gain: +{predicted_gain:.1f}.",
        f"Estimated forecast improvement: +{forecast_improvement:.1f} readiness points.",
    ]
    return lines
