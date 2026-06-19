from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.intervention_outcome_types_v1 import InterventionOutcomeStatus
from prepos.domain.twin.intervention_outcome_v1 import (
    InterventionOutcomeInputs,
    classify_outcome_status,
    compute_effectiveness_score_v1,
    compute_intervention_outcome_v1,
)
from prepos.domain.twin.intervention_types_v1 import TwinInterventionType


def test_effectiveness_score_formula() -> None:
    score = compute_effectiveness_score_v1(
        readiness_delta=Decimal("10"),
        predicted_score_delta=Decimal("100"),
        completion_delta=Decimal("0.5"),
    )
    assert score == Decimal("45.00")


def test_classify_highly_effective() -> None:
    assert classify_outcome_status(Decimal("80")) == InterventionOutcomeStatus.HIGHLY_EFFECTIVE


def test_classify_effective() -> None:
    assert classify_outcome_status(Decimal("55")) == InterventionOutcomeStatus.EFFECTIVE


def test_classify_partially_effective() -> None:
    assert classify_outcome_status(Decimal("30")) == InterventionOutcomeStatus.PARTIALLY_EFFECTIVE


def test_classify_ineffective() -> None:
    assert classify_outcome_status(Decimal("10")) == InterventionOutcomeStatus.INEFFECTIVE


def test_compute_intervention_outcome_deltas() -> None:
    outcome = compute_intervention_outcome_v1(
        InterventionOutcomeInputs(
            intervention_type=TwinInterventionType.REVISION_SPRINT,
            readiness_before=Decimal("65"),
            readiness_after=Decimal("71.2"),
            predicted_score_before=Decimal("430"),
            predicted_score_after=Decimal("450"),
            completion_rate_before=Decimal("0.70"),
            completion_rate_after=Decimal("0.80"),
        )
    )
    assert outcome.readiness_delta == Decimal("6.20")
    assert outcome.predicted_score_delta == Decimal("20.00")
    assert outcome.completion_delta == Decimal("0.10")
    assert outcome.effectiveness_score == Decimal("11.10")
    assert outcome.outcome_status == InterventionOutcomeStatus.INEFFECTIVE
