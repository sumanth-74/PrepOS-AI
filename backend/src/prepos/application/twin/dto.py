from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TwinRecommendationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    recommendation_type: str
    recommendation_score: Decimal
    importance_score: Decimal
    weakness_score: Decimal
    retention_score: Decimal | None = None
    readiness_gain: Decimal
    explanation: str
