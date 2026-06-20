from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class StudyPlanVersionModel(Base):
    __tablename__ = "study_plan_versions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date] = mapped_column(Date, nullable=False)
    readiness_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    forecast_snapshot: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudyPlanItemModel(Base):
    __tablename__ = "study_plan_items"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study_plan_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False)
    activity_type: Mapped[str] = mapped_column(String(64), nullable=False)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    estimated_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    estimated_readiness_gain: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    scheduled_date: Mapped[date] = mapped_column(Date, nullable=False)
    source_reason: Mapped[str] = mapped_column(String(512), nullable=False)
    completion_status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class StudyPlanRevisionModel(Base):
    __tablename__ = "study_plan_revisions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    plan_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("study_plan_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False)
    revision_reason: Mapped[str] = mapped_column(String(256), nullable=False)
    old_priority: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    new_priority: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PlanningEventModel(Base):
    __tablename__ = "planning_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    student_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    plan_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    item_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False)
    priority_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    estimated_gain: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
