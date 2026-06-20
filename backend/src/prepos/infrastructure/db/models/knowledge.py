from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, TSVECTOR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from prepos.infrastructure.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin, utcnow


class KnowledgeSourceModel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "knowledge_sources"
    __table_args__ = (
        UniqueConstraint("tenant_id", "exam_id", "content_hash", name="uq_knowledge_sources_content_hash"),
    )

    tenant_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True, index=True)
    exam_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_type: Mapped[str] = mapped_column(String(64), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    external_uri: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    catalog_version: Mapped[str | None] = mapped_column(String(32), nullable=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)
    file_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    indexed_chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ingestion_failure_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    ingestion_started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ingestion_completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)
    source_authority: Mapped[str | None] = mapped_column(String(64), nullable=True)
    exam_stage: Mapped[str | None] = mapped_column(String(64), nullable=True)
    importance: Mapped[str | None] = mapped_column(String(32), nullable=True)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)

    chunks: Mapped[list[KnowledgeChunkModel]] = relationship(back_populates="source")


class KnowledgeChunkModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "knowledge_chunks"
    __table_args__ = (UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_chunks_source_index"),)

    source_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_sources.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_tsv: Mapped[str | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(content, ''))", persisted=True),
        nullable=True,
    )
    token_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    metadata_json: Mapped[dict[str, object]] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    source: Mapped[KnowledgeSourceModel] = relationship(back_populates="chunks")
    embeddings: Mapped[list[KnowledgeChunkEmbeddingModel]] = relationship(back_populates="chunk")


class KnowledgeChunkEmbeddingModel(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "knowledge_chunk_embeddings"
    __table_args__ = (
        UniqueConstraint("chunk_id", "embedding_model", name="uq_knowledge_chunk_embeddings_chunk_model"),
    )

    chunk_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("knowledge_chunks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    embedding_model: Mapped[str] = mapped_column(String(64), nullable=False)
    embedding_dims: Mapped[int] = mapped_column(Integer, nullable=False)
    embedding: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)

    chunk: Mapped[KnowledgeChunkModel] = relationship(back_populates="embeddings")
