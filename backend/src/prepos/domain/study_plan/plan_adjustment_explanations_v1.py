from __future__ import annotations

from decimal import Decimal

from prepos.domain.study_plan.behavior_metrics_v1 import ConceptBehaviorStats

PLAN_ADJUSTMENT_EXPLANATIONS_V1 = "plan_adjustment_explanations_v1"

_HIGH_COMPLETION_THRESHOLD = Decimal("0.75")
_HIGH_READINESS_GAIN_THRESHOLD = Decimal("4")


def explain_plan_adjustment_v1(
    *,
    priority_score: Decimal,
    adaptive_priority: Decimal,
    readiness_gain: Decimal,
    behavior: ConceptBehaviorStats,
) -> str:
    """Deterministic plan adjustment copy based on execution history."""
    if behavior.skip_rate > Decimal("0") and adaptive_priority > priority_score:
        return "Moved higher because previous sessions were skipped."

    if (
        behavior.completion_rate >= _HIGH_COMPLETION_THRESHOLD
        and adaptive_priority < priority_score
    ):
        return "Priority reduced because you consistently complete revisions."

    if (
        readiness_gain >= _HIGH_READINESS_GAIN_THRESHOLD
        and behavior.completion_rate == Decimal("0")
        and behavior.skip_rate == Decimal("0")
    ):
        return "Estimated gain increased after recent mastery decline."

    return ""
