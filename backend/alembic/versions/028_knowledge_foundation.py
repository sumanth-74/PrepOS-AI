"""Knowledge foundation P7 S15 — pgvector, sources, chunks, embeddings."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "028_knowledge_foundation"
down_revision = "027_copilot_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    extension_exists = bind.execute(
        sa.text("SELECT 1 FROM pg_extension WHERE extname = 'vector'")
    ).scalar()
    if not extension_exists:
        try:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        except Exception as exc:
            if "permission denied" not in str(exc).lower():
                raise
            raise RuntimeError(
                "pgvector extension is missing and cannot be created by the app user. "
                "Run backend/scripts/migrate-db.sh or, as a Postgres superuser: "
                'psql -U postgres -d prepos -c "CREATE EXTENSION IF NOT EXISTS vector;"'
            ) from exc

    op.create_table(
        "knowledge_sources",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("external_uri", sa.Text(), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("catalog_version", sa.String(length=32), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("file_name", sa.String(length=512), nullable=True),
        sa.Column("mime_type", sa.String(length=128), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("indexed_chunk_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("embedding_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ingestion_failure_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("ingestion_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingestion_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_knowledge_sources_tenant_id", "knowledge_sources", ["tenant_id"])
    op.create_index("ix_knowledge_sources_exam_id", "knowledge_sources", ["exam_id"])
    op.create_index("ix_knowledge_sources_status", "knowledge_sources", ["status"])
    op.create_index(
        "ix_knowledge_sources_tenant_exam",
        "knowledge_sources",
        ["tenant_id", "exam_id"],
    )
    op.create_unique_constraint(
        "uq_knowledge_sources_content_hash",
        "knowledge_sources",
        ["tenant_id", "exam_id", "content_hash"],
    )

    op.create_table(
        "knowledge_chunks",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_tsv",
            postgresql.TSVECTOR(),
            sa.Computed("to_tsvector('english', coalesce(content, ''))", persisted=True),
            nullable=True,
        ),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["source_id"], ["knowledge_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("source_id", "chunk_index", name="uq_knowledge_chunks_source_index"),
    )
    op.create_index("ix_knowledge_chunks_source_id", "knowledge_chunks", ["source_id"])
    op.create_index(
        "ix_knowledge_chunks_source_chunk_index",
        "knowledge_chunks",
        ["source_id", "chunk_index"],
    )
    op.execute(
        "CREATE INDEX ix_knowledge_chunks_metadata ON knowledge_chunks USING GIN (metadata_json)"
    )
    op.execute("CREATE INDEX ix_knowledge_chunks_fts ON knowledge_chunks USING GIN (content_tsv)")

    op.execute(
        """
        CREATE TABLE knowledge_chunk_embeddings (
            id UUID PRIMARY KEY,
            chunk_id UUID NOT NULL REFERENCES knowledge_chunks(id) ON DELETE CASCADE,
            embedding_model VARCHAR(64) NOT NULL,
            embedding_dims INTEGER NOT NULL,
            embedding vector(1536) NOT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_knowledge_chunk_embeddings_chunk_model UNIQUE (chunk_id, embedding_model)
        )
        """
    )
    op.create_index(
        "ix_knowledge_chunk_embeddings_chunk_id",
        "knowledge_chunk_embeddings",
        ["chunk_id"],
    )
    op.execute(
        """
        CREATE INDEX ix_knowledge_chunk_embeddings_hnsw
        ON knowledge_chunk_embeddings
        USING hnsw (embedding vector_cosine_ops)
        WITH (m = 16, ef_construction = 64)
        """
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_chunk_embeddings_hnsw", table_name="knowledge_chunk_embeddings")
    op.drop_table("knowledge_chunk_embeddings")
    op.drop_index("ix_knowledge_chunks_fts", table_name="knowledge_chunks")
    op.drop_index("ix_knowledge_chunks_metadata", table_name="knowledge_chunks")
    op.drop_table("knowledge_chunks")
    op.drop_constraint("uq_knowledge_sources_content_hash", "knowledge_sources", type_="unique")
    op.drop_index("ix_knowledge_sources_tenant_exam", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_status", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_exam_id", table_name="knowledge_sources")
    op.drop_index("ix_knowledge_sources_tenant_id", table_name="knowledge_sources")
    op.drop_table("knowledge_sources")
