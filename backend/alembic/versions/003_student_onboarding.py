"""Student profile, onboarding, and provisioning shell tables."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "003_student_onboarding"
down_revision = "002_exam_domain"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "students",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("target_exam_id", sa.String(length=64), nullable=True),
        sa.Column("target_year", sa.Integer(), nullable=True),
        sa.Column("daily_study_hours", sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column("experience_level", sa.String(length=32), nullable=True),
        sa.Column("onboarding_completed", sa.Boolean(), server_default="false", nullable=False),
        sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["target_exam_id"], ["exams.exam_id"], name=op.f("fk_students_target_exam_id_exams"), ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name=op.f("fk_students_user_id_users"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_students")),
        sa.UniqueConstraint("tenant_id", "user_id", name="uq_students_tenant_user"),
    )
    op.create_index(op.f("ix_students_tenant_id"), "students", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_students_user_id"), "students", ["user_id"], unique=False)
    op.create_index(op.f("ix_students_target_exam_id"), "students", ["target_exam_id"], unique=False)

    op.create_table(
        "learning_graph_provisions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("catalog_version", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="provisioned", nullable=False),
        sa.Column("expected_node_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("provisioned_node_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("provisioned_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_learning_graph_provisions_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_learning_graph_provisions_student_id_students"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_learning_graph_provisions")),
        sa.UniqueConstraint("tenant_id", "student_id", name="uq_learning_graph_provisions_tenant_student"),
    )
    op.create_index(op.f("ix_learning_graph_provisions_tenant_id"), "learning_graph_provisions", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_provisions_student_id"), "learning_graph_provisions", ["student_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_provisions_exam_id"), "learning_graph_provisions", ["exam_id"], unique=False)
    op.create_index(op.f("ix_learning_graph_provisions_status"), "learning_graph_provisions", ["status"], unique=False)

    op.create_table(
        "preparation_twins",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="provisioned", nullable=False),
        sa.Column("academic_profile", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("behavioral_profile", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("prediction_profile", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), server_default="{}", nullable=False),
        sa.Column("projection_version", sa.String(length=64), server_default="twin_projection_v1", nullable=False),
        sa.Column("row_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("last_rebuilt_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_event_id_processed", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["exam_id"], ["exams.exam_id"], name=op.f("fk_preparation_twins_exam_id_exams"), ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], name=op.f("fk_preparation_twins_student_id_students"), ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_preparation_twins")),
        sa.UniqueConstraint("tenant_id", "student_id", "exam_id", name="uq_preparation_twins_tenant_student_exam"),
    )
    op.create_index(op.f("ix_preparation_twins_tenant_id"), "preparation_twins", ["tenant_id"], unique=False)
    op.create_index(op.f("ix_preparation_twins_student_id"), "preparation_twins", ["student_id"], unique=False)
    op.create_index(op.f("ix_preparation_twins_exam_id"), "preparation_twins", ["exam_id"], unique=False)
    op.create_index(op.f("ix_preparation_twins_status"), "preparation_twins", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_preparation_twins_status"), table_name="preparation_twins")
    op.drop_index(op.f("ix_preparation_twins_exam_id"), table_name="preparation_twins")
    op.drop_index(op.f("ix_preparation_twins_student_id"), table_name="preparation_twins")
    op.drop_index(op.f("ix_preparation_twins_tenant_id"), table_name="preparation_twins")
    op.drop_table("preparation_twins")

    op.drop_index(op.f("ix_learning_graph_provisions_status"), table_name="learning_graph_provisions")
    op.drop_index(op.f("ix_learning_graph_provisions_exam_id"), table_name="learning_graph_provisions")
    op.drop_index(op.f("ix_learning_graph_provisions_student_id"), table_name="learning_graph_provisions")
    op.drop_index(op.f("ix_learning_graph_provisions_tenant_id"), table_name="learning_graph_provisions")
    op.drop_table("learning_graph_provisions")

    op.drop_index(op.f("ix_students_target_exam_id"), table_name="students")
    op.drop_index(op.f("ix_students_user_id"), table_name="students")
    op.drop_index(op.f("ix_students_tenant_id"), table_name="students")
    op.drop_table("students")
