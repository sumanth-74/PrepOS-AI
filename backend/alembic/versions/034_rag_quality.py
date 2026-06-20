"""RAG quality evaluation tables (P7 S20)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "034_rag_quality"
down_revision = "033_pyq_analytics"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "knowledge_query_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=True),
        sa.Column("retrieved_chunk_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("relevant_chunk_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("recall_at_5", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("recall_at_8", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("precision_at_5", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("precision_at_8", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("mrr", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("ndcg", sa.Numeric(precision=6, scale=4), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_query_eval_tenant_created",
        "knowledge_query_evaluations",
        ["tenant_id", "created_at"],
    )

    op.create_table(
        "knowledge_answer_evaluations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("citation_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("citation_coverage", sa.Numeric(precision=6, scale=2), nullable=False, server_default="0"),
        sa.Column("support_score", sa.Numeric(precision=6, scale=2), nullable=False, server_default="0"),
        sa.Column("hallucination_score", sa.Numeric(precision=6, scale=2), nullable=False, server_default="0"),
        sa.Column("confidence", sa.String(length=16), nullable=False),
        sa.Column("source_types", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("query_evaluation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index(
        "ix_knowledge_answer_eval_tenant_created",
        "knowledge_answer_evaluations",
        ["tenant_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_knowledge_answer_eval_tenant_created", table_name="knowledge_answer_evaluations")
    op.drop_table("knowledge_answer_evaluations")
    op.drop_index("ix_knowledge_query_eval_tenant_created", table_name="knowledge_query_evaluations")
    op.drop_table("knowledge_query_evaluations")
