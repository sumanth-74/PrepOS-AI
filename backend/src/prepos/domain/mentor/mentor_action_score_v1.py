from __future__ import annotations

from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_insights_v1 import MentorInsightInputs
from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.twin.behavior_profile_types_v1 import RiskProfile

MENTOR_ACTION_SCORE_V1 = "mentor_action_score_v1"

_GOAL_PROBABILITY_MAX = Decimal("100")
_REVISION_CAP = Decimal("10")


def _risk_factor(*, goal_probability: Decimal | None, risk_profile: str | None) -> Decimal:
    if goal_probability is not None:
        return clamp(_GOAL_PROBABILITY_MAX - goal_probability, Decimal("0"), _GOAL_PROBABILITY_MAX)
    if risk_profile == RiskProfile.HIGH_RISK.value:
        return Decimal("80")
    if risk_profile == RiskProfile.MEDIUM_RISK.value:
        return Decimal("50")
    return Decimal("20")


def _milestone_factor(*, milestone_status: str | None, current_gap: Decimal | None) -> Decimal:
    if milestone_status == MilestoneStatus.BEHIND.value:
        return Decimal("100")
    if current_gap is not None and current_gap > Decimal("0"):
        return clamp(current_gap * Decimal("5"), Decimal("0"), _GOAL_PROBABILITY_MAX)
    return Decimal("0")


def _revision_factor(*, due_revision_count: int) -> Decimal:
    return clamp(Decimal(due_revision_count) * Decimal("10"), Decimal("0"), _GOAL_PROBABILITY_MAX)


def _effectiveness_factor(*, historical_effectiveness: Decimal | None) -> Decimal:
    if historical_effectiveness is None:
        return Decimal("0")
    return clamp(historical_effectiveness, Decimal("0"), _GOAL_PROBABILITY_MAX)


def compute_mentor_action_priority_score_v1(inputs: MentorInsightInputs) -> Decimal:
    risk = _risk_factor(
        goal_probability=inputs.forecast.goal_probability,
        risk_profile=inputs.behavior_profile.risk_profile,
    )
    milestone = _milestone_factor(
        milestone_status=inputs.milestones.milestone_status,
        current_gap=inputs.milestones.current_gap,
    )
    revision = _revision_factor(due_revision_count=inputs.due_revision_count)
    effectiveness = _effectiveness_factor(
        historical_effectiveness=inputs.intervention_effectiveness.historical_effectiveness,
    )
    raw = (
        risk * Decimal("0.40")
        + milestone * Decimal("0.30")
        + revision * Decimal("0.20")
        + effectiveness * Decimal("0.10")
    )
    return round_score(clamp(raw, Decimal("0"), _GOAL_PROBABILITY_MAX))
