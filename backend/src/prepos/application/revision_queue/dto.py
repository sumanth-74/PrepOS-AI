from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RevisionQueueItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    concept_id: str
    status: str
    priority_score: Decimal
    next_review_at: datetime
    retention_score: Decimal | None = None
    weakness_score: Decimal | None = None
    importance_score: Decimal
