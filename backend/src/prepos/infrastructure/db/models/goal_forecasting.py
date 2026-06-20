from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class GoalForecastModel(Base):
    __tablename__ = "goal_forecasts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    goal_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False)
    forecast_date: Mapped[date] = mapped_column(Date, nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    current_readiness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    projected_readiness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    target_readiness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    probability_of_success: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    forecast_status: Mapped[str] = mapped_column(String(32), nullable=False)
    top_drivers_json: Mapped[list[str]] = mapped_column(JSONB, nullable=False, default=list)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastScenarioModel(Base):
    __tablename__ = "forecast_scenarios"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    forecast_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("goal_forecasts.id", ondelete="CASCADE"),
        nullable=False,
    )
    scenario_type: Mapped[str] = mapped_column(String(64), nullable=False)
    scenario_name: Mapped[str] = mapped_column(String(128), nullable=False)
    weekly_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    projected_readiness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    projected_score: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    probability_of_success: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ForecastEventModel(Base):
    __tablename__ = "forecast_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    student_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    forecast_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    scenario_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
