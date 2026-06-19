from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.application.twin.projection_ports import PersonalizationSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_personalization_projection_persists_section() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.PERSONALIZATION,
        port_attr="get_personalization_summary",
        summary=PersonalizationSummary(
            learning_style="CONSISTENT_LEARNER",
            risk_profile="MEDIUM_RISK",
            top_multiplier=Decimal("1.25"),
            best_activity_type="REVISION",
            historical_effectiveness=Decimal("71.0"),
            explanation="Revision works best.",
        ),
    )
    assert result.best_activity_type == "REVISION"
    assert result.twin_payload["personalization"]["best_activity_type"] == "REVISION"
