from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TwinSnapshotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    readiness_score: Decimal | None = None
    average_mastery: Decimal | None = None
    average_retention: Decimal | None = None
    average_confidence: Decimal | None = None
    due_revision_count: int
    high_risk_concept_count: int
    largest_positive_driver: str | None = None
    largest_negative_driver: str | None = None
    generated_at: datetime | None = None
