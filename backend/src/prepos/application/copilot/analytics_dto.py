from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CopilotPersonaUsageResponse(BaseModel):
    persona: str
    query_count: int
    unique_users: int
    share_of_queries: Decimal = Decimal("0")


class CopilotIntentDistributionItem(BaseModel):
    intent: str
    count: int
    share: Decimal = Decimal("0")


class CopilotDailyUsageItem(BaseModel):
    date: date
    query_count: int
    unique_users: int


class CopilotConfidenceDistributionItem(BaseModel):
    confidence: str
    count: int
    share: Decimal = Decimal("0")


class CopilotContentAnalyticsResponse(BaseModel):
    content_questions_today: int
    content_questions_period: int
    citation_usage_count: int
    citation_usage_rate: Decimal = Decimal("0")
    confidence_distribution: list[CopilotConfidenceDistributionItem] = Field(default_factory=list)
    content_daily_usage: list[CopilotDailyUsageItem] = Field(default_factory=list)


class CopilotMentorKnowledgeAnalyticsResponse(BaseModel):
    mentor_content_questions_today: int
    mentor_content_questions_period: int
    citation_usage_count: int
    citation_usage_rate: Decimal = Decimal("0")
    confidence_distribution: list[CopilotConfidenceDistributionItem] = Field(default_factory=list)
    mentor_content_daily_usage: list[CopilotDailyUsageItem] = Field(default_factory=list)


class CopilotPromptCountItem(BaseModel):
    query_text: str
    count: int


class CopilotAdoptionFunnelItem(BaseModel):
    stage: str
    count: int
    share: Decimal = Decimal("0")


class CopilotSuccessCriteriaResponse(BaseModel):
    active_user_adoption_target: Decimal = Decimal("40")
    active_user_adoption_actual: Decimal = Decimal("0")
    active_user_adoption_met: bool = False
    unknown_intent_rate_target: Decimal = Decimal("15")
    unknown_intent_rate_actual: Decimal = Decimal("0")
    unknown_intent_rate_met: bool = False
    queries_per_active_user_target: Decimal = Decimal("3")
    queries_per_active_user_actual: Decimal = Decimal("0")
    queries_per_active_user_met: bool = False
    content_explanation_in_top_five_met: bool = False
    content_explanation_note: str = ""


class CopilotAnalyticsResponse(BaseModel):
    period_days: int = 30
    generated_at: datetime
    dau: int
    wau: int
    total_queries: int
    unique_copilot_users: int
    total_tenant_users: int
    queries_per_user_avg: Decimal
    unknown_intent_rate: Decimal
    student_usage: CopilotPersonaUsageResponse
    mentor_usage: CopilotPersonaUsageResponse
    admin_usage: CopilotPersonaUsageResponse
    intent_distribution: list[CopilotIntentDistributionItem] = Field(default_factory=list)
    daily_usage_trend: list[CopilotDailyUsageItem] = Field(default_factory=list)
    top_prompts: list[CopilotPromptCountItem] = Field(default_factory=list)
    unknown_intents: list[CopilotPromptCountItem] = Field(default_factory=list)
    adoption_funnel: list[CopilotAdoptionFunnelItem] = Field(default_factory=list)
    success_criteria: CopilotSuccessCriteriaResponse
    content_analytics: CopilotContentAnalyticsResponse
    mentor_content_analytics: CopilotMentorKnowledgeAnalyticsResponse
