from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class PyqQuestionModel(Base):
    __tablename__ = "pyq_questions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_stage: Mapped[str] = mapped_column(String(32), nullable=False)
    paper: Mapped[str] = mapped_column(String(64), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_reference: Mapped[str | None] = mapped_column(String(256), nullable=True)
    difficulty: Mapped[int | None] = mapped_column(Integer, nullable=True)
    importance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    knowledge_source_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="SET NULL"),
        nullable=True,
    )
    knowledge_chunk_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_chunks.id", ondelete="SET NULL"),
        nullable=True,
    )
    metadata_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PyqMappingModel(Base):
    __tablename__ = "pyq_mappings"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    pyq_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("pyq_questions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    concept_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=1.0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class PyqStatisticModel(Base):
    __tablename__ = "pyq_statistics"

    exam_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    concept_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    pyq_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    first_appearance_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_appearance_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frequency_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    trend_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
