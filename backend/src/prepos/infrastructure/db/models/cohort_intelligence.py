from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class CohortSnapshotModel(Base):
    __tablename__ = "cohort_snapshots"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(128), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_readiness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    avg_forecast: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    avg_effectiveness: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    risk_count: Mapped[int] = mapped_column(Integer, nullable=False)
    segment_counts_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudentSegmentModel(Base):
    __tablename__ = "student_segments"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(128), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    segment_type: Mapped[str] = mapped_column(String(64), nullable=False)
    segment_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CohortTrendModel(Base):
    __tablename__ = "cohort_trends"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    cohort_id: Mapped[str] = mapped_column(String(128), nullable=False)
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False)
    trend_direction: Mapped[str] = mapped_column(String(16), nullable=False)
    readiness_delta: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    period: Mapped[str] = mapped_column(String(16), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class CohortEventModel(Base):
    __tablename__ = "cohort_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    cohort_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
