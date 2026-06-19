from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_forecast_payload_section,
    build_goal_payload_section,
    merge_twin_payload_sections,
)


def test_build_goal_payload_section() -> None:
    from datetime import date

    section = build_goal_payload_section(
        target_readiness_score=Decimal("85"),
        target_date=date(2026, 9, 1),
    )
    assert section["target_readiness_score"] == 85.0
    assert section["target_date"] == "2026-09-01"


def test_build_forecast_payload_section() -> None:
    section = build_forecast_payload_section(
        current_readiness=Decimal("71.5"),
        projected_readiness=Decimal("81.2"),
        gap_to_goal=Decimal("3.8"),
        on_track=False,
        days_remaining=60,
        explanation="You are projected to reach 81.2 readiness before the exam.",
    )
    assert section["projected_readiness"] == 81.2
    assert section["on_track"] is False
    assert section["days_remaining"] == 60


def test_merge_twin_payload_includes_goal_and_forecast() -> None:
    from datetime import date

    merged = merge_twin_payload_sections(
        {},
        goal=build_goal_payload_section(
            target_readiness_score=Decimal("85"),
            target_date=date(2026, 9, 1),
        ),
        forecast=build_forecast_payload_section(
            current_readiness=Decimal("71.5"),
            projected_readiness=Decimal("81.2"),
            gap_to_goal=Decimal("3.8"),
            on_track=False,
            days_remaining=60,
        ),
    )
    assert "goal" in merged
    assert "forecast" in merged
