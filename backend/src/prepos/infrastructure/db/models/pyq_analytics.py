from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class PyqQueryEventModel(Base):
    __tablename__ = "pyq_query_events"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    event_type: Mapped[str] = mapped_column(String(32), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    intent: Mapped[str | None] = mapped_column(String(64), nullable=True)
    citation_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    pyq_boost_applied: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    pyq_retrieval_success: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
