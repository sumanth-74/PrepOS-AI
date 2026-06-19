from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.mentor.mentor_explanations_v1 import overall_status_key_message
from prepos.domain.mentor.mentor_insights_v1 import MentorInsight, MentorInsightInputs
from prepos.domain.mentor.mentor_types_v1 import (
    _GOAL_PROBABILITY_AT_RISK,
    _GOAL_PROBABILITY_CRITICAL,
    _GOAL_PROBABILITY_EXCELLENT,
    _READINESS_EXCELLENT,
    _READINESS_GOOD,
    InsightPriority,
    OverallStatus,
)

MENTOR_SUMMARY_V1 = "mentor_summary_v1"


@dataclass(frozen=True, slots=True)
class MentorSummary:
    overall_status: OverallStatus
    key_message: str
    strongest_signal: str
    weakest_signal: str


def classify_overall_status(
    *,
    readiness_score: Decimal | None,
    goal_probability: Decimal | None,
) -> OverallStatus:
    if goal_probability is not None and goal_probability < Decimal(str(_GOAL_PROBABILITY_CRITICAL)):
        return OverallStatus.CRITICAL
    if goal_probability is not None and goal_probability < Decimal(str(_GOAL_PROBABILITY_AT_RISK)):
        return OverallStatus.AT_RISK
    if (
        readiness_score is not None
        and readiness_score >= Decimal(str(_READINESS_EXCELLENT))
        and goal_probability is not None
        and goal_probability >= Decimal(str(_GOAL_PROBABILITY_EXCELLENT))
    ):
        return OverallStatus.EXCELLENT
    if readiness_score is not None and readiness_score >= Decimal(str(_READINESS_GOOD)):
        return OverallStatus.GOOD
    return OverallStatus.AT_RISK


def _strongest_signal(inputs: MentorInsightInputs, insights: tuple[MentorInsight, ...]) -> str:
    if any(item.insight_type.value == "POSITIVE_PROGRESS" for item in insights):
        return "consistency"
    if inputs.behavior_profile.consistency_score is not None:
        return "consistency"
    if inputs.optimization.historical_effectiveness is not None:
        return "intervention_effectiveness"
    if inputs.readiness.largest_negative_driver:
        return inputs.readiness.largest_negative_driver
    return "readiness"


def _weakest_signal(inputs: MentorInsightInputs, insights: tuple[MentorInsight, ...]) -> str:
    if inputs.readiness.largest_negative_driver:
        return inputs.readiness.largest_negative_driver
    if inputs.due_revision_count > 0:
        return "revision_backlog"
    if inputs.readiness.coverage_subscore is not None:
        return "coverage"
    if any(item.priority == InsightPriority.CRITICAL for item in insights):
        return "goal_probability"
    return "readiness"


def build_mentor_summary_v1(
    *,
    inputs: MentorInsightInputs,
    insights: tuple[MentorInsight, ...],
) -> MentorSummary:
    overall_status = classify_overall_status(
        readiness_score=inputs.readiness.readiness_score,
        goal_probability=inputs.forecast.goal_probability,
    )
    key_message = overall_status_key_message(overall_status)
    if insights:
        key_message = insights[0].message
    return MentorSummary(
        overall_status=overall_status,
        key_message=key_message,
        strongest_signal=_strongest_signal(inputs, insights),
        weakest_signal=_weakest_signal(inputs, insights),
    )
