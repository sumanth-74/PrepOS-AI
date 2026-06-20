from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class KnowledgeQueryEvaluationModel(Base):
    __tablename__ = "knowledge_query_evaluations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    source_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    retrieved_chunk_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    relevant_chunk_ids: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    recall_at_5: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    recall_at_8: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    precision_at_5: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    precision_at_8: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    mrr: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    ndcg: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class KnowledgeAnswerEvaluationModel(Base):
    __tablename__ = "knowledge_answer_evaluations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    query: Mapped[str] = mapped_column(Text, nullable=False)
    answer: Mapped[str] = mapped_column(Text, nullable=False)
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    citation_coverage: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    support_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    hallucination_score: Mapped[float] = mapped_column(Numeric(6, 2), nullable=False, default=0)
    confidence: Mapped[str] = mapped_column(String(16), nullable=False)
    source_types: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    query_evaluation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
