from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.goal.milestones_v1 import MilestoneStatus
from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.intervention_score_v1 import compute_intervention_score_v1
from prepos.domain.twin.decision_engine_v1 import TwinDecision
from prepos.domain.twin.decision_types_v1 import TwinDecisionType
from prepos.domain.twin.intervention_explanations_v1 import (
    describe_intervention_v1,
    title_for_intervention_v1,
)
from prepos.domain.twin.intervention_types_v1 import InterventionUrgency, TwinInterventionType
from prepos.domain.twin.personalized_scoring_v1 import (
    PersonalizationContext,
    compute_personalization_multiplier,
    map_intervention_type_to_activity,
)

INTERVENTIONS_V1 = "interventions_v1"

_DUE_REVISION_THRESHOLD = 0
_GOAL_PROBABILITY_CRITICAL = Decimal("40")
_GOAL_PROBABILITY_LOW = Decimal("70")

_DECISION_TO_INTERVENTION: dict[TwinDecisionType, TwinInterventionType] = {
    TwinDecisionType.REVISE_NOW: TwinInterventionType.REVISION_SPRINT,
    TwinDecisionType.FOCUS_WEAKNESS: TwinInterventionType.WEAKNESS_REMEDIATION,
    TwinDecisionType.RECOVER_COVERAGE: TwinInterventionType.COVERAGE_RECOVERY,
    TwinDecisionType.INCREASE_DAILY_CAPACITY: TwinInterventionType.CAPACITY_INCREASE,
    TwinDecisionType.REDUCE_DAILY_CAPACITY: TwinInterventionType.CAPACITY_REDUCTION,
    TwinDecisionType.MAINTAIN_PLAN: TwinInterventionType.MAINTAIN_COURSE,
    TwinDecisionType.GOAL_RECOVERY_MODE: TwinInterventionType.CAPACITY_INCREASE,
}


@dataclass(frozen=True, slots=True)
class TwinInterventionInputs:
    decision: TwinDecision
    goal_probability: Decimal | None
    milestone_status: MilestoneStatus | None
    due_revision_count: int
    daily_plan_count: int
    personalization: PersonalizationContext | None = None


@dataclass(frozen=True, slots=True)
class TwinIntervention:
    intervention_type: TwinInterventionType
    intervention_score: Decimal
    title: str
    description: str
    expected_readiness_gain: Decimal
    urgency: InterventionUrgency


def map_decision_to_intervention(decision_type: TwinDecisionType) -> TwinInterventionType:
    return _DECISION_TO_INTERVENTION[decision_type]


def classify_intervention_urgency(
    *,
    goal_probability: Decimal | None,
    milestone_status: MilestoneStatus | None,
    due_revision_count: int,
    decision_type: TwinDecisionType,
) -> InterventionUrgency:
    if goal_probability is not None and goal_probability < _GOAL_PROBABILITY_CRITICAL:
        return InterventionUrgency.CRITICAL
    if milestone_status == MilestoneStatus.BEHIND:
        return InterventionUrgency.HIGH
    if due_revision_count > _DUE_REVISION_THRESHOLD:
        return InterventionUrgency.HIGH
    if (
        decision_type == TwinDecisionType.MAINTAIN_PLAN
        and goal_probability is not None
        and goal_probability >= _GOAL_PROBABILITY_LOW
    ):
        return InterventionUrgency.LOW
    return InterventionUrgency.MEDIUM


def build_twin_intervention_v1(inputs: TwinInterventionInputs) -> TwinIntervention:
    intervention_type = map_decision_to_intervention(inputs.decision.decision_type)
    urgency = classify_intervention_urgency(
        goal_probability=inputs.goal_probability,
        milestone_status=inputs.milestone_status,
        due_revision_count=inputs.due_revision_count,
        decision_type=inputs.decision.decision_type,
    )
    intervention_score = compute_intervention_score_v1(
        decision_score=inputs.decision.decision_score,
        urgency=urgency.value,
        expected_readiness_gain=inputs.decision.expected_readiness_gain,
    )
    if inputs.personalization is not None:
        activity_type = map_intervention_type_to_activity(intervention_type.value)
        historical_effectiveness = inputs.personalization.effectiveness_by_activity.get(
            activity_type.value,
            Decimal("0"),
        )
        multiplier = compute_personalization_multiplier(
            learning_style=inputs.personalization.learning_style,
            activity_type=activity_type,
            historical_effectiveness=historical_effectiveness,
        )
        intervention_score = round_score(
            clamp(intervention_score * multiplier, Decimal("0"), Decimal("100"))
        )
    title = title_for_intervention_v1(
        intervention_type=intervention_type,
        urgency=urgency,
        due_revision_count=inputs.due_revision_count,
    )
    description = describe_intervention_v1(
        intervention_type=intervention_type,
        urgency=urgency,
        expected_readiness_gain=inputs.decision.expected_readiness_gain,
        daily_plan_count=inputs.daily_plan_count,
    )
    return TwinIntervention(
        intervention_type=intervention_type,
        intervention_score=intervention_score,
        title=title,
        description=description,
        expected_readiness_gain=inputs.decision.expected_readiness_gain,
        urgency=urgency,
    )
