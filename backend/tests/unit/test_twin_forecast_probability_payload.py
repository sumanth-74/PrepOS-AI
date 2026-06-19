from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_forecast_probability_payload_section,
    build_forecast_scenarios_payload_section,
    build_score_distribution_payload_section,
    merge_twin_payload_sections,
)


def test_build_forecast_probability_payload_section() -> None:
    section = build_forecast_probability_payload_section(
        goal_probability=Decimal("72.50"),
        goal_likelihood="LIKELY",
        explanation="You currently have a 72.5% likelihood of reaching your goal.",
    )
    assert section["version"] == "forecast_probability_v1"
    assert section["goal_probability"] == 72.5
    assert section["goal_likelihood"] == "LIKELY"


def test_build_forecast_scenarios_payload_section() -> None:
    section = build_forecast_scenarios_payload_section(
        best_case=Decimal("86.0"),
        expected=Decimal("81.2"),
        worst_case=Decimal("72.4"),
    )
    assert section == {
        "best_case": 86.0,
        "expected": 81.2,
        "worst_case": 72.4,
    }


def test_build_score_distribution_payload_section() -> None:
    section = build_score_distribution_payload_section(
        optimistic_score=Decimal("83.5"),
        expected_score=Decimal("76.0"),
        pessimistic_score=Decimal("68.5"),
    )
    assert section["optimistic_score"] == 83.5
    assert section["pessimistic_score"] == 68.5


def test_merge_twin_payload_includes_probability_sections() -> None:
    merged = merge_twin_payload_sections(
        {},
        forecast_probability=build_forecast_probability_payload_section(
            goal_probability=Decimal("72.5"),
            goal_likelihood="LIKELY",
        ),
        forecast_scenarios=build_forecast_scenarios_payload_section(
            best_case=Decimal("86.0"),
            expected=Decimal("81.2"),
            worst_case=Decimal("72.4"),
        ),
        score_distribution=build_score_distribution_payload_section(
            optimistic_score=Decimal("83.5"),
            expected_score=Decimal("76.0"),
            pessimistic_score=Decimal("68.5"),
        ),
    )
    assert merged["forecast_probability"]["goal_likelihood"] == "LIKELY"
    assert merged["forecast_scenarios"]["best_case"] == 86.0
    assert merged["score_distribution"]["expected_score"] == 76.0
