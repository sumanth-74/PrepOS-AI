"""Shared helpers for PrepOS demo seeding and I1.2 E2E validation."""

from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from typing import Any
from uuid import UUID

from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from prepos.api.main import create_app
from decimal import Decimal

from prepos.application.twin.rebuild_factory import build_mentor_case_service
from prepos.domain.mentor.mentor_types_v1 import ActionUrgency, MentorActionType
from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID
from prepos.application.learning_graph.services import LearningGraphService
from prepos.core.config import Settings, get_settings
from prepos.core.database import create_engine, dispose_engine
from prepos.core.security import hash_password
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.foundation import OutboxEventModel, RoleModel, UserModel, UserRoleModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository

DEMO_TENANT_SLUG = "prepos-demo"
DEMO_TENANT_NAME = "PrepOS Demo Institute"
DEMO_ADMIN_EMAIL = "admin@prepos-demo.example.com"
DEMO_FACULTY_EMAIL = "faculty@prepos-demo.example.com"
DEMO_STUDENT_EMAIL = "student@prepos-demo.example.com"
DEMO_PASSWORD = "SecurePass123!"


def configure_demo_env() -> Settings:
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql+asyncpg://prepos:prepos@localhost:5432/prepos",
    )
    os.environ.setdefault(
        "SECRET_KEY",
        "dev-demo-seed-secret-key-minimum-32-characters-long",
    )
    os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "true")
    os.environ.setdefault("OTEL_ENABLED", "false")
    os.environ.setdefault("CORS_ORIGINS", '["http://localhost:3000","http://127.0.0.1:3000"]')
    get_settings.cache_clear()
    return get_settings()


def outbox_row_to_envelope(row: OutboxEventModel) -> DomainEventEnvelope:
    return DomainEventEnvelope(
        event_id=row.event_id,
        event_version=row.event_version,
        event_type=row.event_type,
        occurred_at=row.occurred_at,
        recorded_at=row.recorded_at,
        tenant_id=row.tenant_id,
        correlation_id=row.correlation_id,
        causation_id=row.causation_id,
        producer=row.producer,
        payload=row.payload,
        metadata=row.metadata_json,
    )


async def drain_outbox(session: AsyncSession, *, max_rounds: int = 80) -> list[str]:
    """Dispatch pending outbox events synchronously (dev / validation mode)."""
    from prepos.events.handlers import (  # noqa: F401
        behavior_profile_handlers,
        decision_handlers,
        exam_handlers,
        forecast_probability_handlers,
        foundation_handlers,
        goal_handlers,
        intervention_handlers,
        intervention_outcome_handlers,
        learning_graph_handlers,
        mentor_action_handlers,
        mentor_case_handlers,
        mentor_effectiveness_handlers,
        mentor_handlers,
        milestone_handlers,
        personalization_handlers,
        predicted_score_handlers,
        student_handlers,
        study_plan_handlers,
        twin_handlers,
    )

    repo = OutboxRepository(session)
    emitted: list[str] = []
    for _ in range(max_rounds):
        pending = await repo.fetch_pending(limit=200)
        if not pending:
            break
        for row in pending:
            await dispatcher.dispatch(outbox_row_to_envelope(row))
            await repo.mark_published(row.id)
            emitted.append(row.event_type)
        await session.commit()
    return emitted


async def create_app_client(settings: Settings) -> tuple[Any, AsyncClient, async_sessionmaker[AsyncSession]]:
    create_engine(settings)
    app = create_app()
    engine = create_async_engine(settings.database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test", timeout=60.0)
    return app, client, session_factory


async def dispose_demo_resources(client: AsyncClient) -> None:
    await client.aclose()
    await dispose_engine()


async def assign_role(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    user_id: UUID,
    role_name: str,
) -> None:
    role = (await session.execute(select(RoleModel).where(RoleModel.name == role_name))).scalar_one()
    existing = (
        await session.execute(
            select(UserRoleModel).where(
                UserRoleModel.user_id == user_id,
                UserRoleModel.role_id == role.id,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        session.add(UserRoleModel(tenant_id=tenant_id, user_id=user_id, role_id=role.id))
        await session.commit()


async def create_user_with_role(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    email: str,
    full_name: str,
    role_name: str,
) -> UUID:
    existing = (
        await session.execute(select(UserModel).where(UserModel.email == email))
    ).scalar_one_or_none()
    if existing is not None:
        await assign_role(session, tenant_id=tenant_id, user_id=existing.id, role_name=role_name)
        return existing.id

    user = UserModel(
        tenant_id=tenant_id,
        email=email,
        password_hash=hash_password(DEMO_PASSWORD),
        full_name=full_name,
        is_active=True,
    )
    session.add(user)
    await session.flush()
    await assign_role(session, tenant_id=tenant_id, user_id=user.id, role_name=role_name)
    await session.commit()
    return user.id


async def login(client: AsyncClient, *, email: str) -> str:
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": DEMO_TENANT_SLUG,
            "email": email,
            "password": DEMO_PASSWORD,
        },
    )
    response.raise_for_status()
    return response.json()["access_token"]


async def register_or_login_admin(client: AsyncClient, session: AsyncSession) -> tuple[str, str]:
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": DEMO_TENANT_NAME,
            "tenant_slug": DEMO_TENANT_SLUG,
            "email": DEMO_ADMIN_EMAIL,
            "password": DEMO_PASSWORD,
            "full_name": "Demo Institute Admin",
        },
    )
    if register.status_code == 201:
        token = register.json()["access_token"]
    elif register.status_code == 409:
        token = await login(client, email=DEMO_ADMIN_EMAIL)
    else:
        register.raise_for_status()
        token = register.json()["access_token"]

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    me.raise_for_status()
    tenant_id = me.json()["tenant_id"]
    user_id = me.json()["id"]
    await assign_role(
        session,
        tenant_id=UUID(tenant_id),
        user_id=UUID(user_id),
        role_name="institute_admin",
    )
    await assign_role(
        session,
        tenant_id=UUID(tenant_id),
        user_id=UUID(user_id),
        role_name="super_admin",
    )
    return tenant_id, await login(client, email=DEMO_ADMIN_EMAIL)


async def seed_exam_catalog(client: AsyncClient, admin_token: str) -> dict[str, Any]:
    headers = {"Authorization": f"Bearer {admin_token}"}
    import_response = await client.post("/api/v1/syllabus/seed/import", headers=headers)
    import_response.raise_for_status()
    import_body = import_response.json()

    publish = await client.post(
        f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
        headers=headers,
        json={"change_summary": "PrepOS I1.2 demo seed publish"},
    )
    if publish.status_code not in {200, 400}:
        publish.raise_for_status()
    return import_body


async def provision_learning_graph(session: AsyncSession, *, tenant_id: UUID, student_id: UUID) -> int:
    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(session),
        outbox=OutboxPublisher(session),
        cache=NoOpLearningGraphCache(),
    )
    count = await service.provision_from_onboarding(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="demo-seed-provision",
        causation_id=None,
    )
    await session.commit()
    return count


async def complete_student_onboarding(
    client: AsyncClient,
    session: AsyncSession,
    *,
    student_token: str,
) -> tuple[str, int]:
    headers = {"Authorization": f"Bearer {student_token}"}
    profile = (await client.get("/api/v1/students/me", headers=headers)).json()
    student_id = profile["id"]

    if not profile.get("onboarding_completed"):
        await client.patch(
            f"/api/v1/students/{student_id}",
            headers=headers,
            json={
                "target_exam": EXAM_ID,
                "target_year": 2026,
                "daily_study_hours": "4.00",
                "experience_level": "beginner",
            },
        )
        complete = await client.post(
            "/api/v1/students/onboarding/complete",
            headers=headers,
            json={"diagnostic_offered": True},
        )
        complete.raise_for_status()
        expected_nodes = complete.json()["provisioning"]["expected_node_count"]
    else:
        expected_nodes = profile.get("expected_node_count") or 618

    return student_id, expected_nodes


def default_goal_payload() -> dict[str, Any]:
    return {
        "exam_id": EXAM_ID,
        "target_readiness_score": "75.00",
        "target_date": (date.today() + timedelta(days=180)).isoformat(),
        "daily_capacity_minutes": 180,
    }


async def ensure_demo_mentor_case(
    session: AsyncSession,
    *,
    tenant_id: UUID,
    student_id: UUID,
) -> str | None:
    """Ensure at least one open mentor case exists for demo walkthroughs."""
    service = build_mentor_case_service(session=session)
    created = await service.process_mentor_action_updated(
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=EXAM_ID,
        action_type=MentorActionType.CONTACT_STUDENT,
        priority_score=Decimal("85.0"),
        urgency=ActionUrgency.HIGH,
        correlation_id="demo-seed-mentor-case",
        causation_id=None,
    )
    await session.commit()
    await drain_outbox(session)
    return str(created.case_id) if created is not None else None
