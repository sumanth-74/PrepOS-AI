from __future__ import annotations

from prepos.application.planning.planning_models import PlanningScoreBreakdown


def explain_planning_decision(*, breakdown: PlanningScoreBreakdown, source_reason: str) -> list[str]:
    explanations = [
        f"Priority score {breakdown.priority_score:.1f}/100 from deterministic planning weights.",
        (
            "Score components: "
            f"weakness {breakdown.weakness_score:.1f}, "
            f"recommendation impact {breakdown.recommendation_impact_score:.1f}, "
            f"PYQ {breakdown.pyq_frequency_score:.1f}, "
            f"forecast risk {breakdown.forecast_risk_score:.1f}, "
            f"current affairs {breakdown.current_affairs_score:.1f}, "
            f"memory success {breakdown.memory_success_score:.1f}."
        ),
        f"Primary scheduling reason: {source_reason}.",
    ]
    if "memory_success" in breakdown.reason_codes:
        explanations.append("Boosted because coaching memory shows this concept responded well before.")
    if "unresolved_weakness" in breakdown.reason_codes:
        explanations.append("Prioritized because weakness remains unresolved.")
    if "pyq_frequency" in breakdown.reason_codes:
        explanations.append("Elevated due to PYQ frequency signal.")
    return explanations
