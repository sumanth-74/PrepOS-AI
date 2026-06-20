from __future__ import annotations

from prepos.application.agents.agents.current_affairs_agent import CurrentAffairsAgent
from prepos.application.agents.agents.faculty_teaching_agent import FacultyTeachingAgent
from prepos.application.agents.agents.forecasting_agent import ForecastingAgent
from prepos.application.agents.agents.institution_strategy_agent import InstitutionStrategyAgent
from prepos.application.agents.agents.knowledge_agent_wrapper import KnowledgeAgentWrapper
from prepos.application.agents.agents.memory_agent import MemoryAgent
from prepos.application.agents.agents.mentor_coach_agent import MentorCoachAgent
from prepos.application.agents.agents.planning_agent import PlanningAgent
from prepos.application.agents.agents.pyq_agent import PyqAgent
from prepos.application.agents.agents.recommendation_agent import RecommendationAgent
from prepos.application.agents.agents.student_success_agent import StudentSuccessAgent
from prepos.application.agents.base_agent import BaseAgent
from prepos.application.agents.models import AgentCapability, AgentHealthStatus
from prepos.application.agents.registry import ToolRegistry

TOOL_TO_SPECIALIST: dict[str, str] = {
    "forecasting": "forecasting_agent",
    "recommendation": "recommendation_agent",
    "planning": "planning_agent",
    "memory": "memory_agent",
    "knowledge": "knowledge_agent",
    "pyq": "pyq_agent",
    "current_affairs": "current_affairs_agent",
    "intervention": "mentor_coach_agent",
    "cohort": "institution_strategy_agent",
    "institution": "institution_strategy_agent",
    "twin": "student_success_agent",
}

CAPABILITY_CATALOG: tuple[AgentCapability, ...] = (
    AgentCapability(
        agent_type="student_success_agent",
        display_name="Student Success Agent",
        description="Maximizes student readiness through multi-tool coaching.",
        capabilities=["readiness_coaching", "study_strategy", "goal_planning"],
        supported_personas=["student"],
        tool_names=["memory", "forecasting", "recommendation", "planning", "twin", "pyq", "current_affairs"],
    ),
    AgentCapability(
        agent_type="mentor_coach_agent",
        display_name="Mentor Coach Agent",
        description="Improves student outcomes with interventions and coaching guidance.",
        capabilities=["intervention_guidance", "risk_analysis", "student_summary"],
        supported_personas=["mentor"],
        tool_names=["memory", "forecasting", "intervention", "recommendation", "planning", "twin", "pyq"],
    ),
    AgentCapability(
        agent_type="institution_strategy_agent",
        display_name="Institution Strategy Agent",
        description="Executive institutional insights and ROI guidance.",
        capabilities=["institutional_risk", "mentor_effectiveness", "executive_summary"],
        supported_personas=["admin"],
        tool_names=["institution", "cohort", "forecasting", "intervention"],
    ),
    AgentCapability(
        agent_type="faculty_teaching_agent",
        display_name="Faculty Teaching Agent",
        description="Generates teaching plans, revision campaigns, and concept priorities.",
        capabilities=["weekly_teaching_plan", "revision_campaign", "risk_report", "concept_priority"],
        supported_personas=["mentor", "admin"],
        tool_names=["cohort", "forecasting", "recommendation", "pyq", "current_affairs"],
    ),
    AgentCapability(
        agent_type="forecasting_agent",
        display_name="Forecast Agent",
        description="Loads goal forecast and readiness projections.",
        capabilities=["forecasting"],
        supported_personas=["student", "mentor", "admin"],
        tool_names=["forecasting"],
    ),
    AgentCapability(
        agent_type="recommendation_agent",
        display_name="Recommendation Agent",
        description="Loads ranked learning recommendations.",
        capabilities=["recommendations"],
        supported_personas=["student", "mentor"],
        tool_names=["recommendation"],
    ),
    AgentCapability(
        agent_type="planning_agent",
        display_name="Planning Agent",
        description="Loads adaptive study plans.",
        capabilities=["planning"],
        supported_personas=["student", "mentor"],
        tool_names=["planning"],
    ),
    AgentCapability(
        agent_type="memory_agent",
        display_name="Memory Agent",
        description="Loads coaching memory and milestones.",
        capabilities=["memory"],
        supported_personas=["student", "mentor", "admin"],
        tool_names=["memory"],
    ),
    AgentCapability(
        agent_type="knowledge_agent",
        display_name="Knowledge Agent",
        description="Answers syllabus and concept questions via RAG.",
        capabilities=["knowledge_rag"],
        supported_personas=["student", "mentor"],
        tool_names=["knowledge"],
    ),
    AgentCapability(
        agent_type="pyq_agent",
        display_name="PYQ Agent",
        description="Loads previous-year question intelligence.",
        capabilities=["pyq_intelligence"],
        supported_personas=["student", "mentor", "admin"],
        tool_names=["pyq"],
    ),
    AgentCapability(
        agent_type="current_affairs_agent",
        display_name="Current Affairs Agent",
        description="Loads current affairs search results.",
        capabilities=["current_affairs"],
        supported_personas=["student", "mentor", "admin"],
        tool_names=["current_affairs"],
    ),
)


class AgentMarketplace:
    def __init__(self, *, tool_registry: ToolRegistry) -> None:
        self._registry = tool_registry
        self._agents: dict[str, BaseAgent] = {
            "student_success_agent": StudentSuccessAgent(tool_registry),
            "mentor_coach_agent": MentorCoachAgent(tool_registry),
            "institution_strategy_agent": InstitutionStrategyAgent(tool_registry),
            "faculty_teaching_agent": FacultyTeachingAgent(tool_registry),
            "forecasting_agent": ForecastingAgent(tool_registry),
            "recommendation_agent": RecommendationAgent(tool_registry),
            "planning_agent": PlanningAgent(tool_registry),
            "memory_agent": MemoryAgent(tool_registry),
            "knowledge_agent": KnowledgeAgentWrapper(tool_registry),
            "pyq_agent": PyqAgent(tool_registry),
            "current_affairs_agent": CurrentAffairsAgent(tool_registry),
        }

    def get(self, agent_type: str) -> BaseAgent | None:
        return self._agents.get(agent_type)

    def list_capabilities(self) -> list[AgentCapability]:
        return list(CAPABILITY_CATALOG)

    def select_agents_for_tools(self, *, tool_names: list[str], persona: str) -> list[str]:
        selected: list[str] = []
        for tool_name in tool_names:
            agent_type = TOOL_TO_SPECIALIST.get(tool_name, "student_success_agent")
            capability = next((item for item in CAPABILITY_CATALOG if item.agent_type == agent_type), None)
            if capability and persona not in capability.supported_personas and agent_type.endswith("_agent"):
                if persona == "admin" and agent_type == "institution_strategy_agent":
                    pass
                elif persona == "mentor" and agent_type in {"mentor_coach_agent", "faculty_teaching_agent"}:
                    pass
                elif persona == "student" and agent_type == "student_success_agent":
                    pass
                elif capability.supported_personas != ["student", "mentor", "admin"]:
                    continue
            if agent_type not in selected:
                selected.append(agent_type)
        return selected

    def select_for_objective(self, *, objective: str, persona: str) -> str | None:
        normalized = objective.lower()
        if any(keyword in normalized for keyword in ("teaching plan", "revision campaign", "faculty", "class plan")):
            if persona in {"mentor", "admin"}:
                return "faculty_teaching_agent"
        return None

    @staticmethod
    def build_health_status(metrics: dict[str, object]) -> list[AgentHealthStatus]:
        agent_usage = metrics.get("agent_usage", {})
        if not isinstance(agent_usage, dict):
            return []
        success_rate = float(metrics.get("success_rate", 0.0) or 0.0)
        avg_confidence = float(metrics.get("average_confidence_score", 0.0) or 0.0)
        statuses: list[AgentHealthStatus] = []
        for agent_type, count in agent_usage.items():
            execution_count = int(count)
            status = "healthy" if success_rate >= 0.7 and execution_count > 0 else "degraded"
            if execution_count == 0:
                status = "idle"
            statuses.append(
                AgentHealthStatus(
                    agent_type=str(agent_type),
                    success_rate=success_rate,
                    average_confidence_score=avg_confidence,
                    execution_count=execution_count,
                    status=status,
                )
            )
        return statuses
