from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class CopilotMemoryModel(Base):
    __tablename__ = "copilot_memories"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    persona: Mapped[str] = mapped_column(String(16), nullable=False)
    memory_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    memory_key: Mapped[str] = mapped_column(String(256), nullable=False)
    memory_value: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
