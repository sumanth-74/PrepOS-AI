from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.application.twin.projection_ports import DecisionSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_decision_projection_persists_decision_section() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.DECISION,
        port_attr="get_decision_summary",
        summary=DecisionSummary(
            decision_type="INCREASE_REVISION",
            decision_score=Decimal("72.5"),
            expected_readiness_gain=Decimal("4.2"),
            expected_score_gain=Decimal("1.5"),
            explanation="Increase revision cadence.",
        ),
    )
    assert result.decision_type == "INCREASE_REVISION"
    decision = result.twin_payload["decision"]
    assert isinstance(decision, dict)
    assert decision["decision_type"] == "INCREASE_REVISION"
