from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class InstitutionInitiativeModel(Base):
    __tablename__ = "institution_initiatives"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    initiative_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    affected_students: Mapped[int] = mapped_column(Integer, nullable=False)
    affected_cohorts_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    expected_outcomes_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    actual_outcomes_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    before_state_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InstitutionOutcomeModel(Base):
    __tablename__ = "institution_outcomes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    initiative_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    outcome_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(128), nullable=False)
    before_readiness: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    after_readiness: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    before_forecast: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    after_forecast: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    before_cohort_health: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    after_cohort_health: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    before_risk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    after_risk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    actual_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    expected_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    variance: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InstitutionRoiMetricModel(Base):
    __tablename__ = "institution_roi_metrics"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    initiative_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    subject_key: Mapped[str] = mapped_column(String(128), nullable=False)
    roi_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    readiness_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    forecast_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    cohort_health_gain: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    risk_reduction: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    calculation_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class InstitutionInitiativeEffectivenessModel(Base):
    __tablename__ = "institution_initiative_effectiveness"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    initiative_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    effectiveness_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    readiness_delta: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    forecast_delta: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    cohort_health_delta: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False)
    risk_reduction: Mapped[int] = mapped_column(Integer, nullable=False)
    roi_score: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    evidence_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    calculation_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
