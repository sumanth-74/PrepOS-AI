from __future__ import annotations

from prepos.application.agents.tools.base_tool import BaseTool
from prepos.application.agents.tools.cohort_tool import CohortTool
from prepos.application.agents.tools.current_affairs_tool import CurrentAffairsTool
from prepos.application.agents.tools.forecasting_tool import ForecastingTool
from prepos.application.agents.tools.institution_tool import InstitutionTool
from prepos.application.agents.tools.intervention_tool import InterventionTool
from prepos.application.agents.tools.knowledge_tool import KnowledgeTool
from prepos.application.agents.tools.memory_tool import MemoryTool
from prepos.application.agents.tools.planning_tool import PlanningTool
from prepos.application.agents.tools.pyq_tool import PyqTool
from prepos.application.agents.tools.recommendation_tool import RecommendationTool
from prepos.application.agents.tools.twin_tool import TwinTool
from prepos.application.cohort.cohort_service import CohortIntelligenceService
from prepos.application.forecasting.forecast_service import GoalForecastingService
from prepos.application.institution.institution_service import InstitutionIntelligenceService
from prepos.application.institution_outcomes.outcome_service import InstitutionOutcomeService
from prepos.application.interventions.intervention_service import MentorInterventionService
from prepos.application.knowledge.current_affairs_service import CurrentAffairsService
from prepos.application.knowledge.knowledge_agent_service import KnowledgeAgentService
from prepos.application.memory.memory_service import CoachingMemoryService
from prepos.application.planning.planning_service import AdaptivePlanningService
from prepos.application.pyq.pyq_service import PyqService
from prepos.application.recommendations.recommendation_service import LearningRecommendationService
from prepos.application.twin.twin_read_service import TwinReadService


class ToolRegistry:
    def __init__(self, tools: dict[str, BaseTool]) -> None:
        self._tools = tools

    def get(self, name: str) -> BaseTool | None:
        return self._tools.get(name)

    def names(self) -> list[str]:
        return list(self._tools.keys())


def build_tool_registry(
    *,
    recommendation_service: LearningRecommendationService,
    planning_service: AdaptivePlanningService,
    forecasting_service: GoalForecastingService,
    knowledge_service: KnowledgeAgentService,
    memory_service: CoachingMemoryService,
    pyq_service: PyqService,
    current_affairs_service: CurrentAffairsService,
    intervention_service: MentorInterventionService,
    cohort_service: CohortIntelligenceService,
    institution_service: InstitutionIntelligenceService,
    institution_outcome_service: InstitutionOutcomeService,
    twin_read_service: TwinReadService,
) -> ToolRegistry:
    tools: dict[str, BaseTool] = {
        "recommendation": RecommendationTool(service=recommendation_service),
        "planning": PlanningTool(service=planning_service),
        "forecasting": ForecastingTool(service=forecasting_service),
        "memory": MemoryTool(service=memory_service),
        "knowledge": KnowledgeTool(service=knowledge_service),
        "pyq": PyqTool(service=pyq_service),
        "current_affairs": CurrentAffairsTool(service=current_affairs_service),
        "intervention": InterventionTool(service=intervention_service),
        "cohort": CohortTool(service=cohort_service),
        "institution": InstitutionTool(
            intelligence_service=institution_service,
            outcome_service=institution_outcome_service,
        ),
        "twin": TwinTool(service=twin_read_service),
    }
    return ToolRegistry(tools)
