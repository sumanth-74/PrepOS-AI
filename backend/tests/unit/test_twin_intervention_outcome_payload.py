from __future__ import annotations

from decimal import Decimal

from prepos.domain.twin.twin_payload_v1 import (
    build_intervention_effectiveness_payload_section,
    build_optimization_payload_section,
    merge_twin_payload_sections,
)


def test_build_intervention_effectiveness_payload_section() -> None:
    section = build_intervention_effectiveness_payload_section(
        last_effectiveness_score=Decimal("82.4"),
        outcome_status="HIGHLY_EFFECTIVE",
        explanation="Revision Sprint interventions have historically improved readiness by 6.2 points.",
    )
    assert section["version"] == "intervention_outcome_v1"
    assert section["last_effectiveness_score"] == 82.4
    assert section["outcome_status"] == "HIGHLY_EFFECTIVE"


def test_merge_twin_payload_includes_outcome_sections() -> None:
    merged = merge_twin_payload_sections(
        {},
        intervention_effectiveness=build_intervention_effectiveness_payload_section(
            last_effectiveness_score=Decimal("82.4"),
            outcome_status="HIGHLY_EFFECTIVE",
        ),
        optimization=build_optimization_payload_section(
            best_intervention="REVISION_SPRINT",
            historical_effectiveness=Decimal("78.2"),
            optimized_intervention_score=Decimal("84.0"),
        ),
    )
    assert merged["intervention_effectiveness"]["outcome_status"] == "HIGHLY_EFFECTIVE"
    assert merged["optimization"]["best_intervention"] == "REVISION_SPRINT"
