from __future__ import annotations

from decimal import Decimal

from prepos.domain.scoring.readiness_v1 import (
    ReadinessInputs,
    compute_readiness_explanation,
    compute_readiness_v1,
)


def test_readiness_formula_all_dimensions() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=Decimal("80"),
            average_retention=Decimal("60"),
            average_confidence=Decimal("70"),
        )
    )

    assert result.unrated is False
    assert result.score == Decimal("72.00")
    assert result.mastery_subscore == Decimal("80.00")
    assert result.retention_subscore == Decimal("60.00")
    assert result.confidence_subscore == Decimal("70.00")


def test_readiness_weight_redistribution_missing_confidence() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=Decimal("80"),
            average_retention=Decimal("60"),
            average_confidence=None,
        )
    )

    assert result.unrated is False
    assert result.score == Decimal("72.50")
    assert result.confidence_subscore is None


def test_readiness_all_null_inputs() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
        )
    )

    assert result.unrated is True
    assert result.score is None
    assert result.mastery_subscore is None
    assert result.retention_subscore is None
    assert result.confidence_subscore is None


def test_readiness_mastery_only() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=Decimal("80"),
            average_retention=None,
            average_confidence=None,
        )
    )

    assert result.unrated is False
    assert result.score == Decimal("80.00")
    assert result.mastery_subscore == Decimal("80.00")
    assert result.retention_subscore is None
    assert result.confidence_subscore is None


def test_readiness_retention_only() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=None,
            average_retention=Decimal("65"),
            average_confidence=None,
        )
    )

    assert result.unrated is False
    assert result.score == Decimal("65.00")
    assert result.retention_subscore == Decimal("65.00")


def test_readiness_confidence_only() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=None,
            average_retention=None,
            average_confidence=Decimal("70"),
        )
    )

    assert result.unrated is False
    assert result.score == Decimal("70.00")
    assert result.confidence_subscore == Decimal("70.00")


def test_readiness_explanation_generation() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=Decimal("80"),
            average_retention=Decimal("60"),
            average_confidence=Decimal("70"),
        )
    )
    explanation = compute_readiness_explanation(result)

    assert explanation is not None
    assert explanation.strongest_dimension == "mastery"
    assert explanation.weakest_dimension == "retention"
    assert explanation.improvement_opportunity == "Revision completion would increase readiness fastest."


def test_readiness_explanation_unrated_returns_none() -> None:
    result = compute_readiness_v1(
        ReadinessInputs(
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
        )
    )

    assert compute_readiness_explanation(result) is None


def test_compute_readiness_from_snapshot_uses_v1_1() -> None:
    """Legacy test module keeps v1 direct tests; snapshot entry uses v1_1."""
    from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
    from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot

    snapshot = LearningGraphReadinessSnapshot(
        average_mastery=Decimal("80"),
        average_retention=Decimal("60"),
        average_confidence=Decimal("70"),
        rated_node_count=143,
        total_node_count=286,
    )

    result, drivers = compute_readiness_from_snapshot(snapshot)

    assert result.version == "readiness_v1_1"
    assert result.overall_score is not None
    assert drivers is not None
