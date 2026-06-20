from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from prepos.infrastructure.db.base import Base


class AgentCritiqueModel(Base):
    __tablename__ = "agent_critiques"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    overall_score: Mapped[float] = mapped_column(Float, nullable=False)
    unsupported_claims: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    citation_issues: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    critique_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentReflectionModel(Base):
    __tablename__ = "agent_reflections"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    critique_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    original_answer: Mapped[str] = mapped_column(Text, nullable=False)
    refined_answer: Mapped[str] = mapped_column(Text, nullable=False)
    improvements_json: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentExecutionGraphNodeModel(Base):
    __tablename__ = "agent_execution_graph_nodes"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    execution_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    node_id: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_node_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    agent_type: Mapped[str] = mapped_column(String(64), nullable=False)
    tool_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    step_order: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(32), nullable=False)
    result_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class AgentLearningSignalModel(Base):
    __tablename__ = "agent_learning_signals"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    tenant_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False, index=True)
    signal_type: Mapped[str] = mapped_column(String(64), nullable=False)
    subject_key: Mapped[str] = mapped_column(String(128), nullable=False)
    concept_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    effectiveness_score: Mapped[float] = mapped_column(Float, nullable=False)
    signal_json: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
