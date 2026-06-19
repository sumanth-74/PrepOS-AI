from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal


def clamp(value: Decimal, lo: Decimal, hi: Decimal) -> Decimal:
    """Map value into [lo, hi] (spec §1.3)."""
    if value < lo:
        return lo
    if value > hi:
        return hi
    return value


def norm(value: Decimal, minimum: Decimal, maximum: Decimal) -> Decimal:
    """Linear min-max normalization to [0, 1]; returns 0 when max == min."""
    if maximum == minimum:
        return Decimal("0")
    return clamp((value - minimum) / (maximum - minimum), Decimal("0"), Decimal("1"))


def logistic(value: Decimal, midpoint: Decimal, steepness: Decimal) -> Decimal:
    """Logistic squash to [0, 1] (spec §1.3)."""
    exponent = -(steepness * (value - midpoint))
    return Decimal("1") / (Decimal("1") + exponent.exp())


def shrink(raw: Decimal, n: int, k_conf: Decimal, prior: Decimal) -> Decimal:
    """Bayesian shrinkage toward prior (spec §1.4)."""
    if n < 0:
        msg = "evidence count must be non-negative"
        raise ValueError(msg)
    n_decimal = Decimal(n)
    denominator = n_decimal + k_conf
    if denominator == 0:
        return prior
    return (n_decimal / denominator) * raw + (k_conf / denominator) * prior


def round_score(value: Decimal, *, places: int = 2) -> Decimal:
    """Round stored scores to two decimals (spec §1.3)."""
    quantize_exp = Decimal("1").scaleb(-places)
    return value.quantize(quantize_exp, rounding=ROUND_HALF_UP)


def recency_weight(age_days: Decimal, half_life_days: Decimal) -> Decimal:
    """Exponential recency decay: 0.5^(age / half_life) (spec §2.3.1)."""
    if age_days <= 0:
        return Decimal("1")
    if half_life_days <= 0:
        return Decimal("0")
    return Decimal("0.5") ** (age_days / half_life_days)


def redistribute_weights(
    weights: dict[str, Decimal],
    counts: dict[str, int],
) -> dict[str, Decimal]:
    """Renormalize weights over components with evidence (spec §2.4)."""
    active = {name: weight for name, weight in weights.items() if counts.get(name, 0) > 0}
    if not active:
        return {}
    total = sum(active.values(), start=Decimal("0"))
    if total == 0:
        return {}
    return {name: weight / total for name, weight in active.items()}


def weighted_blend(
    components: dict[str, Decimal],
    weights: dict[str, Decimal],
) -> Decimal:
    """Compute Σ w_j · c_j over present keys."""
    total = Decimal("0")
    for name, weight in weights.items():
        total += weight * components[name]
    return total
