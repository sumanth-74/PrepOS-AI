from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class RecommendationEventModel(Base):
    __tablename__ = "recommendation_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    student_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    impact_score: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    estimated_gain: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    readiness_gain_after: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
