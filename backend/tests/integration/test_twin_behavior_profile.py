from __future__ import annotations

from decimal import Decimal

import pytest

from prepos.application.twin.projection_ports import BehaviorProfileSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_behavior_profile_projection_persists_section() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.BEHAVIOR_PROFILE,
        port_attr="get_behavior_profile_summary",
        summary=BehaviorProfileSummary(
            consistency_score=Decimal("68.5"),
            discipline_score=Decimal("72.0"),
            revision_adherence_score=Decimal("70.0"),
            weakness_recovery_score=Decimal("66.0"),
            engagement_score=Decimal("65.0"),
            learning_style="CONSISTENT_LEARNER",
            risk_profile="MEDIUM_RISK",
            explanation="Consistent study pattern.",
        ),
    )
    assert result.learning_style == "CONSISTENT_LEARNER"
    assert result.twin_payload["behavior_profile"]["learning_style"] == "CONSISTENT_LEARNER"
