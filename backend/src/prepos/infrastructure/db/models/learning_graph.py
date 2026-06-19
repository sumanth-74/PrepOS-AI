from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentConceptProgressModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_concept_progress"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "concept_id",
            name="uq_student_concept_progress_tenant_student_concept",
        ),
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
    catalog_version: Mapped[str] = mapped_column(String(32), nullable=False)
    concept_id: Mapped[str] = mapped_column(
        String(192),
        ForeignKey("concepts.concept_id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[str] = mapped_column(String(128), nullable=False)
    topic_id: Mapped[str] = mapped_column(String(192), nullable=False)
    mastery_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    mastery_nonmcq_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    retention_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, default=None)
    retention_stability_s: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True, default=None)
    retention_last_event_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_last_review_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    retention_last_grade: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, default=None)
    importance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("50"))
    overconfidence_flag: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    mcq_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mcq_correct_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    nonmcq_attempt_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    study_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    mastery_version: Mapped[str] = mapped_column(String(32), nullable=False, default="mastery_v1")
    mastery_nonmcq_version: Mapped[str] = mapped_column(String(32), nullable=False, default="masterynonmcq_v1")
    retention_version: Mapped[str] = mapped_column(String(32), nullable=False, default="retention_v1")
    confidence_version: Mapped[str] = mapped_column(String(32), nullable=False, default="confidence_v1")
    importance_version: Mapped[str] = mapped_column(String(32), nullable=False, default="importance_copy_v1")
    node_state: Mapped[str] = mapped_column(String(32), nullable=False, default="unrated", index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class LearningGraphEventModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "learning_graph_events"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(192), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    event_payload: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    causation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False)
    event_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    scoring_versions: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class ScoreAuditLogModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "score_audit_log"

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    concept_id: Mapped[str] = mapped_column(String(192), nullable=False, index=True)
    score_type: Mapped[str] = mapped_column(String(64), nullable=False)
    previous_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    new_value: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    reason: Mapped[str] = mapped_column(String(255), nullable=False)
    causation_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
