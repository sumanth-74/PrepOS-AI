from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "students"
    __table_args__ = (UniqueConstraint("tenant_id", "user_id", name="uq_students_tenant_user"),)

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_exam_id: Mapped[str | None] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    target_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    daily_study_hours: Mapped[Decimal | None] = mapped_column(Numeric(4, 2), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    onboarding_completed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="false")
    onboarding_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class LearningGraphProvisionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "learning_graph_provisions"
    __table_args__ = (UniqueConstraint("tenant_id", "student_id", name="uq_learning_graph_provisions_tenant_student"),)

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    catalog_version: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="provisioned", index=True)
    expected_node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provisioned_node_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    provisioned_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class PreparationTwinModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "preparation_twins"
    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "exam_id", name="uq_preparation_twins_tenant_student_exam"),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="provisioned", index=True)
    academic_profile: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    behavioral_profile: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    prediction_profile: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    projection_version: Mapped[str] = mapped_column(String(64), nullable=False, default="twin_projection_v1")
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    last_rebuilt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_event_id_processed: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    readiness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    average_mastery: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    average_retention: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    average_confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    rated_node_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    due_revision_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    high_risk_concept_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    largest_positive_driver: Mapped[str | None] = mapped_column(String(64), nullable=True)
    largest_negative_driver: Mapped[str | None] = mapped_column(String(64), nullable=True)
    generated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    profile_version: Mapped[str] = mapped_column(String(32), nullable=False, default="TWIN_PROFILE_V1")
    recommendation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_recommendation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    twin_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    last_learning_graph_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    learning_graph_node_versions: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    projection_revision: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    rebuild_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    skipped_rebuild_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    incremental_update_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    lock_contention_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    decision_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    decision_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    expected_readiness_gain: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    expected_score_gain: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    intervention_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    intervention_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    intervention_urgency: Mapped[str | None] = mapped_column(String(32), nullable=True)
    learning_style: Mapped[str | None] = mapped_column(String(64), nullable=True)
    risk_profile: Mapped[str | None] = mapped_column(String(32), nullable=True)
    consistency_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    discipline_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    engagement_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    best_activity_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    top_multiplier: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    historical_effectiveness: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    mentor_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    top_mentor_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    mentor_action_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    mentor_action_priority: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    escalation_level: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active_case_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    active_case_priority: Mapped[str | None] = mapped_column(String(32), nullable=True)


class StudentInterventionHistoryModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_intervention_history"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("exams.exam_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intervention_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    effectiveness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    readiness_delta: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    predicted_score_delta: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    completion_delta: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    outcome_status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
