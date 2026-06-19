from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.application.twin.projection_ports import InterventionSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_intervention_projection_persists_intervention_section() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.INTERVENTION,
        port_attr="get_intervention_summary",
        summary=InterventionSummary(
            intervention_type="REVISION_SPRINT",
            intervention_score=Decimal("68.0"),
            urgency="HIGH",
            expected_readiness_gain=Decimal("3.5"),
            title="Revision sprint",
            description="Clear overdue revisions.",
        ),
    )
    assert result.intervention_type == "REVISION_SPRINT"
    intervention = result.twin_payload["intervention"]
    assert isinstance(intervention, dict)
    assert intervention["intervention_type"] == "REVISION_SPRINT"
