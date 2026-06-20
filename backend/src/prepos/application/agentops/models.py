from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

FeedbackRating = Literal["helpful", "not_helpful", "partially_helpful"]
ApprovalStatus = Literal["pending", "approved", "rejected"]


class AgentTraceStepRecord(BaseModel):
    step_number: int
    agent_name: str
    tool_name: str | None = None
    input_json: dict[str, Any] = Field(default_factory=dict)
    output_json: dict[str, Any] = Field(default_factory=dict)
    latency_ms: int = 0
    status: str = "completed"


class AgentTraceArtifactRecord(BaseModel):
    artifact_type: str
    artifact_json: dict[str, Any] = Field(default_factory=dict)


class AgentTraceRecord(BaseModel):
    trace_id: UUID
    tenant_id: UUID
    execution_id: UUID
    user_id: UUID
    persona: str
    question: str
    answer: str
    confidence: str
    latency_ms: int
    created_at: datetime
    steps: list[AgentTraceStepRecord] = Field(default_factory=list)
    artifacts: list[AgentTraceArtifactRecord] = Field(default_factory=list)


class AgentTraceListResponse(BaseModel):
    items: list[AgentTraceRecord]
    total: int


class AgentEvaluationScores(BaseModel):
    evaluation_id: UUID
    trace_id: UUID
    execution_id: UUID
    retrieval_score: float
    citation_score: float
    hallucination_score: float
    support_score: float
    answer_quality_score: float
    planner_quality_score: float
    details: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class AgentEvaluationDashboardResponse(BaseModel):
    average_retrieval_score: float
    average_citation_score: float
    average_hallucination_score: float
    average_support_score: float
    average_answer_quality_score: float
    average_planner_quality_score: float
    recent_evaluations: list[AgentEvaluationScores]
    total_evaluations: int


class AgentBenchmarkRunRequest(BaseModel):
    suite_type: str = Field(default="planner")
    benchmark_name: str | None = None


class AgentBenchmarkRecord(BaseModel):
    benchmark_id: UUID
    benchmark_name: str
    suite_type: str
    status: str
    scenario_count: int
    passed_count: int
    failed_count: int
    results: list[dict[str, Any]] = Field(default_factory=list)
    created_at: datetime
    completed_at: datetime | None = None


class AgentFeedbackRequest(BaseModel):
    trace_id: UUID
    execution_id: UUID
    rating: FeedbackRating
    feedback_text: str | None = None


class AgentFeedbackAnalyticsResponse(BaseModel):
    feedback_rate: float
    satisfaction_score: float
    feedback_by_agent: dict[str, int]
    feedback_by_intent: dict[str, int]
    total_feedback: int


class AgentCostRecord(BaseModel):
    agent_type: str
    workflow_type: str | None = None
    tokens_in: int
    tokens_out: int
    estimated_cost: float
    latency_ms: int
    query_count: int = 1


class AgentCostDashboardResponse(BaseModel):
    daily_cost: float
    cost_per_query: float
    total_queries: int
    cost_by_agent: dict[str, float]
    slowest_workflows: list[dict[str, Any]]
    highest_cost_agents: list[AgentCostRecord]


class PendingActionRecord(BaseModel):
    action_id: UUID
    action_type: str
    proposed_by_agent: str
    subject_key: str
    explanation: str
    payload: dict[str, Any] = Field(default_factory=dict)
    status: ApprovalStatus
    created_at: datetime
    reviewed_at: datetime | None = None
    review_note: str | None = None


class PendingActionListResponse(BaseModel):
    items: list[PendingActionRecord]
    total: int


class ApprovalDecisionRequest(BaseModel):
    review_note: str | None = None


class ExperimentRecord(BaseModel):
    experiment_id: UUID
    name: str
    description: str
    experiment_type: str
    status: str
    created_at: datetime


class ExperimentVariantRecord(BaseModel):
    variant_id: UUID
    variant_key: str
    description: str
    traffic_pct: float
    config: dict[str, Any] = Field(default_factory=dict)


class PromptRecord(BaseModel):
    prompt_id: UUID
    prompt_key: str
    description: str
    active_version: str | None = None
    rollout_pct: float = 100.0
    benchmark_score: float | None = None


class AgentHealthDetailResponse(BaseModel):
    agent_type: str
    executions: int
    failures: int
    retries: int
    average_latency_ms: float
    average_confidence_score: float
    satisfaction_score: float
    estimated_cost: float
    status: str


class AgentHealthLeaderboardResponse(BaseModel):
    agents: list[AgentHealthDetailResponse]
    generated_at: datetime
