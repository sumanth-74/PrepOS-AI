from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, UUIDPrimaryKeyMixin


class StudentRevisionQueueModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "student_revision_queue"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "concept_id",
            name="uq_student_revision_queue_tenant_student_concept",
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
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False)
    next_review_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    retention_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    importance_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    weakness_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    priority_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
