from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_action_explanations_v1 import explain_mentor_action_v1
from prepos.domain.mentor.mentor_action_score_v1 import compute_mentor_action_priority_score_v1
from prepos.domain.mentor.mentor_insights_v1 import MentorInsight, MentorInsightInputs
from prepos.domain.mentor.mentor_summary_v1 import MentorSummary
from prepos.domain.mentor.mentor_types_v1 import (
    _DUE_REVISION_HIGH_THRESHOLD,
    _GOAL_PROBABILITY_CRITICAL,
    ActionUrgency,
    MentorActionType,
)
from prepos.domain.scoring.common import round_score
from prepos.domain.twin.behavior_profile_types_v1 import RiskProfile

MENTOR_ACTIONS_V1 = "mentor_actions_v1"


@dataclass(frozen=True, slots=True)
class MentorActionInputs:
    summary: MentorSummary
    insights: tuple[MentorInsight, ...]
    signals: MentorInsightInputs


@dataclass(frozen=True, slots=True)
class MentorAction:
    action_type: MentorActionType
    priority_score: Decimal
    urgency: ActionUrgency
    explanation: str
    expected_impact: Decimal


def _select_action_type(inputs: MentorActionInputs) -> MentorActionType:
    signals = inputs.signals
    goal_probability = signals.forecast.goal_probability
    if goal_probability is not None and goal_probability < Decimal(str(_GOAL_PROBABILITY_CRITICAL)):
        return MentorActionType.ESCALATE_RISK
    if signals.behavior_profile.risk_profile == RiskProfile.HIGH_RISK.value:
        return MentorActionType.CONTACT_STUDENT
    if signals.milestones.milestone_status == MilestoneStatus.BEHIND.value:
        return MentorActionType.SCHEDULE_REVIEW
    if signals.due_revision_count > _DUE_REVISION_HIGH_THRESHOLD:
        return MentorActionType.ASSIGN_REVISION_SPRINT
    if signals.forecast.on_track is False or (
        signals.forecast.gap_to_goal is not None and signals.forecast.gap_to_goal > Decimal("0")
    ):
        return MentorActionType.INCREASE_STUDY_TARGET
    return MentorActionType.NO_ACTION_REQUIRED


def _urgency_for_action(
    *,
    action_type: MentorActionType,
    priority_score: Decimal,
) -> ActionUrgency:
    if action_type == MentorActionType.ESCALATE_RISK or priority_score >= Decimal("80"):
        return ActionUrgency.HIGH
    if priority_score >= Decimal("60"):
        return ActionUrgency.MEDIUM
    if action_type == MentorActionType.NO_ACTION_REQUIRED:
        return ActionUrgency.LOW
    return ActionUrgency.MEDIUM


def _expected_impact(*, inputs: MentorActionInputs, priority_score: Decimal) -> Decimal:
    plan_gain = inputs.signals.study_plan.total_estimated_gain or Decimal("0")
    if inputs.signals.due_revision_count > _DUE_REVISION_HIGH_THRESHOLD:
        return round_score(plan_gain * Decimal("0.40") or priority_score / Decimal("10"))
    return round_score(plan_gain * Decimal("0.25") or priority_score / Decimal("15"))


def select_mentor_action_type_v1(inputs: MentorActionInputs) -> MentorActionType:
    return _select_action_type(inputs)


def build_mentor_action_v1(
    inputs: MentorActionInputs,
    *,
    action_effectiveness_score: Decimal | None = None,
) -> MentorAction:
    from prepos.domain.mentor.mentor_effectiveness_learning_v1 import apply_optimized_priority_v1

    action_type = _select_action_type(inputs)
    base_priority = compute_mentor_action_priority_score_v1(inputs.signals)
    priority_score = base_priority
    if action_effectiveness_score is not None:
        priority_score = apply_optimized_priority_v1(
            base_priority=base_priority,
            effectiveness_score=action_effectiveness_score,
        )
    urgency = _urgency_for_action(action_type=action_type, priority_score=priority_score)
    return MentorAction(
        action_type=action_type,
        priority_score=priority_score,
        urgency=urgency,
        explanation=explain_mentor_action_v1(action_type=action_type),
        expected_impact=_expected_impact(inputs=inputs, priority_score=priority_score),
    )
