from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import build_decision_payload_section, merge_twin_payload_sections


def test_build_decision_payload_section() -> None:
    section = build_decision_payload_section(
        decision_type="REVISE_NOW",
        decision_score=Decimal("84.5"),
        expected_readiness_gain=Decimal("3.2"),
        expected_score_gain=Decimal("2.1"),
        explanation="Completing overdue revisions is currently the fastest path to improve readiness.",
    )
    assert section["version"] == "decision_engine_v1"
    assert section["decision_type"] == "REVISE_NOW"
    assert section["decision_score"] == 84.5
    assert section["expected_readiness_gain"] == 3.2


def test_merge_twin_payload_includes_decision() -> None:
    merged = merge_twin_payload_sections(
        {},
        decision=build_decision_payload_section(
            decision_type="REVISE_NOW",
            decision_score=Decimal("84.5"),
            expected_readiness_gain=Decimal("3.2"),
            expected_score_gain=Decimal("2.1"),
            explanation="Completing overdue revisions is currently the fastest path to improve readiness.",
        ),
    )
    assert merged["decision"]["decision_type"] == "REVISE_NOW"
