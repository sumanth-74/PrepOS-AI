from __future__ import annotations

from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentPreparationGoalModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_preparation_goals"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            name="uq_student_preparation_goals_tenant_student_exam",
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
    target_readiness_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    target_date: Mapped[date] = mapped_column(Date, nullable=False)
    daily_capacity_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=120)
