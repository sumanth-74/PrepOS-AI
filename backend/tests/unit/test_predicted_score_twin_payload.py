from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_predicted_outcome_payload_section,
    build_simulations_payload_section,
    merge_twin_payload_sections,
)


def test_build_predicted_outcome_payload_section() -> None:
    section = build_predicted_outcome_payload_section(
        expected_score=Decimal("74.50"),
        low_score=Decimal("68.20"),
        high_score=Decimal("80.80"),
        risk_level="MEDIUM",
        explanation="Current readiness suggests a likely score around 74.5.",
    )
    assert section["version"] == "predicted_score_v1"
    assert section["expected_score"] == 74.5
    assert section["low_score"] == 68.2
    assert section["high_score"] == 80.8
    assert section["risk_level"] == "MEDIUM"
    assert section["explanation"] == "Current readiness suggests a likely score around 74.5."


def test_build_simulations_payload_section() -> None:
    section = build_simulations_payload_section(
        current_state=Decimal("74.50"),
        complete_recommendations=Decimal("82.00"),
        no_study=Decimal("66.00"),
    )
    assert section == {
        "current_state": 74.5,
        "complete_recommendations": 82.0,
        "no_study": 66.0,
    }


def test_merge_twin_payload_includes_predicted_outcome_and_simulations() -> None:
    merged = merge_twin_payload_sections(
        {},
        predicted_outcome=build_predicted_outcome_payload_section(
            expected_score=Decimal("74.50"),
            low_score=Decimal("68.20"),
            high_score=Decimal("80.80"),
            risk_level="MEDIUM",
        ),
        simulations=build_simulations_payload_section(
            current_state=Decimal("74.50"),
            complete_recommendations=Decimal("82.00"),
            no_study=Decimal("66.00"),
        ),
    )
    assert merged["predicted_outcome"]["expected_score"] == 74.5
    assert merged["simulations"]["no_study"] == 66.0
