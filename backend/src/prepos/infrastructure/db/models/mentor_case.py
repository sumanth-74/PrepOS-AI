from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class MentorCaseModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "mentor_cases"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            "mentor_action_type",
            "status",
            name="uq_mentor_cases_open_action",
        ),
        Index("ix_mentor_cases_tenant_status", "tenant_id", "status"),
        Index("ix_mentor_cases_tenant_priority", "tenant_id", "mentor_action_priority"),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    student_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    priority: Mapped[str] = mapped_column(String(32), nullable=False)
    mentor_action_type: Mapped[str] = mapped_column(String(64), nullable=False)
    escalation_level: Mapped[str] = mapped_column(String(32), nullable=False)
    mentor_action_priority: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolution_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)


class MentorCaseNoteModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "mentor_case_notes"

    case_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("mentor_cases.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    mentor_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    note: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
