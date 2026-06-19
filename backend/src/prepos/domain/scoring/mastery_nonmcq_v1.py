from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.common import clamp, redistribute_weights, round_score, shrink, weighted_blend
from prepos.domain.scoring.config import DEFAULT_SCORING_CONFIG, ScoringConfig
from prepos.domain.scoring.mastery_v1 import MasteryEvidenceCounters

MASTERY_NONMCQ_V1 = "masterynonmcq_v1"


@dataclass(frozen=True, slots=True)
class MasteryNonMcqResult:
    value: Decimal | None
    version: str
    raw_unit: Decimal | None
    shrunk_unit: Decimal | None
    n_nonmcq: int
    active_components: tuple[str, ...]
    redistributed_weights: dict[str, Decimal]


def compute_mastery_nonmcq_v1(
    evidence: MasteryEvidenceCounters,
    *,
    config: ScoringConfig = DEFAULT_SCORING_CONFIG,
) -> MasteryNonMcqResult:
    """Mastery over non-MCQ channels only (Scoring v1.1 §4.2)."""
    component_values = {
        "mains": clamp(evidence.mains_component, Decimal("0"), Decimal("1")),
        "revision": clamp(evidence.revision_component, Decimal("0"), Decimal("1")),
        "study": clamp(evidence.study_component, Decimal("0"), Decimal("1")),
    }
    component_counts = {
        "mains": evidence.n_mains,
        "revision": evidence.n_rev,
        "study": evidence.n_study,
    }
    base_weights = {
        "mains": config.MASTERY_NONMCQ_W_MAINS,
        "revision": config.MASTERY_NONMCQ_W_REVISION,
        "study": config.MASTERY_NONMCQ_W_STUDY,
    }

    redistributed = redistribute_weights(base_weights, component_counts)
    n_nonmcq = evidence.n_mains + evidence.n_rev + evidence.n_study

    if not redistributed:
        return MasteryNonMcqResult(
            value=None,
            version=MASTERY_NONMCQ_V1,
            raw_unit=None,
            shrunk_unit=None,
            n_nonmcq=0,
            active_components=(),
            redistributed_weights={},
        )

    raw_unit = weighted_blend(component_values, redistributed)
    shrunk_unit = shrink(raw_unit, n_nonmcq, config.MASTERY_K_CONF, config.MASTERY_PRIOR)
    value = round_score(Decimal("100") * shrunk_unit)

    return MasteryNonMcqResult(
        value=value,
        version=MASTERY_NONMCQ_V1,
        raw_unit=raw_unit,
        shrunk_unit=shrunk_unit,
        n_nonmcq=n_nonmcq,
        active_components=tuple(redistributed),
        redistributed_weights=redistributed,
    )
