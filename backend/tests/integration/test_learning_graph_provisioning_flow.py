from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID
from prepos.application.learning_graph.services import LearningGraphService
from prepos.core.security import hash_password
from prepos.domain.events.envelope import DomainEventEnvelope
from prepos.events.dispatcher import dispatcher
from prepos.events.outbox.publisher import OutboxPublisher
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.foundation import RoleModel, UserModel, UserRoleModel
from prepos.infrastructure.db.models.learning_graph import StudentConceptProgressModel
from prepos.infrastructure.db.models.student import LearningGraphProvisionModel
from prepos.infrastructure.db.repositories.exam_repository import SqlAlchemyExamCatalogUnitOfWork
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository


async def _register_admin(client: AsyncClient, db_session: AsyncSession, *, slug: str, email: str) -> str:
    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": f"Institute {slug}",
            "tenant_slug": slug,
            "email": email,
            "password": "SecurePass123!",
            "full_name": "Admin User",
        },
    )
    assert register_response.status_code == 201
    access_token = register_response.json()["access_token"]

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert me_response.status_code == 200
    me = me_response.json()

    role_result = await db_session.execute(select(RoleModel).where(RoleModel.name == "super_admin"))
    role = role_result.scalar_one()
    db_session.add(
        UserRoleModel(
            tenant_id=me["tenant_id"],
            user_id=me["id"],
            role_id=role.id,
        )
    )
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _seed_and_publish_exam(client: AsyncClient, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    import_response = await client.post("/api/v1/syllabus/seed/import", headers=headers)
    assert import_response.status_code == 200
    publish_response = await client.post(
        f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
        headers=headers,
        json={"change_summary": "Learning graph provisioning test publish"},
    )
    assert publish_response.status_code in {200, 400}
    if publish_response.status_code == 400:
        assert publish_response.json()["error"]["code"] == "CATALOG_ALREADY_PUBLISHED"


async def _create_student_user(
    db_session: AsyncSession,
    *,
    tenant_id: str,
    email: str,
) -> tuple[str, str]:
    from uuid import UUID

    role_result = await db_session.execute(select(RoleModel).where(RoleModel.name == "student"))
    student_role = role_result.scalar_one()

    user = UserModel(
        tenant_id=UUID(tenant_id),
        email=email,
        password_hash=hash_password("SecurePass123!"),
        full_name="Test Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(
        UserRoleModel(
            tenant_id=UUID(tenant_id),
            user_id=user.id,
            role_id=student_role.id,
        )
    )
    await db_session.commit()
    return str(user.id), email


async def _login_student(client: AsyncClient, *, slug: str, email: str) -> str:
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _complete_student_onboarding(
    client: AsyncClient,
    db_session: AsyncSession,
    *,
    slug: str,
    admin_email: str,
    student_email: str,
) -> tuple[str, str, int]:
    from uuid import UUID

    admin_token = await _register_admin(client, db_session, slug=slug, email=admin_email)
    await _seed_and_publish_exam(client, admin_token)

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    tenant_id = me.json()["tenant_id"]
    _, student_user_email = await _create_student_user(
        db_session,
        tenant_id=tenant_id,
        email=student_email,
    )
    student_token = await _login_student(client, slug=slug, email=student_user_email)
    headers = {"Authorization": f"Bearer {student_token}"}

    profile = (await client.get("/api/v1/students/me", headers=headers)).json()
    student_id = profile["id"]
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
    assert complete.status_code == 200
    expected_node_count = complete.json()["provisioning"]["expected_node_count"]

    lg_row = (
        await db_session.execute(
            select(LearningGraphProvisionModel).where(LearningGraphProvisionModel.student_id == UUID(student_id))
        )
    ).scalar_one()
    assert lg_row.expected_node_count == expected_node_count

    return tenant_id, student_id, expected_node_count


@pytest.mark.asyncio
async def test_learning_graph_provisioning_via_event_handler(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from datetime import UTC, datetime
    from uuid import UUID

    tenant_id, student_id, expected_node_count = await _complete_student_onboarding(
        client,
        db_session,
        slug="lg-provision-handler",
        admin_email="admin-lg-provision@example.com",
        student_email="student-lg-provision@example.com",
    )

    envelope = DomainEventEnvelope(
        event_id=UUID("00000000-0000-4000-8000-000000000101"),
        event_version=1,
        event_type="StudentOnboardingCompleted",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=UUID(tenant_id),
        correlation_id="lg-provision-corr",
        causation_id=None,
        producer="student_onboarding_service",
        payload={
            "student_id": student_id,
            "user_id": student_id,
            "tenant_id": tenant_id,
            "exam_id": EXAM_ID,
            "diagnostic_offered": True,
            "target_stages": ["prelims", "mains"],
            "catalog_version": CATALOG_VERSION,
        },
    )
    await dispatcher.dispatch(envelope)

    count = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == UUID(tenant_id),
                StudentConceptProgressModel.student_id == UUID(student_id),
            )
        )
    ).scalar_one()
    assert count == expected_node_count
    assert expected_node_count >= 497

    provision = (
        await db_session.execute(
            select(LearningGraphProvisionModel).where(LearningGraphProvisionModel.student_id == UUID(student_id))
        )
    ).scalar_one()
    assert provision.provisioned_node_count == expected_node_count
    assert provision.status == "complete"


@pytest.mark.asyncio
async def test_learning_graph_provisioning_is_idempotent(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from uuid import UUID

    tenant_id, student_id, expected_node_count = await _complete_student_onboarding(
        client,
        db_session,
        slug="lg-provision-idempotent",
        admin_email="admin-lg-idempotent@example.com",
        student_email="student-lg-idempotent@example.com",
    )

    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )
    first_count = await service.provision_from_onboarding(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="lg-idempotent-1",
        causation_id=None,
    )
    await db_session.commit()

    second_count = await service.provision_from_onboarding(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="lg-idempotent-2",
        causation_id=None,
    )
    await db_session.commit()

    assert first_count == expected_node_count
    assert second_count == expected_node_count

    db_count = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == UUID(tenant_id),
                StudentConceptProgressModel.student_id == UUID(student_id),
            )
        )
    ).scalar_one()
    assert db_count == expected_node_count


@pytest.mark.asyncio
async def test_learning_graph_provisioning_tenant_isolation(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from uuid import UUID

    tenant_a, student_a, expected_a = await _complete_student_onboarding(
        client,
        db_session,
        slug="lg-provision-tenant-a",
        admin_email="admin-lg-a@example.com",
        student_email="student-lg-a@example.com",
    )
    tenant_b, student_b, expected_b = await _complete_student_onboarding(
        client,
        db_session,
        slug="lg-provision-tenant-b",
        admin_email="admin-lg-b@example.com",
        student_email="student-lg-b@example.com",
    )

    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )
    await service.provision_from_onboarding(
        tenant_id=UUID(tenant_a),
        student_id=UUID(student_a),
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="lg-tenant-a",
        causation_id=None,
    )
    await service.provision_from_onboarding(
        tenant_id=UUID(tenant_b),
        student_id=UUID(student_b),
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="lg-tenant-b",
        causation_id=None,
    )
    await db_session.commit()

    count_a = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == UUID(tenant_a),
                StudentConceptProgressModel.student_id == UUID(student_a),
            )
        )
    ).scalar_one()
    count_b = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == UUID(tenant_b),
                StudentConceptProgressModel.student_id == UUID(student_b),
            )
        )
    ).scalar_one()
    cross_tenant = (
        await db_session.execute(
            select(func.count())
            .select_from(StudentConceptProgressModel)
            .where(
                StudentConceptProgressModel.tenant_id == UUID(tenant_a),
                StudentConceptProgressModel.student_id == UUID(student_b),
            )
        )
    ).scalar_one()

    assert count_a == expected_a
    assert count_b == expected_b
    assert cross_tenant == 0
