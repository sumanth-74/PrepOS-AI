from __future__ import annotations

from datetime import date
from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_milestone_status_payload_section,
    build_milestones_payload_section,
    build_trajectory_payload_section,
    merge_twin_payload_sections,
)


def test_build_trajectory_payload_section() -> None:
    section = build_trajectory_payload_section(
        required_gain=Decimal("14.50"),
        expected_daily_progress=Decimal("0.24"),
        expected_weekly_progress=Decimal("1.68"),
    )
    assert section == {
        "required_gain": 14.5,
        "expected_daily_progress": 0.24,
        "expected_weekly_progress": 1.68,
    }


def test_build_milestones_payload_section() -> None:
    section = build_milestones_payload_section(
        [
            {
                "target_date": "2026-07-01",
                "target_readiness": 74.0,
                "expected_score": 70.0,
            }
        ]
    )
    assert section[0]["target_readiness"] == 74.0
    assert section[0]["expected_score"] == 70.0


def test_merge_twin_payload_includes_milestone_sections() -> None:
    merged = merge_twin_payload_sections(
        {},
        trajectory=build_trajectory_payload_section(
            required_gain=Decimal("14.50"),
            expected_daily_progress=Decimal("0.24"),
            expected_weekly_progress=Decimal("1.68"),
        ),
        milestones=build_milestones_payload_section(
            [
                {
                    "target_date": date(2026, 7, 1).isoformat(),
                    "target_readiness": 74.0,
                    "expected_score": 70.0,
                }
            ]
        ),
        milestone_status=build_milestone_status_payload_section(
            status="BEHIND",
            current_gap=Decimal("3.50"),
            explanation="You are 3.5 readiness points behind the current milestone.",
        ),
    )
    assert merged["trajectory"]["expected_weekly_progress"] == 1.68
    assert merged["milestones"][0]["target_readiness"] == 74.0
    assert merged["milestone_status"]["status"] == "BEHIND"
