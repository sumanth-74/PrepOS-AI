from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class RecommendationOutcomeModel(Base):
    __tablename__ = "recommendation_outcomes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    recommendation_event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, unique=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    student_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    readiness_before: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    readiness_after: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    forecast_before: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    forecast_after: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    weakness_before: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    weakness_after: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    study_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    predicted_gain: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    actual_gain: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    effectiveness_score: Mapped[float | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class RecommendationEffectivenessMetricModel(Base):
    __tablename__ = "recommendation_effectiveness_metrics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_date",
            "concept_id",
            name="uq_recommendation_effectiveness_metrics_tenant_date_concept",
        ),
    )

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False)
    recommendation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    average_predicted_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    average_actual_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    average_effectiveness: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
