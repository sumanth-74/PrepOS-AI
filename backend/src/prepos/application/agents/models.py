from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class AgentSource(BaseModel):
    label: str
    reference: str


class AgentTask(BaseModel):
    task_id: UUID
    objective: str
    requested_by: UUID
    persona: str
    priority: int = Field(default=5, ge=1, le=10)


class AgentResult(BaseModel):
    success: bool
    confidence: str
    data: dict[str, Any] = Field(default_factory=dict)
    reasoning: str = ""
    sources: list[AgentSource] = Field(default_factory=list)
    tool_name: str | None = None
    agent_type: str | None = None


class AgentPlanStep(BaseModel):
    step_order: int
    agent_type: str
    tool_names: list[str] = Field(default_factory=list)
    objective: str


class AgentExecutionPlan(BaseModel):
    plan_id: UUID
    objective: str
    persona: str
    steps: list[AgentPlanStep] = Field(default_factory=list)


class AgentExecutionRecord(BaseModel):
    execution_id: UUID
    agent_type: str
    persona: str
    objective: str
    plan: AgentExecutionPlan
    results: list[AgentResult]
    confidence: str
    execution_time_ms: int
    success: bool
    created_at: datetime


class AgentCritiqueRecord(BaseModel):
    critique_id: UUID
    execution_id: UUID
    overall_score: float
    unsupported_claims: list[str] = Field(default_factory=list)
    citation_issues: list[str] = Field(default_factory=list)
    passed: bool
    reasoning: str = ""


class AgentReflectionRecord(BaseModel):
    reflection_id: UUID
    execution_id: UUID
    critique_id: UUID
    original_answer: str
    refined_answer: str
    improvements: list[str] = Field(default_factory=list)


class AgentExecutionGraphNode(BaseModel):
    node_id: str
    parent_node_id: str | None = None
    agent_type: str
    tool_name: str | None = None
    step_order: int
    status: str
    result: AgentResult | None = None


class AgentExecutionGraph(BaseModel):
    execution_id: UUID | None = None
    nodes: list[AgentExecutionGraphNode] = Field(default_factory=list)


class AgentLearningSignal(BaseModel):
    signal_type: str
    subject_key: str
    concept_id: str | None = None
    effectiveness_score: float
    explanation: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class AgentCapability(BaseModel):
    agent_type: str
    display_name: str
    description: str
    capabilities: list[str] = Field(default_factory=list)
    supported_personas: list[str] = Field(default_factory=list)
    tool_names: list[str] = Field(default_factory=list)


class AgentHealthStatus(BaseModel):
    agent_type: str
    success_rate: float
    average_confidence_score: float
    execution_count: int
    status: str


class AutonomousAction(BaseModel):
    action_type: str
    subject_key: str
    message: str
    payload: dict[str, Any] = Field(default_factory=dict)
    source_workflow: str


class AgentOrchestratorResponse(BaseModel):
    agent_used: str
    confidence: str
    answer: str
    results: list[AgentResult]
    sources: list[AgentSource]
    plan: AgentExecutionPlan
    execution_id: UUID | None = None
    critique: AgentCritiqueRecord | None = None
    reflection: AgentReflectionRecord | None = None
    execution_graph: AgentExecutionGraph | None = None
    collaborating_agents: list[str] = Field(default_factory=list)
    trace_id: UUID | None = None


class AgentAdminDashboardResponse(BaseModel):
    total_executions: int
    executions_last_30_days: int
    success_rate: float
    average_confidence_score: float
    agent_usage: dict[str, int]
    tool_usage: dict[str, int]
    workflow_counts: dict[str, int]
    recent_executions: list[dict[str, Any]]
    critique_count: int = 0
    reflection_count: int = 0
    average_critique_score: float = 0.0
    registered_agents: list[dict[str, Any]] = Field(default_factory=list)
    agent_health: list[AgentHealthStatus] = Field(default_factory=list)


@dataclass(slots=True)
class AgentContext:
    tenant_id: UUID
    user_id: UUID
    persona: str
    question: str
    student_id: UUID | None = None
    student_user_id: UUID | None = None
    exam_id: str | None = None
    memory_context: dict[str, Any] = field(default_factory=dict)
    learning_signals: list[AgentLearningSignal] = field(default_factory=list)
    shared_state: dict[str, Any] = field(default_factory=dict)

    def to_metadata(self) -> dict[str, Any]:
        return {
            "tenant_id": str(self.tenant_id),
            "user_id": str(self.user_id),
            "persona": self.persona,
            "student_id": str(self.student_id) if self.student_id else None,
            "exam_id": self.exam_id,
        }
