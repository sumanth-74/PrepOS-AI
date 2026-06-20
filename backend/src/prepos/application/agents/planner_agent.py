from __future__ import annotations

from uuid import uuid4

import structlog

from prepos.application.agents.agent_marketplace import TOOL_TO_SPECIALIST
from prepos.application.agents.models import AgentExecutionPlan, AgentLearningSignal, AgentPlanStep

logger = structlog.get_logger(__name__)

STUDENT_KEYWORDS: dict[str, tuple[str, ...]] = {
    "forecasting": ("forecast", "readiness", "probability", "prelims", "exam date", "improve"),
    "recommendation": ("recommend", "weak", "concept", "priority", "focus", "study"),
    "planning": ("plan", "schedule", "weekly", "adherence"),
    "memory": ("memory", "milestone", "progress", "history"),
    "knowledge": ("explain", "what is", "how does", "syllabus", "topic"),
    "pyq": ("pyq", "previous year", "past paper"),
    "current_affairs": ("current affairs", "news", "recent"),
    "twin": ("readiness", "twin", "score", "dashboard"),
}

MENTOR_KEYWORDS: dict[str, tuple[str, ...]] = {
    "memory": ("memory", "history", "milestone"),
    "forecasting": ("forecast", "risk", "probability", "on track"),
    "intervention": ("intervention", "coach", "mentor", "action", "student"),
    "recommendation": ("recommend", "weakness", "concept"),
    "planning": ("plan", "adherence", "schedule"),
    "pyq": ("pyq", "previous year"),
    "cohort": ("cohort", "at risk", "segment"),
    "twin": ("readiness", "dashboard", "student"),
}

ADMIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "institution": ("institution", "management", "executive", "roi", "initiative"),
    "cohort": ("cohort", "segment", "batch"),
    "forecasting": ("forecast", "projection", "trend"),
    "intervention": ("intervention", "mentor", "roi"),
}

FACULTY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "cohort": ("cohort", "class", "batch", "section"),
    "forecasting": ("forecast", "risk", "readiness"),
    "recommendation": ("recommend", "concept", "priority", "weak"),
    "pyq": ("pyq", "previous year"),
    "current_affairs": ("current affairs", "news"),
}

DEFAULT_TOOLS: dict[str, list[str]] = {
    "student": ["memory", "forecasting", "recommendation", "planning", "twin"],
    "mentor": ["memory", "forecasting", "intervention", "recommendation", "twin"],
    "admin": ["institution", "cohort", "forecasting", "intervention"],
}

COORDINATOR_BY_PERSONA: dict[str, str] = {
    "student": "student_success_agent",
    "mentor": "mentor_coach_agent",
    "admin": "institution_strategy_agent",
}


class PlannerAgent:
    """Decomposes objectives into multi-agent execution plans without business calculations."""

    def plan(
        self,
        *,
        objective: str,
        persona: str,
        learning_signals: list[AgentLearningSignal] | None = None,
        preferred_coordinator: str | None = None,
    ) -> AgentExecutionPlan:
        normalized = objective.strip().lower()
        keyword_map = {
            "student": STUDENT_KEYWORDS,
            "mentor": MENTOR_KEYWORDS,
            "admin": ADMIN_KEYWORDS,
        }.get(persona, STUDENT_KEYWORDS)

        if any(keyword in normalized for keyword in ("teaching plan", "revision campaign", "faculty", "class plan")):
            keyword_map = FACULTY_KEYWORDS
            preferred_coordinator = preferred_coordinator or "faculty_teaching_agent"

        selected_tools: list[str] = []
        for tool_name, keywords in keyword_map.items():
            if any(keyword in normalized for keyword in keywords):
                selected_tools.append(tool_name)

        selected_tools = self._apply_learning_signals(selected_tools, learning_signals or [])
        if not selected_tools:
            selected_tools = list(DEFAULT_TOOLS.get(persona, DEFAULT_TOOLS["student"]))

        coordinator = preferred_coordinator or COORDINATOR_BY_PERSONA.get(persona, "student_success_agent")
        steps = [
            AgentPlanStep(
                step_order=index + 1,
                agent_type=TOOL_TO_SPECIALIST.get(tool_name, coordinator),
                tool_names=[tool_name],
                objective=f"{TOOL_TO_SPECIALIST.get(tool_name, tool_name)} handles {tool_name}: {objective[:120]}",
            )
            for index, tool_name in enumerate(selected_tools)
        ]

        plan = AgentExecutionPlan(
            plan_id=uuid4(),
            objective=objective,
            persona=persona,
            steps=steps,
        )
        logger.info(
            "agent_plan_generated",
            persona=persona,
            step_count=len(steps),
            tools=selected_tools,
            coordinator=coordinator,
        )
        return plan

    @staticmethod
    def _apply_learning_signals(
        selected_tools: list[str],
        learning_signals: list[AgentLearningSignal],
    ) -> list[str]:
        boosted = list(selected_tools)
        for signal in learning_signals:
            if signal.signal_type in {"weak_effectiveness_concept", "high_effectiveness_concept"}:
                if "recommendation" not in boosted:
                    boosted.append("recommendation")
            if signal.signal_type == "intervention_effectiveness" and signal.effectiveness_score < 0.5:
                if "intervention" not in boosted:
                    boosted.append("intervention")
        return boosted

    def coordinator_for_persona(self, persona: str, objective: str) -> str:
        normalized = objective.lower()
        if any(keyword in normalized for keyword in ("teaching plan", "revision campaign", "faculty", "class plan")):
            return "faculty_teaching_agent"
        return COORDINATOR_BY_PERSONA.get(persona, "student_success_agent")
