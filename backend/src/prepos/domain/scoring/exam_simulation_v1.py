from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from prepos.domain.scoring.common import clamp, round_score

EXAM_SIMULATION_V1 = "exam_simulation_v1"

_RETENTION_DECAY_FACTOR = Decimal("0.15")
_MIN_RETENTION_DECAY_PENALTY = Decimal("5")


class ExamSimulationScenario(StrEnum):
    CURRENT_STATE = "CURRENT_STATE"
    COMPLETE_RECOMMENDATIONS = "COMPLETE_RECOMMENDATIONS"
    NO_STUDY = "NO_STUDY"


@dataclass(frozen=True, slots=True)
class ExamSimulationInputs:
    current_predicted_score: Decimal
    total_estimated_gain: Decimal
    retention_subscore: Decimal | None


@dataclass(frozen=True, slots=True)
class ExamSimulationResult:
    current_state: Decimal
    complete_recommendations: Decimal
    no_study: Decimal


def compute_retention_decay_penalty(retention_subscore: Decimal | None) -> Decimal:
    if retention_subscore is None:
        return _MIN_RETENTION_DECAY_PENALTY
    penalty = (Decimal("100") - retention_subscore) * _RETENTION_DECAY_FACTOR
    return round_score(max(penalty, _MIN_RETENTION_DECAY_PENALTY))


def _clamp_score(value: Decimal) -> Decimal:
    return round_score(clamp(value, Decimal("0"), Decimal("100")))


def simulate_exam_score(
    scenario: ExamSimulationScenario,
    *,
    inputs: ExamSimulationInputs,
) -> Decimal:
    if scenario == ExamSimulationScenario.CURRENT_STATE:
        return inputs.current_predicted_score
    if scenario == ExamSimulationScenario.COMPLETE_RECOMMENDATIONS:
        return _clamp_score(inputs.current_predicted_score + inputs.total_estimated_gain)
    penalty = compute_retention_decay_penalty(inputs.retention_subscore)
    return _clamp_score(inputs.current_predicted_score - penalty)


def compute_exam_simulations_v1(inputs: ExamSimulationInputs) -> ExamSimulationResult:
    return ExamSimulationResult(
        current_state=simulate_exam_score(ExamSimulationScenario.CURRENT_STATE, inputs=inputs),
        complete_recommendations=simulate_exam_score(
            ExamSimulationScenario.COMPLETE_RECOMMENDATIONS,
            inputs=inputs,
        ),
        no_study=simulate_exam_score(ExamSimulationScenario.NO_STUDY, inputs=inputs),
    )
