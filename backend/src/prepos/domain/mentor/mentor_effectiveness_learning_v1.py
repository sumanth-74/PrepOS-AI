from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.mentor.case_management_v1 import is_successful_resolution
from prepos.domain.mentor.mentor_types_v1 import CaseResolutionReason, MentorActionType
from prepos.domain.scoring.common import clamp, round_score

MENTOR_EFFECTIVENESS_LEARNING_V1 = "mentor_effectiveness_learning_v1"

_SCORE_MAX = Decimal("100")
_DELTA_NORMALIZATION_CAP = Decimal("20")


@dataclass(frozen=True, slots=True)
class ActionEffectivenessSample:
    action_type: MentorActionType
    resolution_reason: CaseResolutionReason | None
    readiness_delta: Decimal
    predicted_score_delta: Decimal


@dataclass(frozen=True, slots=True)
class MentorActionEffectiveness:
    action_type: MentorActionType
    effectiveness_score: Decimal
    readiness_delta: Decimal
    predicted_score_delta: Decimal
    success_rate: Decimal
    sample_size: int


@dataclass(frozen=True, slots=True)
class MentorEffectivenessLearningResult:
    action_effectiveness: tuple[MentorActionEffectiveness, ...]
    best_action: MentorActionType | None
    best_action_effectiveness: Decimal
    average_action_effectiveness: Decimal


def _normalize_delta(delta: Decimal) -> Decimal:
    if delta <= Decimal("0"):
        return Decimal("0")
    return clamp(delta / _DELTA_NORMALIZATION_CAP * _SCORE_MAX, Decimal("0"), _SCORE_MAX)


def _success_rate(*, successful: int, sample_size: int) -> Decimal:
    if sample_size <= 0:
        return Decimal("0")
    return clamp(
        Decimal(successful) / Decimal(sample_size) * _SCORE_MAX,
        Decimal("0"),
        _SCORE_MAX,
    )


def compute_action_effectiveness_v1(
    *,
    action_type: MentorActionType,
    samples: tuple[ActionEffectivenessSample, ...],
) -> MentorActionEffectiveness | None:
    action_samples = tuple(sample for sample in samples if sample.action_type == action_type)
    if not action_samples:
        return None

    successful = sum(
        1
        for sample in action_samples
        if sample.resolution_reason is not None
        and is_successful_resolution(reason=sample.resolution_reason)
    )
    sample_size = len(action_samples)
    avg_readiness = sum(sample.readiness_delta for sample in action_samples) / Decimal(sample_size)
    avg_predicted = sum(sample.predicted_score_delta for sample in action_samples) / Decimal(
        sample_size
    )
    success_rate = _success_rate(successful=successful, sample_size=sample_size)
    readiness_normalized = _normalize_delta(avg_readiness)
    predicted_normalized = _normalize_delta(avg_predicted)
    raw_score = (
        success_rate * Decimal("0.40")
        + readiness_normalized * Decimal("0.30")
        + predicted_normalized * Decimal("0.30")
    )
    return MentorActionEffectiveness(
        action_type=action_type,
        effectiveness_score=round_score(clamp(raw_score, Decimal("0"), _SCORE_MAX)),
        readiness_delta=round_score(avg_readiness),
        predicted_score_delta=round_score(avg_predicted),
        success_rate=round_score(success_rate),
        sample_size=sample_size,
    )


def rank_action_effectiveness_v1(
    action_effectiveness: tuple[MentorActionEffectiveness, ...],
) -> tuple[MentorActionEffectiveness, ...]:
    return tuple(
        sorted(
            action_effectiveness,
            key=lambda item: (
                -item.effectiveness_score,
                -item.sample_size,
                item.action_type.value,
            ),
        )
    )


def compute_mentor_effectiveness_learning_v1(
    samples: tuple[ActionEffectivenessSample, ...],
) -> MentorEffectivenessLearningResult:
    action_types = {sample.action_type for sample in samples}
    effectiveness = tuple(
        computed
        for action_type in action_types
        if (computed := compute_action_effectiveness_v1(action_type=action_type, samples=samples))
        is not None
    )
    ranked = rank_action_effectiveness_v1(effectiveness)
    if not ranked:
        return MentorEffectivenessLearningResult(
            action_effectiveness=(),
            best_action=None,
            best_action_effectiveness=Decimal("0"),
            average_action_effectiveness=Decimal("0"),
        )

    total_weight = sum(item.sample_size for item in ranked)
    weighted_average = (
        sum(item.effectiveness_score * Decimal(item.sample_size) for item in ranked)
        / Decimal(total_weight)
        if total_weight > 0
        else Decimal("0")
    )
    best = ranked[0]
    return MentorEffectivenessLearningResult(
        action_effectiveness=ranked,
        best_action=best.action_type,
        best_action_effectiveness=best.effectiveness_score,
        average_action_effectiveness=round_score(weighted_average),
    )


def apply_optimized_priority_v1(
    *,
    base_priority: Decimal,
    effectiveness_score: Decimal,
) -> Decimal:
    multiplier = Decimal("1") + effectiveness_score / _SCORE_MAX
    return round_score(clamp(base_priority * multiplier, Decimal("0"), _SCORE_MAX))
