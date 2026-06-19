from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID
from prepos.core.security import hash_password
from prepos.infrastructure.db.models.foundation import RoleModel, UserModel, UserRoleModel
from prepos.infrastructure.db.models.student import LearningGraphProvisionModel, PreparationTwinModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository


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


async def _seed_exam_only(client: AsyncClient, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    import_response = await client.post("/api/v1/syllabus/seed/import", headers=headers)
    assert import_response.status_code == 200


async def _seed_and_publish_exam(client: AsyncClient, admin_token: str) -> None:
    await _seed_exam_only(client, admin_token)
    headers = {"Authorization": f"Bearer {admin_token}"}
    publish_response = await client.post(
        f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
        headers=headers,
        json={"change_summary": "Student onboarding test publish"},
    )
    assert publish_response.status_code == 200


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


@pytest.mark.asyncio
async def test_student_onboarding_flow_provisions_and_outbox(client: AsyncClient, db_session: AsyncSession) -> None:
    slug = "student-onboard-tenant"
    admin_token = await _register_admin(client, db_session, slug=slug, email="admin-onboard@example.com")
    await _seed_and_publish_exam(client, admin_token)

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    tenant_id = me.json()["tenant_id"]
    _, student_email = await _create_student_user(
        db_session,
        tenant_id=tenant_id,
        email="student-onboard@example.com",
    )
    student_token = await _login_student(client, slug=slug, email=student_email)
    headers = {"Authorization": f"Bearer {student_token}"}

    me_response = await client.get("/api/v1/students/me", headers=headers)
    assert me_response.status_code == 200
    profile = me_response.json()
    assert profile["onboarding_completed"] is False
    student_id = profile["id"]

    patch_response = await client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={
            "target_exam": EXAM_ID,
            "target_year": 2026,
            "daily_study_hours": "4.00",
            "experience_level": "beginner",
        },
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["target_exam"] == EXAM_ID

    complete_response = await client.post(
        "/api/v1/students/onboarding/complete",
        headers=headers,
        json={"diagnostic_offered": True},
    )
    assert complete_response.status_code == 200
    body = complete_response.json()
    assert body["student"]["onboarding_completed"] is True
    assert body["provisioning"]["expected_node_count"] > 0
    assert body["provisioning"]["catalog_version"] == CATALOG_VERSION
    assert len(body["provisioning"]["target_stages"]) >= 1

    from uuid import UUID

    student_uuid = UUID(student_id)
    lg_result = await db_session.execute(
        select(LearningGraphProvisionModel).where(LearningGraphProvisionModel.student_id == student_uuid)
    )
    lg_row = lg_result.scalar_one()
    assert lg_row.status == "provisioned"
    assert lg_row.provisioned_node_count == 0
    assert lg_row.expected_node_count == body["provisioning"]["expected_node_count"]

    twin_result = await db_session.execute(
        select(PreparationTwinModel).where(PreparationTwinModel.student_id == student_uuid)
    )
    twin_row = twin_result.scalar_one()
    assert twin_row.status == "provisioned"
    assert twin_row.academic_profile == {}
    assert twin_row.prediction_profile.get("readiness") is None

    outbox_repo = OutboxRepository(db_session)
    events = await outbox_repo.fetch_pending(limit=50)
    onboarding_events = [event for event in events if event.event_type == "StudentOnboardingCompleted"]
    assert len(onboarding_events) >= 1
    payload = onboarding_events[-1].payload
    assert payload["student_id"] == student_id
    assert payload["diagnostic_offered"] is True
    assert isinstance(payload["target_stages"], list)


@pytest.mark.asyncio
async def test_student_tenant_isolation(client: AsyncClient, db_session: AsyncSession) -> None:
    slug_a = "student-tenant-a"
    slug_b = "student-tenant-b"
    token_a = await _register_admin(client, db_session, slug=slug_a, email="admin-a@example.com")
    token_b = await _register_admin(client, db_session, slug=slug_b, email="admin-b@example.com")

    me_a = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_a}"})
    me_b = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token_b}"})

    _, email_a = await _create_student_user(
        db_session, tenant_id=me_a.json()["tenant_id"], email="student-a@example.com"
    )
    _, email_b = await _create_student_user(
        db_session, tenant_id=me_b.json()["tenant_id"], email="student-b@example.com"
    )

    token_student_a = await _login_student(client, slug=slug_a, email=email_a)
    token_student_b = await _login_student(client, slug=slug_b, email=email_b)

    profile_a = await client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {token_student_a}"},
    )
    await client.get(
        "/api/v1/students/me",
        headers={"Authorization": f"Bearer {token_student_b}"},
    )
    student_a_id = profile_a.json()["id"]

    cross_tenant = await client.get(
        f"/api/v1/students/{student_a_id}",
        headers={"Authorization": f"Bearer {token_student_b}"},
    )
    assert cross_tenant.status_code == 404


@pytest.mark.asyncio
async def test_student_cannot_update_goals_after_onboarding(client: AsyncClient, db_session: AsyncSession) -> None:
    slug = "student-patch-tenant"
    admin_token = await _register_admin(client, db_session, slug=slug, email="admin-patch@example.com")
    await _seed_and_publish_exam(client, admin_token)

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    _, student_email = await _create_student_user(
        db_session,
        tenant_id=me.json()["tenant_id"],
        email="student-patch@example.com",
    )
    student_token = await _login_student(client, slug=slug, email=student_email)
    headers = {"Authorization": f"Bearer {student_token}"}

    profile = (await client.get("/api/v1/students/me", headers=headers)).json()
    student_id = profile["id"]
    await client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={
            "target_exam": EXAM_ID,
            "target_year": 2026,
            "daily_study_hours": "3.00",
            "experience_level": "intermediate",
        },
    )
    await client.post("/api/v1/students/onboarding/complete", headers=headers, json={"diagnostic_offered": False})

    blocked = await client.patch(
        f"/api/v1/students/{student_id}",
        headers=headers,
        json={"daily_study_hours": "5.00"},
    )
    assert blocked.status_code == 409


@pytest.mark.asyncio
async def test_complete_onboarding_requires_published_exam(client: AsyncClient, db_session: AsyncSession) -> None:
    slug = "student-unpublished-tenant"
    admin_token = await _register_admin(client, db_session, slug=slug, email="admin-unpub@example.com")
    await _seed_exam_only(client, admin_token)

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    _, student_email = await _create_student_user(
        db_session,
        tenant_id=me.json()["tenant_id"],
        email="student-unpub@example.com",
    )
    student_token = await _login_student(client, slug=slug, email=student_email)
    headers = {"Authorization": f"Bearer {student_token}"}

    profile = (await client.get("/api/v1/students/me", headers=headers)).json()
    await client.patch(
        f"/api/v1/students/{profile['id']}",
        headers=headers,
        json={
            "target_exam": EXAM_ID,
            "target_year": 2026,
            "daily_study_hours": "2.00",
            "experience_level": "beginner",
        },
    )

    response = await client.post("/api/v1/students/onboarding/complete", headers=headers, json={})
    assert response.status_code == 422
