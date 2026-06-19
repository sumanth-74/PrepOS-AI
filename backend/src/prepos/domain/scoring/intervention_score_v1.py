from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

INTERVENTION_SCORE_V1 = "intervention_score_v1"

_W_DECISION = Decimal("0.50")
_W_URGENCY = Decimal("0.30")
_W_IMPACT = Decimal("0.20")

_URGENCY_SCORES: dict[str, Decimal] = {
    "CRITICAL": Decimal("100"),
    "HIGH": Decimal("75"),
    "MEDIUM": Decimal("50"),
    "LOW": Decimal("25"),
}


def urgency_to_score(urgency: str) -> Decimal:
    return _URGENCY_SCORES.get(urgency, Decimal("50"))


def compute_expected_impact_score(expected_readiness_gain: Decimal) -> Decimal:
    return round_score(clamp(expected_readiness_gain * Decimal("10"), Decimal("0"), Decimal("100")))


def compute_intervention_score_v1(
    *,
    decision_score: Decimal,
    urgency: str,
    expected_readiness_gain: Decimal,
) -> Decimal:
    urgency_score = urgency_to_score(urgency)
    impact_score = compute_expected_impact_score(expected_readiness_gain)
    raw = (
        decision_score * _W_DECISION
        + urgency_score * _W_URGENCY
        + impact_score * _W_IMPACT
    )
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))
