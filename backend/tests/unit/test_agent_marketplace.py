from __future__ import annotations

from prepos.application.agents.agent_marketplace import AgentMarketplace, CAPABILITY_CATALOG
from prepos.application.agents.registry import ToolRegistry


def test_marketplace_lists_registered_agents() -> None:
    marketplace = AgentMarketplace(tool_registry=ToolRegistry({}))
    capabilities = marketplace.list_capabilities()
    assert len(capabilities) == len(CAPABILITY_CATALOG)
    agent_types = {item.agent_type for item in capabilities}
    assert "faculty_teaching_agent" in agent_types
    assert "knowledge_agent" in agent_types


def test_marketplace_selects_faculty_agent_for_teaching_plan() -> None:
    marketplace = AgentMarketplace(tool_registry=ToolRegistry({}))
    selected = marketplace.select_for_objective(
        objective="Build weekly teaching plan for GS batch",
        persona="mentor",
    )
    assert selected == "faculty_teaching_agent"
