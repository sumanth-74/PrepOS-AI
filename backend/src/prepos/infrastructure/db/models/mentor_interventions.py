from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class MentorInterventionModel(Base):
    __tablename__ = "mentor_interventions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    mentor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False)
    intervention_type: Mapped[str] = mapped_column(String(64), nullable=False)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    predicted_gain: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InterventionEffectivenessModel(Base):
    __tablename__ = "intervention_effectiveness"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    intervention_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mentor_interventions.id", ondelete="CASCADE"),
        nullable=False,
    )
    readiness_before: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    readiness_after: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    actual_gain: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    effectiveness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    evaluated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InterventionRecommendationModel(Base):
    __tablename__ = "intervention_recommendations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False)
    intervention_type: Mapped[str] = mapped_column(String(64), nullable=False)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    recommendation_reason: Mapped[str] = mapped_column(Text, nullable=False)
    impact_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    predicted_gain: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
