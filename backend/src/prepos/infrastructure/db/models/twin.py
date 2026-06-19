from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, UUIDPrimaryKeyMixin


class PreparationTwinRecommendationModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "preparation_twin_recommendations"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "student_id",
            "exam_id",
            "concept_id",
            name="uq_preparation_twin_recommendations_student_exam_concept",
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
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    recommendation_type: Mapped[str] = mapped_column(String(64), nullable=False)
    recommendation_score: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    readiness_gain: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False, default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
