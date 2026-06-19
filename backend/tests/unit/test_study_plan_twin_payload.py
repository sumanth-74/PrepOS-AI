from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_study_behavior_payload_section,
    build_study_plan_payload_section,
    merge_twin_payload_sections,
)


def test_build_study_plan_payload_section() -> None:
    now = datetime(2026, 6, 18, tzinfo=UTC)
    section = build_study_plan_payload_section(
        generated_at=now,
        daily_item_count=6,
        weekly_item_count=14,
        total_estimated_gain=Decimal("18.40"),
    )

    assert section["daily_items"] == 6
    assert section["weekly_items"] == 14
    assert section["total_estimated_gain"] == 18.4
    assert section["generated_at"] == now.isoformat()


def test_build_study_behavior_payload_section() -> None:
    section = build_study_behavior_payload_section(
        completion_rate=Decimal("0.82"),
        skip_rate=Decimal("0.11"),
        average_minutes_variance=Decimal("0.18"),
    )

    assert section["completion_rate"] == 0.82
    assert section["skip_rate"] == 0.11
    assert section["average_minutes_variance"] == 0.18


def test_merge_twin_payload_includes_study_behavior() -> None:
    merged = merge_twin_payload_sections(
        {},
        study_behavior=build_study_behavior_payload_section(
            completion_rate=Decimal("0.50"),
            skip_rate=Decimal("0.25"),
            average_minutes_variance=Decimal("0.10"),
        ),
    )

    behavior = merged["study_behavior"]
    assert isinstance(behavior, dict)
    assert behavior["completion_rate"] == 0.5
