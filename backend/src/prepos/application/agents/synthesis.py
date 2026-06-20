from __future__ import annotations

from prepos.application.agents.models import AgentResult, AgentSource


def synthesize_collaborative_answer(
    *,
    coordinator_agent: str,
    results: list[AgentResult],
) -> tuple[str, str, list[AgentSource]]:
    successful = [item for item in results if item.success]
    if not successful:
        return (
            "low",
            "Unable to gather sufficient evidence from collaborating agents.",
            [],
        )

    lines = [f"{coordinator_agent} coordinated {len(successful)}/{len(results)} specialist agents."]
    sources: list[AgentSource] = []
    for result in successful:
        if result.reasoning:
            agent_label = result.agent_type or "agent"
            lines.append(f"[{agent_label}] {result.reasoning}")
        sources.extend(result.sources)

    confidence = "high" if len(successful) >= max(1, len(results) // 2) else "medium"
    return confidence, "\n".join(lines), sources
