from __future__ import annotations

import pytest

from prepos.application.twin.projection_ports import MentorSummary
from prepos.domain.twin.projection_sections import TwinProjectionSection
from tests.integration.twin_projection_test_support import apply_section_update


@pytest.mark.asyncio
async def test_twin_mentor_projection_persists_section() -> None:
    result = await apply_section_update(
        section=TwinProjectionSection.MENTOR,
        port_attr="get_mentor_summary",
        summary=MentorSummary(
            mentor_status="AT_RISK",
            top_mentor_message="Student is falling behind on revisions.",
            mentor_payload={
                "version": "mentor_v1",
                "summary": {
                    "overall_status": "AT_RISK",
                    "key_message": "Student is falling behind on revisions.",
                },
            },
        ),
    )
    assert result.mentor_status == "AT_RISK"
    mentor = result.twin_payload["mentor"]
    assert isinstance(mentor, dict)
    assert mentor["summary"]["overall_status"] == "AT_RISK"
