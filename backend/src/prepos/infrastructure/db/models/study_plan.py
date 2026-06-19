from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class StudentStudyPlanModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "student_study_plans"
    __table_args__ = (
        UniqueConstraint("tenant_id", "student_id", "exam_id", name="uq_student_study_plans_tenant_student_exam"),
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
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    daily_plan_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    weekly_plan_json: Mapped[list[dict[str, object]]] = mapped_column(JSONB, nullable=False, default=list)
    total_estimated_gain: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
