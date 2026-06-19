from __future__ import annotations

from decimal import Decimal

from prepos.application.learning_graph.readiness import compute_readiness_from_snapshot
from prepos.domain.learning_graph.entities import LearningGraphReadinessSnapshot
from prepos.domain.scoring.readiness_v1_1 import (
    READINESS_V1_1,
    ReadinessInputsV1_1,
    compute_confidence_subscore,
    compute_coverage_subscore,
    compute_knowledge_subscore,
    compute_readiness_v1_1,
    compute_retention_subscore,
)


def test_knowledge_subscore_clamps_and_rounds() -> None:
    assert compute_knowledge_subscore(Decimal("80.456")) == Decimal("80.46")
    assert compute_knowledge_subscore(Decimal("120")) == Decimal("100.00")
    assert compute_knowledge_subscore(None) is None


def test_retention_subscore() -> None:
    assert compute_retention_subscore(Decimal("64.2")) == Decimal("64.20")


def test_confidence_subscore_nullable() -> None:
    assert compute_confidence_subscore(None) is None
    assert compute_confidence_subscore(Decimal("70")) == Decimal("70.00")


def test_coverage_formula() -> None:
    assert compute_coverage_subscore(rated_node_count=200, total_node_count=400) == Decimal("50.00")
    assert compute_coverage_subscore(rated_node_count=150, total_node_count=320) == Decimal("46.88")
    assert compute_coverage_subscore(rated_node_count=0, total_node_count=0) is None


def test_readiness_v1_1_all_dimensions() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=Decimal("80"),
            average_retention=Decimal("60"),
            average_confidence=Decimal("70"),
            rated_node_count=150,
            total_node_count=300,
        )
    )

    assert result.version == READINESS_V1_1
    assert result.unrated is False
    assert result.knowledge_subscore == Decimal("80.00")
    assert result.retention_subscore == Decimal("60.00")
    assert result.confidence_subscore == Decimal("70.00")
    assert result.coverage_subscore == Decimal("50.00")
    assert result.overall_score == Decimal("69.00")


def test_readiness_v1_1_weight_redistribution_missing_confidence() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=Decimal("80"),
            average_retention=Decimal("60"),
            average_confidence=None,
            rated_node_count=100,
            total_node_count=200,
        )
    )

    assert result.confidence_subscore is None
    assert result.coverage_subscore == Decimal("50.00")
    assert result.overall_score == Decimal("68.75")


def test_readiness_v1_1_all_null_inputs() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
            rated_node_count=0,
            total_node_count=0,
        )
    )

    assert result.unrated is True
    assert result.overall_score is None


def test_readiness_v1_1_coverage_only() -> None:
    result = compute_readiness_v1_1(
        ReadinessInputsV1_1(
            average_mastery=None,
            average_retention=None,
            average_confidence=None,
            rated_node_count=0,
            total_node_count=100,
        )
    )

    assert result.unrated is False
    assert result.coverage_subscore == Decimal("0.00")
    assert result.overall_score == Decimal("0.00")


def test_compute_readiness_from_snapshot_v1_1() -> None:
    snapshot = LearningGraphReadinessSnapshot(
        average_mastery=Decimal("80"),
        average_retention=Decimal("60"),
        average_confidence=Decimal("70"),
        rated_node_count=150,
        total_node_count=320,
    )

    result, drivers = compute_readiness_from_snapshot(snapshot)

    assert result.version == READINESS_V1_1
    assert result.overall_score is not None
    assert drivers is not None
    assert drivers.largest_positive_driver == "knowledge"
