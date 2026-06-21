"""Platform maturity: security, observability, validation, analytics (P11)."""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "053_platform_maturity"
down_revision = "052_prompt_registry"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "prompt_security_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source", sa.String(length=64), nullable=False),
        sa.Column("prompt_text", sa.Text(), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("attack_categories", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("blocked", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("blocked_reason", sa.Text(), nullable=True),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_prompt_security_events_tenant", "prompt_security_events", ["tenant_id"])
    op.create_index("ix_prompt_security_events_created", "prompt_security_events", ["created_at"])

    op.create_table(
        "tenant_audit_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("scope", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("total_checks", sa.Integer(), nullable=False),
        sa.Column("passed_checks", sa.Integer(), nullable=False),
        sa.Column("failed_checks", sa.Integer(), nullable=False),
        sa.Column("findings_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_tenant_audit_reports_tenant", "tenant_audit_reports", ["tenant_id"])

    op.create_table(
        "knowledge_security_scans",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=16), nullable=False),
        sa.Column("attack_categories", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("flagged", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("scan_status", sa.String(length=32), nullable=False),
        sa.Column("details_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_knowledge_security_scans_source", "knowledge_security_scans", ["source_id"])

    op.create_table(
        "rate_limit_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("endpoint_group", sa.String(length=64), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column("limit_value", sa.Integer(), nullable=False),
        sa.Column("blocked", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_rate_limit_events_tenant", "rate_limit_events", ["tenant_id"])

    op.create_table(
        "background_job_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("task_name", sa.String(length=128), nullable=False),
        sa.Column("task_id", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("idempotency_key", sa.String(length=128), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_background_job_events_status", "background_job_events", ["status"])
    op.create_index("ix_background_job_events_task", "background_job_events", ["task_name"])

    op.create_table(
        "real_user_questions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("persona", sa.String(length=16), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("intent", sa.String(length=64), nullable=True),
        sa.Column("answer_text", sa.Text(), nullable=True),
        sa.Column("trace_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_real_user_questions_tenant", "real_user_questions", ["tenant_id"])

    op.create_table(
        "question_labels",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("labeler_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("labeler_role", sa.String(length=32), nullable=False),
        sa.Column("label", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_question_labels_question", "question_labels", ["question_id"])

    op.create_table(
        "evaluation_reviews",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("question_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("reviewer_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("review_status", sa.String(length=32), nullable=False),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "forecast_accuracy_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("exam_id", sa.String(length=32), nullable=False),
        sa.Column("predicted_readiness", sa.Float(), nullable=False),
        sa.Column("actual_readiness", sa.Float(), nullable=False),
        sa.Column("absolute_error", sa.Float(), nullable=False),
        sa.Column("percentage_error", sa.Float(), nullable=False),
        sa.Column("within_tolerance", sa.Boolean(), nullable=False),
        sa.Column("forecast_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_forecast_accuracy_events_tenant", "forecast_accuracy_events", ["tenant_id"])

    op.create_table(
        "recommendation_validation_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("student_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("recommendation_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=32), nullable=False),
        sa.Column("predicted_gain", sa.Float(), nullable=True),
        sa.Column("actual_gain", sa.Float(), nullable=True),
        sa.Column("is_control", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_recommendation_validation_tenant", "recommendation_validation_events", ["tenant_id"])

    op.create_table(
        "backup_verification_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("component", sa.String(length=32), nullable=False),
        sa.Column("backup_success", sa.Boolean(), nullable=False),
        sa.Column("restore_success", sa.Boolean(), nullable=True),
        sa.Column("details_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "product_analytics_snapshots",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("snapshot_date", sa.Date(), nullable=False),
        sa.Column("metrics_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_product_analytics_date", "product_analytics_snapshots", ["snapshot_date"])

    op.create_table(
        "platform_readiness_scores",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("dimension_scores_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("findings_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "domain_event_stream_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("event_type", sa.String(length=128), nullable=False),
        sa.Column("stream_id", sa.String(length=128), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_domain_event_stream_type", "domain_event_stream_log", ["event_type"])


def downgrade() -> None:
    op.drop_index("ix_domain_event_stream_type", table_name="domain_event_stream_log")
    op.drop_table("domain_event_stream_log")
    op.drop_table("platform_readiness_scores")
    op.drop_index("ix_product_analytics_date", table_name="product_analytics_snapshots")
    op.drop_table("product_analytics_snapshots")
    op.drop_table("backup_verification_events")
    op.drop_index("ix_recommendation_validation_tenant", table_name="recommendation_validation_events")
    op.drop_table("recommendation_validation_events")
    op.drop_index("ix_forecast_accuracy_events_tenant", table_name="forecast_accuracy_events")
    op.drop_table("forecast_accuracy_events")
    op.drop_table("evaluation_reviews")
    op.drop_index("ix_question_labels_question", table_name="question_labels")
    op.drop_table("question_labels")
    op.drop_index("ix_real_user_questions_tenant", table_name="real_user_questions")
    op.drop_table("real_user_questions")
    op.drop_index("ix_background_job_events_task", table_name="background_job_events")
    op.drop_index("ix_background_job_events_status", table_name="background_job_events")
    op.drop_table("background_job_events")
    op.drop_index("ix_rate_limit_events_tenant", table_name="rate_limit_events")
    op.drop_table("rate_limit_events")
    op.drop_index("ix_knowledge_security_scans_source", table_name="knowledge_security_scans")
    op.drop_table("knowledge_security_scans")
    op.drop_index("ix_tenant_audit_reports_tenant", table_name="tenant_audit_reports")
    op.drop_table("tenant_audit_reports")
    op.drop_index("ix_prompt_security_events_created", table_name="prompt_security_events")
    op.drop_index("ix_prompt_security_events_tenant", table_name="prompt_security_events")
    op.drop_table("prompt_security_events")
