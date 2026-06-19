from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import round_score
from prepos.domain.twin.intervention_types_v1 import InterventionUrgency, TwinInterventionType

INTERVENTION_EXPLANATIONS_V1 = "intervention_explanations_v1"


def _format_gain(value: Decimal) -> str:
    return f"{round_score(value):.2f}".rstrip("0").rstrip(".")


def title_for_intervention_v1(
    *,
    intervention_type: TwinInterventionType,
    urgency: InterventionUrgency,
    due_revision_count: int,
) -> str:
    if intervention_type == TwinInterventionType.REVISION_SPRINT:
        return f"Complete {due_revision_count} overdue revision sprint"
    if intervention_type == TwinInterventionType.WEAKNESS_REMEDIATION:
        return "Target weak concepts this week"
    if intervention_type == TwinInterventionType.COVERAGE_RECOVERY:
        return "Expand concept coverage"
    if intervention_type == TwinInterventionType.CAPACITY_INCREASE:
        prefix = "Urgent: increase study capacity" if urgency == InterventionUrgency.CRITICAL else "Increase daily study capacity"
        return prefix
    if intervention_type == TwinInterventionType.CAPACITY_REDUCTION:
        return "Reduce daily study load"
    if intervention_type == TwinInterventionType.MOCK_TEST:
        return "Schedule a mock test"
    return "Maintain current study course"


def describe_intervention_v1(
    *,
    intervention_type: TwinInterventionType,
    urgency: InterventionUrgency,
    expected_readiness_gain: Decimal,
    daily_plan_count: int,
) -> str:
    gain = _format_gain(expected_readiness_gain)
    if intervention_type == TwinInterventionType.REVISION_SPRINT:
        return (
            "Clear overdue revision items before adding new study topics to stabilize retention."
        )
    if intervention_type == TwinInterventionType.WEAKNESS_REMEDIATION:
        return (
            f"Focus on high-risk weak concepts from your revision queue to gain about {gain} readiness points."
        )
    if intervention_type == TwinInterventionType.COVERAGE_RECOVERY:
        return "Rate additional concepts to improve coverage and unlock more reliable readiness signals."
    if intervention_type == TwinInterventionType.CAPACITY_INCREASE:
        return (
            f"Add focused study time to your daily plan; completing {daily_plan_count} planned items "
            f"could improve readiness by about {gain} points."
        )
    if intervention_type == TwinInterventionType.CAPACITY_REDUCTION:
        return "You are ahead of schedule; a lighter daily load preserves momentum without burnout."
    if intervention_type == TwinInterventionType.MOCK_TEST:
        return "Take a timed mock test to calibrate exam readiness and identify remaining gaps."
    return "Continue executing your current study plan to maintain steady progress."
