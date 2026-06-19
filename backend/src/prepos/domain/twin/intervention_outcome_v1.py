from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType

_W_READINESS = Decimal("0.50")
_W_PREDICTED = Decimal("0.30")
_W_COMPLETION = Decimal("0.20")

_HIGHLY_EFFECTIVE_THRESHOLD = Decimal("75")
_EFFECTIVE_THRESHOLD = Decimal("50")
_PARTIALLY_EFFECTIVE_THRESHOLD = Decimal("25")


@dataclass(frozen=True, slots=True)
class InterventionOutcomeInputs:
    intervention_type: TwinInterventionType
    readiness_before: Decimal
    readiness_after: Decimal
    predicted_score_before: Decimal
    predicted_score_after: Decimal
    completion_rate_before: Decimal
    completion_rate_after: Decimal


@dataclass(frozen=True, slots=True)
class InterventionOutcome:
    intervention_type: TwinInterventionType
    effectiveness_score: Decimal
    readiness_delta: Decimal
    predicted_score_delta: Decimal
    completion_delta: Decimal
    outcome_status: InterventionOutcomeStatus


def compute_effectiveness_score_v1(
    *,
    readiness_delta: Decimal,
    predicted_score_delta: Decimal,
    completion_delta: Decimal,
) -> Decimal:
    raw = (
        readiness_delta * _W_READINESS
        + predicted_score_delta * _W_PREDICTED
        + completion_delta * Decimal("100") * _W_COMPLETION
    )
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))


def classify_outcome_status(effectiveness_score: Decimal) -> InterventionOutcomeStatus:
    if effectiveness_score >= _HIGHLY_EFFECTIVE_THRESHOLD:
        return InterventionOutcomeStatus.HIGHLY_EFFECTIVE
    if effectiveness_score >= _EFFECTIVE_THRESHOLD:
        return InterventionOutcomeStatus.EFFECTIVE
    if effectiveness_score >= _PARTIALLY_EFFECTIVE_THRESHOLD:
        return InterventionOutcomeStatus.PARTIALLY_EFFECTIVE
    return InterventionOutcomeStatus.INEFFECTIVE


def compute_intervention_outcome_v1(inputs: InterventionOutcomeInputs) -> InterventionOutcome:
    readiness_delta = round_score(inputs.readiness_after - inputs.readiness_before)
    predicted_score_delta = round_score(inputs.predicted_score_after - inputs.predicted_score_before)
    completion_delta = round_score(inputs.completion_rate_after - inputs.completion_rate_before)
    effectiveness_score = compute_effectiveness_score_v1(
        readiness_delta=readiness_delta,
        predicted_score_delta=predicted_score_delta,
        completion_delta=completion_delta,
    )
    return InterventionOutcome(
        intervention_type=inputs.intervention_type,
        effectiveness_score=effectiveness_score,
        readiness_delta=readiness_delta,
        predicted_score_delta=predicted_score_delta,
        completion_delta=completion_delta,
        outcome_status=classify_outcome_status(effectiveness_score),
    )
