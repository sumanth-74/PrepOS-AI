from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig

IMPORTANCE_COPY_V1 = "importance_copy_v1"


@dataclass(frozen=True, slots=True)
class ImportanceCopyInputs:
    global_importance: Decimal
    optional_subject_match: bool = True
    non_optional_multiplier: Decimal = Decimal("0.9")


@dataclass(frozen=True, slots=True)
class ImportanceCopyResult:
    value: Decimal
    version: str
    global_importance: Decimal
    personalized: bool


def compute_importance_copy_v1(
    inputs: ImportanceCopyInputs,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> ImportanceCopyResult:
    """
    STUB: copy global importance to the student node (spec §4.10).

    Optional-subject personalization applies a bounded multiplier when the concept is outside
    the student's optional selection.
    """
    _ = config
    global_value = clamp(inputs.global_importance, Decimal("0"), Decimal("100"))

    if inputs.optional_subject_match:
        value = global_value
        personalized = False
    else:
        value = clamp(global_value * inputs.non_optional_multiplier, Decimal("0"), Decimal("100"))
        personalized = True

    return ImportanceCopyResult(
        value=round_score(value),
        version=IMPORTANCE_COPY_V1,
        global_importance=round_score(global_value),
        personalized=personalized,
    )
