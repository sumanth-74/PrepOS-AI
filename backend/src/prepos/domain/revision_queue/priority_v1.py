from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.common import clamp, round_score

PRIORITY_V1 = "priority_v1"

_W_IMPORTANCE = Decimal("0.40")
_W_WEAKNESS = Decimal("0.35")
_W_RETENTION_RISK = Decimal("0.25")


def compute_retention_risk(retention_score: Decimal | None) -> Decimal:
    if retention_score is None:
        return Decimal("100")
    return clamp(Decimal("100") - retention_score, Decimal("0"), Decimal("100"))


def compute_priority_v1(
    *,
    importance_score: Decimal,
    weakness_score: Decimal | None,
    retention_score: Decimal | None,
) -> Decimal:
    weakness = weakness_score if weakness_score is not None else Decimal("0")
    retention_risk = compute_retention_risk(retention_score)
    raw = (
        _W_IMPORTANCE * importance_score
        + _W_WEAKNESS * weakness
        + _W_RETENTION_RISK * retention_risk
    )
    return round_score(clamp(raw, Decimal("0"), Decimal("100")))
