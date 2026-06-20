from __future__ import annotations

from prepos.application.institution_outcomes.outcome_models import InitiativeEffectivenessItem, OutcomeItem, RoiItem


def explain_outcome(outcome: OutcomeItem) -> str:
    return (
        f"{outcome.outcome_type}: readiness {outcome.before.readiness:.1f} → "
        f"{outcome.after.readiness:.1f} ({outcome.readiness_gain:+.1f}), "
        f"forecast {outcome.before.forecast:.1f} → {outcome.after.forecast:.1f} "
        f"({outcome.forecast_gain:+.1f}), expected gain {outcome.expected_gain:.1f}, "
        f"actual {outcome.actual_gain:.1f}, variance {outcome.variance:+.1f}."
    )


def explain_roi(item: RoiItem) -> str:
    title = item.title or item.subject_key
    return (
        f"{title}: ROI score {item.roi_score:.1f}/100. "
        f"Readiness +{item.readiness_gain:.1f}, forecast +{item.forecast_gain:.1f}, "
        f"health +{item.cohort_health_gain:.1f}, risk -{item.risk_reduction:.0f}. "
        f"{item.calculation}"
    )


def explain_effectiveness(item: InitiativeEffectivenessItem) -> str:
    return (
        f"{item.title} ({item.initiative_type}): {item.status}, "
        f"effectiveness {item.effectiveness_score:.1f}/100, ROI {item.roi_score:.1f}."
    )
