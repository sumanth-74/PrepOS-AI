"""Learning graph tables: student_concept_progress, learning_graph_events, score_audit_log."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "004_learning_graph"
down_revision = "003_student_onboarding"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "student_concept_progress",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("catalog_version", sa.String(length=32), nullable=False),
        sa.Column("concept_id", sa.String(length=192), nullable=False),
        sa.Column("subject_id", sa.String(length=128), nullable=False),
        sa.Column("topic_id", sa.String(length=192), nullable=False),
        sa.Column("mastery_score", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
        sa.Column("mastery_nonmcq_score", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
        sa.Column("retention_score", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
        sa.Column("confidence_score", sa.Numeric(precision=5, scale=2), server_default="0", nullable=False),
        sa.Column("importance_score", sa.Numeric(precision=5, scale=2), server_default="50", nullable=False),
        sa.Column("overconfidence_flag", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("mcq_attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("mcq_correct_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("nonmcq_attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revision_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("study_minutes", sa.Integer(), server_default="0", nullable=False),
        sa.Column("status", sa.String(length=32), server_default="unstarted", nullable=False),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_activity_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["concept_id"], ["concepts.concept_id"], name=op.f("fk_student_concept_progress_concept_id_concepts"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_student_concept_progress_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_student_concept_progress_student_id_students"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_student_concept_progress")),
        sa.UniqueConstraint("tenant_id", "student_id", "concept_id", name="uq_student_concept_progress_tenant_student_concept"),
    )
    op.create_index(op.f("ix_student_concept_progress_tenant_id"), "student_concept_progress", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_student_concept_progress_student_id"), "student_concept_progress", ["student_id"], unique=False)
    op.create_index(op.f("ix_student_concept_progress_exam_id"), "student_concept_progress", ["exam_id"], unique=False)
    op.create_index(op.f("ix_student_concept_progress_concept_id"), "student_concept_progress", ["concept_id"], unique=False)
    op.create_index(op.f("ix_student_concept_progress_status"), "student_concept_progress", ["status"], unique=False)
    op.create_index(
        "ix_student_concept_progress_tenant_student",
        "student_concept_progress",
        ["tenant_id", "student_id"],
        unique=False,
    )

    op.create_table(
        "learning_graph_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", sa.String(length=192), nullable=False),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("event_payload", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("causation_id", sa.String(length=128), nullable=True),
        sa.Column("correlation_id", sa.String(length=128), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_graph_events")),
    )
    op.create_index(op.f("ix_learning_graph_events_tenant_id"), "learning_graph_events", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_events_student_id"), "learning_graph_events", ["student_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_events_concept_id"), "learning_graph_events", ["concept_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_events_event_type"), "learning_graph_events", ["event_type"], unique=False)

    op.create_table(
        "score_audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("concept_id", sa.String(length=192), nullable=False),
        sa.Column("score_type", sa.String(length=64), nullable=False),
        sa.Column("previous_value", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("new_value", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("causation_id", sa.String(length=128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_score_audit_log")),
    )
    op.create_index(op.f("ix_score_audit_log_tenant_id"), "score_audit_log", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_score_audit_log_student_id"), "score_audit_log", ["student_id"], unique=False)
    op.create_index(op.f("ix_score_audit_log_concept_id"), "score_audit_log", ["concept_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_score_audit_log_concept_id"), table_name="score_audit_log")
    op.drop_index(op.f("ix_score_audit_log_student_id"), table_name="score_audit_log")
    op.drop_index(op.f("ix_score_audit_log_tenant_id"), table_name="score_audit_log")
    op.drop_table("score_audit_log")

    op.drop_index(op.f("ix_learning_graph_events_event_type"), table_name="learning_graph_events")
    op.drop_index(op.f("ix_learning_graph_events_concept_id"), table_name="learning_graph_events")
    op.drop_index(op.f("ix_learning_graph_events_student_id"), table_name="learning_graph_events")
    op.drop_index(op.f("ix_learning_graph_events_tenant_id"), table_name="learning_graph_events")
    op.drop_table("learning_graph_events")

    op.drop_index("ix_student_concept_progress_tenant_student", table_name="student_concept_progress")
    op.drop_index(op.f("ix_student_concept_progress_status"), table_name="student_concept_progress")
    op.drop_index(op.f("ix_student_concept_progress_concept_id"), table_name="student_concept_progress")
    op.drop_index(op.f("ix_student_concept_progress_exam_id"), table_name="student_concept_progress")
    op.drop_index(op.f("ix_student_concept_progress_student_id"), table_name="student_concept_progress")
    op.drop_index(op.f("ix_student_concept_progress_tenant_id"), table_name="student_concept_progress")
    op.drop_table("student_concept_progress")
