from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.exam_simulation_v1 import (
    ExamSimulationInputs,
    ExamSimulationScenario,
    compute_exam_simulations_v1,
    compute_retention_decay_penalty,
    simulate_exam_score,
)
from prepos.domain.scoring.predicted_score_explanations_v1 import explain_predicted_score_v1
from prepos.domain.scoring.predicted_score_v1 import (
    PredictedScoreInputs,
    PreparationRisk,
    classify_preparation_risk,
    compute_predicted_score_range,
    compute_predicted_score_v1,
    compute_score_uncertainty,
)


def test_predicted_score_formula_all_dimensions() -> None:
    score = compute_predicted_score_v1(
        PredictedScoreInputs(
            readiness_score=Decimal("80"),
            coverage_subscore=Decimal("50"),
            confidence_subscore=Decimal("70"),
        )
    )
    assert score == Decimal("73.00")


def test_predicted_score_redistribution_missing_confidence() -> None:
    score = compute_predicted_score_v1(
        PredictedScoreInputs(
            readiness_score=Decimal("80"),
            coverage_subscore=Decimal("50"),
            confidence_subscore=None,
        )
    )
    assert score == Decimal("73.33")


def test_predicted_score_only_readiness() -> None:
    score = compute_predicted_score_v1(
        PredictedScoreInputs(
            readiness_score=Decimal("74.5"),
            coverage_subscore=None,
            confidence_subscore=None,
        )
    )
    assert score == Decimal("74.50")


def test_predicted_score_returns_none_when_all_missing() -> None:
    assert (
        compute_predicted_score_v1(
            PredictedScoreInputs(
                readiness_score=None,
                coverage_subscore=None,
                confidence_subscore=None,
            )
        )
        is None
    )


def test_score_uncertainty_uses_minimum_and_confidence() -> None:
    assert compute_score_uncertainty(Decimal("70")) == Decimal("6.00")
    assert compute_score_uncertainty(Decimal("95")) == Decimal("5")
    assert compute_score_uncertainty(None) == Decimal("20.00")


def test_predicted_score_range_clamps() -> None:
    score_range = compute_predicted_score_range(
        predicted_score=Decimal("74.50"),
        confidence_subscore=Decimal("70"),
    )
    assert score_range.expected_score == Decimal("74.50")
    assert score_range.low_score == Decimal("68.50")
    assert score_range.high_score == Decimal("80.50")

    low_edge = compute_predicted_score_range(
        predicted_score=Decimal("3.00"),
        confidence_subscore=Decimal("50"),
    )
    assert low_edge.low_score == Decimal("0.00")
    assert low_edge.high_score == Decimal("13.00")


def test_preparation_risk_classification() -> None:
    assert classify_preparation_risk(Decimal("80")) == PreparationRisk.LOW
    assert classify_preparation_risk(Decimal("79.99")) == PreparationRisk.MEDIUM
    assert classify_preparation_risk(Decimal("60")) == PreparationRisk.MEDIUM
    assert classify_preparation_risk(Decimal("59.99")) == PreparationRisk.HIGH
    assert classify_preparation_risk(None) == PreparationRisk.HIGH


def test_retention_decay_penalty() -> None:
    assert compute_retention_decay_penalty(Decimal("55")) == Decimal("6.75")
    assert compute_retention_decay_penalty(None) == Decimal("5.00")


def test_exam_simulations() -> None:
    inputs = ExamSimulationInputs(
        current_predicted_score=Decimal("74.50"),
        total_estimated_gain=Decimal("7.50"),
        retention_subscore=Decimal("55"),
    )
    result = compute_exam_simulations_v1(inputs)
    assert result.current_state == Decimal("74.50")
    assert result.complete_recommendations == Decimal("82.00")
    assert result.no_study == Decimal("67.75")


def test_simulation_clamps_at_bounds() -> None:
    high_gain = simulate_exam_score(
        ExamSimulationScenario.COMPLETE_RECOMMENDATIONS,
        inputs=ExamSimulationInputs(
            current_predicted_score=Decimal("95"),
            total_estimated_gain=Decimal("20"),
            retention_subscore=Decimal("80"),
        ),
    )
    assert high_gain == Decimal("100.00")

    no_study = simulate_exam_score(
        ExamSimulationScenario.NO_STUDY,
        inputs=ExamSimulationInputs(
            current_predicted_score=Decimal("3"),
            total_estimated_gain=Decimal("0"),
            retention_subscore=Decimal("10"),
        ),
    )
    assert no_study == Decimal("0.00")


def test_predicted_score_explanations_are_deterministic() -> None:
    gain_text = explain_predicted_score_v1(
        expected_score=Decimal("74.50"),
        complete_recommendations_score=Decimal("82.00"),
        confidence_subscore=Decimal("70"),
    )
    assert gain_text == (
        "Completing recommended revisions could increase expected score by 7.5 points."
    )

    low_confidence = explain_predicted_score_v1(
        expected_score=Decimal("74.50"),
        complete_recommendations_score=Decimal("74.50"),
        confidence_subscore=Decimal("65"),
    )
    assert low_confidence == "Low confidence increases uncertainty in score prediction."

    baseline = explain_predicted_score_v1(
        expected_score=Decimal("74.50"),
        complete_recommendations_score=Decimal("74.50"),
        confidence_subscore=Decimal("80"),
    )
    assert baseline == "Current readiness suggests a likely score around 74.5."
