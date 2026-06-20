from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class CopilotSessionModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "copilot_sessions"
    __table_args__ = (
        Index("ix_copilot_sessions_tenant_user", "tenant_id", "user_id"),
        Index("ix_copilot_sessions_tenant_last_activity", "tenant_id", "last_activity_at"),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    last_activity_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class CopilotQueryModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "copilot_queries"
    __table_args__ = (
        Index("ix_copilot_queries_tenant_created", "tenant_id", "created_at"),
        Index("ix_copilot_queries_tenant_intent", "tenant_id", "intent"),
        Index("ix_copilot_queries_tenant_persona", "tenant_id", "persona"),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    session_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("copilot_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(64), nullable=False)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    response_time_ms: Mapped[int] = mapped_column(Integer, nullable=False)
    citation_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String(16), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)


class CopilotIntentMetricModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "copilot_intent_metrics"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "metric_date",
            "persona",
            "intent",
            name="uq_copilot_intent_metrics_daily",
        ),
        Index("ix_copilot_intent_metrics_tenant_date", "tenant_id", "metric_date"),
    )

    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    metric_date: Mapped[date] = mapped_column(Date, nullable=False)
    persona: Mapped[str] = mapped_column(String(32), nullable=False)
    intent: Mapped[str] = mapped_column(String(64), nullable=False)
    query_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
