from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_action_explanations_v1 import explain_escalation_v1
from prepos.domain.mentor.mentor_insights_v1 import MentorInsightInputs
from prepos.domain.mentor.mentor_types_v1 import EscalationLevel
from prepos.domain.twin.behavior_profile_types_v1 import RiskProfile

ESCALATION_V1 = "escalation_v1"

_GOAL_PROBABILITY_CRITICAL = Decimal("30")
_GOAL_PROBABILITY_HIGH = Decimal("50")


@dataclass(frozen=True, slots=True)
class EscalationSignal:
    level: EscalationLevel
    reason: str


def classify_escalation_level_v1(inputs: MentorInsightInputs) -> EscalationLevel:
    goal_probability = inputs.forecast.goal_probability
    if goal_probability is not None and goal_probability < _GOAL_PROBABILITY_CRITICAL:
        return EscalationLevel.CRITICAL
    if goal_probability is not None and goal_probability < _GOAL_PROBABILITY_HIGH:
        return EscalationLevel.HIGH
    if inputs.milestones.milestone_status == MilestoneStatus.BEHIND.value:
        return EscalationLevel.MEDIUM
    if inputs.behavior_profile.risk_profile == RiskProfile.HIGH_RISK.value:
        return EscalationLevel.LOW
    return EscalationLevel.NONE


def build_escalation_signal_v1(inputs: MentorInsightInputs) -> EscalationSignal:
    level = classify_escalation_level_v1(inputs)
    return EscalationSignal(
        level=level,
        reason=explain_escalation_v1(level=level),
    )
