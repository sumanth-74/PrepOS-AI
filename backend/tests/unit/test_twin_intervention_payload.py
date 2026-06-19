from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import build_intervention_payload_section, merge_twin_payload_sections


def test_build_intervention_payload_section() -> None:
    section = build_intervention_payload_section(
        intervention_type="REVISION_SPRINT",
        intervention_score=Decimal("88.5"),
        urgency="HIGH",
        expected_readiness_gain=Decimal("4.2"),
        title="Complete 2 overdue revision sprint",
        description="Clear overdue revision items before adding new study topics to stabilize retention.",
    )
    assert section["version"] == "intervention_v1"
    assert section["intervention_type"] == "REVISION_SPRINT"
    assert section["intervention_score"] == 88.5
    assert section["urgency"] == "HIGH"
    assert section["expected_readiness_gain"] == 4.2


def test_merge_twin_payload_includes_intervention() -> None:
    merged = merge_twin_payload_sections(
        {},
        intervention=build_intervention_payload_section(
            intervention_type="REVISION_SPRINT",
            intervention_score=Decimal("88.5"),
            urgency="HIGH",
            expected_readiness_gain=Decimal("4.2"),
            title="Complete 2 overdue revision sprint",
            description="Clear overdue revision items before adding new study topics to stabilize retention.",
        ),
    )
    assert merged["intervention"]["intervention_type"] == "REVISION_SPRINT"
