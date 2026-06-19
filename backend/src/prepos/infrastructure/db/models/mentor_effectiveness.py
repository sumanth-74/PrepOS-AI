from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class MentorActionEffectivenessModel(Base):
    __tablename__ = "mentor_action_effectiveness"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    action_type: Mapped[str] = mapped_column(String(64), primary_key=True)
    effectiveness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    readiness_delta: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    predicted_score_delta: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    success_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    sample_size: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
