from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_explanations_v1 import coaching_rationale
from prepos.domain.mentor.mentor_insights_v1 import MentorInsightInputs
from prepos.domain.mentor.mentor_types_v1 import (
    _DUE_REVISION_HIGH_THRESHOLD,
    _GOAL_PROBABILITY_AT_RISK,
    CoachingAction,
)
from prepos.domain.scoring.common import round_score
from prepos.domain.study_plan.value_objects import ActivityType

COACHING_RECOMMENDATIONS_V1 = "coaching_recommendations_v1"


@dataclass(frozen=True, slots=True)
class CoachingRecommendation:
    action: CoachingAction
    rationale: str
    expected_gain: Decimal


def generate_coaching_recommendations_v1(
    inputs: MentorInsightInputs,
) -> tuple[CoachingRecommendation, ...]:
    recommendations: list[CoachingRecommendation] = []
    goal_probability = inputs.forecast.goal_probability
    due_revision_count = inputs.due_revision_count
    milestone_status = inputs.milestones.milestone_status
    best_activity = inputs.personalization.best_activity_type
    plan_gain = inputs.study_plan.total_estimated_gain or Decimal("0")

    if due_revision_count > _DUE_REVISION_HIGH_THRESHOLD:
        recommendations.append(
            CoachingRecommendation(
                action=CoachingAction.COMPLETE_REVISIONS,
                rationale=coaching_rationale(CoachingAction.COMPLETE_REVISIONS),
                expected_gain=round_score(Decimal(due_revision_count) * Decimal("0.8")),
            )
        )

    if (
        best_activity == ActivityType.WEAKNESS_RECOVERY.value
        or inputs.high_risk_concept_count > 0
    ):
        recommendations.append(
            CoachingRecommendation(
                action=CoachingAction.FOCUS_WEAKNESS_RECOVERY,
                rationale=coaching_rationale(CoachingAction.FOCUS_WEAKNESS_RECOVERY),
                expected_gain=round_score(plan_gain * Decimal("0.35") or Decimal("2.5")),
            )
        )

    if (
        milestone_status == MilestoneStatus.BEHIND.value
        or (
            goal_probability is not None
            and goal_probability < Decimal(str(_GOAL_PROBABILITY_AT_RISK))
        )
    ):
        recommendations.append(
            CoachingRecommendation(
                action=CoachingAction.INCREASE_DAILY_STUDY_TIME,
                rationale=coaching_rationale(CoachingAction.INCREASE_DAILY_STUDY_TIME),
                expected_gain=round_score(plan_gain * Decimal("0.25") or Decimal("3.0")),
            )
        )

    if not recommendations:
        recommendations.append(
            CoachingRecommendation(
                action=CoachingAction.MAINTAIN_CURRENT_PLAN,
                rationale=coaching_rationale(CoachingAction.MAINTAIN_CURRENT_PLAN),
                expected_gain=round_score(plan_gain or Decimal("1.5")),
            )
        )

    return tuple(recommendations)
