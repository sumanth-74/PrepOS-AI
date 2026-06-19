from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

MENTOR_EFFECTIVENESS_V1 = "mentor_effectiveness_v1"

_SCORE_MAX = Decimal("100")


@dataclass(frozen=True, slots=True)
class CaseEffectivenessInputs:
    total_cases: int
    resolved_cases: int
    risk_reduced_cases: int
    successful_interventions: int
    total_resolution_hours: Decimal


@dataclass(frozen=True, slots=True)
class MentorEffectiveness:
    effectiveness_score: Decimal
    cases_resolved: int
    average_resolution_time_hours: Decimal
    risk_reduction_rate: Decimal


def _rate(*, numerator: int, denominator: int) -> Decimal:
    if denominator <= 0:
        return Decimal("0")
    return clamp(
        Decimal(numerator) / Decimal(denominator) * _SCORE_MAX,
        Decimal("0"),
        _SCORE_MAX,
    )


def compute_mentor_effectiveness_v1(inputs: CaseEffectivenessInputs) -> MentorEffectiveness:
    resolution_rate = _rate(numerator=inputs.resolved_cases, denominator=inputs.total_cases)
    risk_reduction_rate = _rate(
        numerator=inputs.risk_reduced_cases,
        denominator=inputs.resolved_cases,
    )
    intervention_success_rate = _rate(
        numerator=inputs.successful_interventions,
        denominator=inputs.resolved_cases,
    )
    raw_score = (
        resolution_rate * Decimal("0.40")
        + risk_reduction_rate * Decimal("0.30")
        + intervention_success_rate * Decimal("0.30")
    )
    average_resolution_time = (
        inputs.total_resolution_hours / Decimal(inputs.resolved_cases)
        if inputs.resolved_cases > 0
        else Decimal("0")
    )
    return MentorEffectiveness(
        effectiveness_score=round_score(clamp(raw_score, Decimal("0"), _SCORE_MAX)),
        cases_resolved=inputs.resolved_cases,
        average_resolution_time_hours=round_score(average_resolution_time),
        risk_reduction_rate=round_score(risk_reduction_rate),
    )
