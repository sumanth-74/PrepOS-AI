from __future__ import annotations

from prepos.application.agents.agents.student_success_agent import CompositeAgent
from prepos.application.agents.models import AgentContext, AgentResult
from prepos.application.agents.registry import ToolRegistry


class FacultyTeachingAgent(CompositeAgent):
    def __init__(self, registry: ToolRegistry) -> None:
        super().__init__(
            agent_type="faculty_teaching_agent",
            default_tools=["cohort", "forecasting", "recommendation", "pyq", "current_affairs"],
            registry=registry,
        )

    async def run(
        self,
        *,
        context: AgentContext,
        objective: str,
        tool_names: list[str] | None = None,
    ) -> AgentResult:
        result = await super().run(context=context, objective=objective, tool_names=tool_names)
        if not result.success:
            return result

        tool_results = result.data.get("tool_results") or []
        weekly_plan: list[str] = []
        revision_campaign: list[str] = []
        risk_report: list[str] = []
        concept_priorities: list[str] = []

        for payload in tool_results:
            tool_name = payload.get("tool_name")
            data = payload.get("data") or {}
            if tool_name == "cohort":
                metrics = data.get("metrics") or {}
                top_risks = data.get("top_risks") or []
                if top_risks:
                    risk_report.append(f"Cohort risks: {', '.join(top_risks[:3])}.")
                if metrics.get("average_readiness") is not None:
                    weekly_plan.append(
                        f"Focus lectures on readiness lift from {metrics['average_readiness']} baseline."
                    )
            if tool_name == "recommendation":
                recommendations = data.get("recommendations") or []
                for item in recommendations[:3]:
                    name = item.get("concept_name") or item.get("concept_id")
                    concept_priorities.append(str(name))
                    revision_campaign.append(f"Revision drill: {name}")
            if tool_name == "pyq":
                coverage = data.get("coverage") or {}
                weak_topics = coverage.get("weak_topics") or []
                for topic in weak_topics[:2]:
                    revision_campaign.append(f"PYQ revision block: {topic}")
            if tool_name == "current_affairs":
                items = data.get("items") or data.get("results") or []
                if items:
                    weekly_plan.append("Include latest current affairs briefing in weekly sessions.")

        result.data["faculty_outputs"] = {
            "weekly_teaching_plan": weekly_plan or ["Maintain baseline syllabus coverage with readiness checkpoints."],
            "revision_campaign": revision_campaign or ["Run concept revision clinic for top weak areas."],
            "risk_report": risk_report or ["No elevated cohort risks detected from available data."],
            "concept_priorities": concept_priorities or ["Use recommendation engine priorities for this week."],
        }
        result.reasoning = (
            f"{self.agent_type} produced teaching plan, revision campaign, risk report, and concept priorities."
        )
        return result
