from __future__ import annotations

from prepos.application.agents.models import AgentContext
from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.institution.institution_service import InstitutionIntelligenceService
from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService


class InstitutionTool(BaseTool):
    name = "institution"

    def __init__(
        self,
        *,
        intelligence_service: InstitutionIntelligenceService,
        outcome_service: InstitutionOutcomeService,
    ) -> None:
        self._intelligence = intelligence_service
        self._outcomes = outcome_service

    async def execute(self, *, context: AgentContext) -> AgentResult:
        dashboard = await self._intelligence.get_dashboard(tenant_id=context.tenant_id)
        roi = await self._outcomes.get_roi(tenant_id=context.tenant_id)
        return self._success(
            data={
                "dashboard": dashboard.model_dump(mode="json"),
                "roi": roi.model_dump(mode="json"),
            },
            reasoning="Institution intelligence and ROI metrics loaded.",
            label="Institution",
            reference="GET /admin/institution",
        )
