from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.application.twin.projection_ports import InterventionOutcomeSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_intervention_outcome_projection_persists_sections() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.INTERVENTION_OUTCOME,
        port_attr="get_intervention_outcome_summary",
        summary=InterventionOutcomeSummary(
            last_effectiveness_score=Decimal("74.0"),
            outcome_status="IMPROVING",
            explanation="Recent interventions are working.",
            best_intervention="REVISION_SPRINT",
            historical_effectiveness=Decimal("71.0"),
            optimized_intervention_score=Decimal("76.5"),
            readiness_delta=Decimal("2.5"),
        ),
    )
    assert result.twin_payload["intervention_effectiveness"]["last_effectiveness_score"] == 74.0
    assert result.twin_payload["optimization"]["best_intervention"] == "REVISION_SPRINT"
