from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import build_behavior_profile_payload_section, merge_twin_payload_sections


def test_build_behavior_profile_payload_section() -> None:
    section = build_behavior_profile_payload_section(
        consistency_score=Decimal("82.5"),
        discipline_score=Decimal("91.0"),
        revision_adherence_score=Decimal("78.2"),
        weakness_recovery_score=Decimal("84.1"),
        engagement_score=Decimal("88.3"),
        learning_style="CONSISTENT_LEARNER",
        risk_profile="LOW_RISK",
        explanation="You consistently complete planned sessions.",
    )
    assert section["version"] == "behavior_profile_v1"
    assert section["learning_style"] == "CONSISTENT_LEARNER"
    assert section["consistency_score"] == 82.5


def test_merge_twin_payload_includes_behavior_profile() -> None:
    merged = merge_twin_payload_sections(
        {},
        behavior_profile=build_behavior_profile_payload_section(
            consistency_score=Decimal("82.5"),
            discipline_score=Decimal("91.0"),
            revision_adherence_score=Decimal("78.2"),
            weakness_recovery_score=Decimal("84.1"),
            engagement_score=Decimal("88.3"),
            learning_style="CONSISTENT_LEARNER",
            risk_profile="LOW_RISK",
        ),
    )
    assert merged["behavior_profile"]["risk_profile"] == "LOW_RISK"
