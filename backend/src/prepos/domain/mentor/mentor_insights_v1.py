from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.mentor.mentor_explanations_v1 import insight_message, insight_title
from prepos.domain.mentor.mentor_types_v1 import (
    _CONSISTENCY_POSITIVE_THRESHOLD,
    _DUE_REVISION_HIGH_THRESHOLD,
    _GOAL_PROBABILITY_AT_RISK,
    _GOAL_PROBABILITY_CRITICAL,
    _READINESS_ALERT_THRESHOLD,
    InsightPriority,
    InsightType,
)
from prepos.domain.twin.behavior_profile_types_v1 import RiskProfile

MENTOR_INSIGHTS_V1 = "mentor_insights_v1"


@dataclass(frozen=True, slots=True)
class ReadinessSignals:
    readiness_score: Decimal | None
    coverage_subscore: Decimal | None
    largest_negative_driver: str | None


@dataclass(frozen=True, slots=True)
class ForecastSignals:
    goal_probability: Decimal | None
    gap_to_goal: Decimal | None
    on_track: bool | None


@dataclass(frozen=True, slots=True)
class MilestoneSignals:
    milestone_status: str | None
    current_gap: Decimal | None


@dataclass(frozen=True, slots=True)
class InterventionEffectivenessSignals:
    last_effectiveness_score: Decimal | None
    historical_effectiveness: Decimal | None
    outcome_status: str | None


@dataclass(frozen=True, slots=True)
class BehaviorProfileSignals:
    consistency_score: Decimal | None
    discipline_score: Decimal | None
    risk_profile: str | None
    learning_style: str | None


@dataclass(frozen=True, slots=True)
class PersonalizationSignals:
    best_activity_type: str | None
    top_multiplier: Decimal | None
    historical_effectiveness: Decimal | None


@dataclass(frozen=True, slots=True)
class StudyPlanSignals:
    total_estimated_gain: Decimal | None
    daily_item_count: int
    completion_rate: Decimal | None


@dataclass(frozen=True, slots=True)
class OptimizationSignals:
    best_intervention: str | None
    historical_effectiveness: Decimal | None
    optimized_intervention_score: Decimal | None


@dataclass(frozen=True, slots=True)
class MentorInsightInputs:
    readiness: ReadinessSignals
    forecast: ForecastSignals
    milestones: MilestoneSignals
    intervention_effectiveness: InterventionEffectivenessSignals
    behavior_profile: BehaviorProfileSignals
    personalization: PersonalizationSignals
    study_plan: StudyPlanSignals
    optimization: OptimizationSignals
    due_revision_count: int = 0
    high_risk_concept_count: int = 0


@dataclass(frozen=True, slots=True)
class MentorInsight:
    insight_type: InsightType
    priority: InsightPriority
    title: str
    message: str
    supporting_signals: tuple[str, ...]


def classify_insight_priority(
    *,
    insight_type: InsightType,
    goal_probability: Decimal | None,
    milestone_status: str | None,
    due_revision_count: int,
    risk_profile: str | None,
) -> InsightPriority:
    if (
        goal_probability is not None
        and goal_probability < Decimal(str(_GOAL_PROBABILITY_CRITICAL))
        and insight_type in {
            InsightType.GOAL_RISK,
            InsightType.MILESTONE_ALERT,
            InsightType.READINESS_ALERT,
        }
    ):
        return InsightPriority.CRITICAL
    if milestone_status == MilestoneStatus.BEHIND.value and insight_type == InsightType.MILESTONE_ALERT:
        return InsightPriority.CRITICAL
    if due_revision_count > _DUE_REVISION_HIGH_THRESHOLD and insight_type == InsightType.REVISION_WARNING:
        return InsightPriority.HIGH
    if (
        goal_probability is not None
        and goal_probability < Decimal(str(_GOAL_PROBABILITY_AT_RISK))
        and insight_type == InsightType.GOAL_RISK
    ):
        return InsightPriority.HIGH
    if risk_profile == RiskProfile.MEDIUM_RISK.value and insight_type == InsightType.BEHAVIOR_WARNING:
        return InsightPriority.MEDIUM
    if risk_profile == RiskProfile.HIGH_RISK.value and insight_type == InsightType.BEHAVIOR_WARNING:
        return InsightPriority.HIGH
    if insight_type == InsightType.POSITIVE_PROGRESS:
        return InsightPriority.LOW
    if insight_type == InsightType.OPTIMIZATION_OPPORTUNITY:
        return InsightPriority.MEDIUM
    if insight_type == InsightType.READINESS_ALERT:
        return InsightPriority.HIGH
    return InsightPriority.MEDIUM


def _supporting_signals(*signals: str | None) -> tuple[str, ...]:
    return tuple(signal for signal in signals if signal)


def generate_mentor_insights_v1(inputs: MentorInsightInputs) -> tuple[MentorInsight, ...]:
    insights: list[MentorInsight] = []
    goal_probability = inputs.forecast.goal_probability
    readiness_score = inputs.readiness.readiness_score
    consistency_score = inputs.behavior_profile.consistency_score
    due_revision_count = inputs.due_revision_count
    milestone_status = inputs.milestones.milestone_status
    risk_profile = inputs.behavior_profile.risk_profile
    best_intervention = inputs.optimization.best_intervention

    if goal_probability is not None and goal_probability < Decimal(str(_GOAL_PROBABILITY_AT_RISK)):
        insight_type = InsightType.GOAL_RISK
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(insight_type, goal_probability=float(goal_probability)),
                supporting_signals=_supporting_signals(
                    "goal_probability",
                    "forecast_probability",
                ),
            )
        )

    if due_revision_count > _DUE_REVISION_HIGH_THRESHOLD:
        insight_type = InsightType.REVISION_WARNING
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(insight_type, due_revision_count=due_revision_count),
                supporting_signals=_supporting_signals(
                    "due_revision_count",
                    "revision_queue",
                ),
            )
        )

    if milestone_status == MilestoneStatus.BEHIND.value:
        insight_type = InsightType.MILESTONE_ALERT
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(insight_type),
                supporting_signals=_supporting_signals(
                    "milestone_status",
                    "milestones",
                ),
            )
        )

    if (
        readiness_score is not None
        and readiness_score < Decimal(str(_READINESS_ALERT_THRESHOLD))
    ):
        insight_type = InsightType.READINESS_ALERT
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(
                    insight_type,
                    readiness_score=float(readiness_score),
                ),
                supporting_signals=_supporting_signals(
                    "readiness_score",
                    inputs.readiness.largest_negative_driver,
                ),
            )
        )

    if risk_profile in {RiskProfile.MEDIUM_RISK.value, RiskProfile.HIGH_RISK.value}:
        insight_type = InsightType.BEHAVIOR_WARNING
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(insight_type),
                supporting_signals=_supporting_signals(
                    "risk_profile",
                    "behavior_profile",
                ),
            )
        )

    if (
        inputs.optimization.historical_effectiveness is not None
        and inputs.optimization.historical_effectiveness >= Decimal("50")
        and best_intervention is not None
    ):
        insight_type = InsightType.OPTIMIZATION_OPPORTUNITY
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(insight_type, best_intervention=best_intervention),
                supporting_signals=_supporting_signals(
                    "optimization",
                    "historical_effectiveness",
                    best_intervention,
                ),
            )
        )

    if (
        consistency_score is not None
        and consistency_score > Decimal(str(_CONSISTENCY_POSITIVE_THRESHOLD))
    ):
        insight_type = InsightType.POSITIVE_PROGRESS
        insights.append(
            MentorInsight(
                insight_type=insight_type,
                priority=classify_insight_priority(
                    insight_type=insight_type,
                    goal_probability=goal_probability,
                    milestone_status=milestone_status,
                    due_revision_count=due_revision_count,
                    risk_profile=risk_profile,
                ),
                title=insight_title(insight_type),
                message=insight_message(
                    insight_type,
                    consistency_score=float(consistency_score),
                ),
                supporting_signals=_supporting_signals(
                    "consistency_score",
                    "behavior_profile",
                ),
            )
        )

    priority_rank = {
        InsightPriority.CRITICAL: 0,
        InsightPriority.HIGH: 1,
        InsightPriority.MEDIUM: 2,
        InsightPriority.LOW: 3,
    }
    insights.sort(key=lambda item: (priority_rank[item.priority], item.insight_type.value))
    return tuple(insights)
