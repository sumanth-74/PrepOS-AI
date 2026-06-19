from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

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
from prepos.infrastructure.db.models.learning_graph import ScoreAuditLogModel, StudentConceptProgressModel
from prepos.infrastructure.db.repositories.event_repository import OutboxRepository
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

    me_response = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {register_response.json()['access_token']}"},
    )
    me = me_response.json()
    role = (await db_session.execute(select(RoleModel).where(RoleModel.name == "super_admin"))).scalar_one()
    db_session.add(UserRoleModel(tenant_id=me["tenant_id"], user_id=me["id"], role_id=role.id))
    await db_session.commit()

    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _seed_and_publish_exam(client: AsyncClient, admin_token: str) -> None:
    headers = {"Authorization": f"Bearer {admin_token}"}
    assert (await client.post("/api/v1/syllabus/seed/import", headers=headers)).status_code == 200
    assert (
        await client.post(
            f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
            headers=headers,
            json={"change_summary": "Learning graph event handler test publish"},
        )
    ).status_code == 200


async def _create_student_user(db_session: AsyncSession, *, tenant_id: str, email: str) -> str:
    role = (await db_session.execute(select(RoleModel).where(RoleModel.name == "student"))).scalar_one()
    user = UserModel(
        tenant_id=UUID(tenant_id),
        email=email,
        password_hash=hash_password("SecurePass123!"),
        full_name="Test Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    db_session.add(UserRoleModel(tenant_id=UUID(tenant_id), user_id=user.id, role_id=role.id))
    await db_session.commit()
    return str(user.id)


async def _login_student(client: AsyncClient, *, slug: str, email: str) -> str:
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": slug, "email": email, "password": "SecurePass123!"},
    )
    assert login_response.status_code == 200
    return login_response.json()["access_token"]


async def _provision_graph_for_student(
    client: AsyncClient,
    db_session: AsyncSession,
) -> tuple[str, str, str]:
    slug = "lg-event-handlers"
    admin_token = await _register_admin(client, db_session, slug=slug, email="admin-lg-events@example.com")
    await _seed_and_publish_exam(client, admin_token)

    me = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    tenant_id = me.json()["tenant_id"]
    await _create_student_user(db_session, tenant_id=tenant_id, email="student-lg-events@example.com")
    student_token = await _login_student(client, slug=slug, email="student-lg-events@example.com")
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
    assert (await client.post("/api/v1/students/onboarding/complete", headers=headers, json={})).status_code == 200

    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )
    await service.provision_from_onboarding(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        correlation_id="lg-events-provision",
        causation_id=None,
    )
    await db_session.commit()

    concept_id = (
        await db_session.execute(
            select(StudentConceptProgressModel.concept_id)
            .where(StudentConceptProgressModel.student_id == UUID(student_id))
            .order_by(StudentConceptProgressModel.concept_id.asc())
            .limit(1)
        )
    ).scalar_one()
    return tenant_id, student_id, concept_id


@pytest.mark.asyncio
async def test_handle_assessment_completed_updates_scores_audit_and_outbox(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)

    service = LearningGraphService(
        repo=SqlAlchemyLearningGraphRepository(db_session),
        exam_uow=SqlAlchemyExamCatalogUnitOfWork(db_session),
        outbox=OutboxPublisher(db_session),
        cache=NoOpLearningGraphCache(),
    )
    updated = await service.handle_assessment_completed(
        tenant_id=UUID(tenant_id),
        student_id=UUID(student_id),
        concept_id=concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="assessment-corr-1",
        causation_id="assessment-cause-1",
    )
    await db_session.commit()

    assert updated.mastery_score == Decimal("11.11")
    assert updated.confidence_score == Decimal("55.56")
    assert updated.retention_score is None
    assert updated.node_state == "rated"
    assert updated.mcq_attempt_count == 1
    assert updated.mcq_correct_count == 1

    audit_rows = (
        await db_session.execute(
            select(ScoreAuditLogModel).where(
                ScoreAuditLogModel.student_id == UUID(student_id),
                ScoreAuditLogModel.concept_id == concept_id,
            )
        )
    ).scalars().all()
    audit_types = {row.score_type for row in audit_rows}
    assert "mastery" in audit_types
    assert "confidence" in audit_types

    outbox_repo = OutboxRepository(db_session)
    events = await outbox_repo.fetch_pending(limit=50)
    lg_events = [event for event in events if event.event_type == "LearningGraphUpdated"]
    assert len(lg_events) >= 1
    payload = lg_events[-1].payload
    assert payload["concept_id"] == concept_id
    assert payload["student_id"] == student_id
    assert payload["mastery_score"] == 11.11
    assert payload["confidence_score"] == 55.56
    assert "mastery" in payload["changed_scores"]


@pytest.mark.asyncio
async def test_assessment_completed_handler_skips_duplicate_event_id(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    tenant_id, student_id, concept_id = await _provision_graph_for_student(client, db_session)

    event_id = uuid4()
    envelope = DomainEventEnvelope(
        event_id=event_id,
        event_version=1,
        event_type="AssessmentCompleted",
        occurred_at=datetime.now(UTC),
        recorded_at=datetime.now(UTC),
        tenant_id=UUID(tenant_id),
        correlation_id="assessment-dup-corr",
        causation_id=None,
        producer="assessment_service",
        payload={
            "student_id": student_id,
            "concept_id": concept_id,
            "mcq_correct": True,
        },
    )

    await dispatcher.dispatch(envelope)
    await db_session.commit()

    node_after_first = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    audit_count_after_first = (
        await db_session.execute(
            select(func.count())
            .select_from(ScoreAuditLogModel)
            .where(
                ScoreAuditLogModel.student_id == UUID(student_id),
                ScoreAuditLogModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    pending_after_first = await OutboxRepository(db_session).fetch_pending(limit=100)
    outbox_count_after_first = len(
        [event for event in pending_after_first if event.event_type == "LearningGraphUpdated"]
    )

    await dispatcher.dispatch(envelope)
    await db_session.commit()

    node_after_second = (
        await db_session.execute(
            select(StudentConceptProgressModel).where(
                StudentConceptProgressModel.student_id == UUID(student_id),
                StudentConceptProgressModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    audit_count_after_second = (
        await db_session.execute(
            select(func.count())
            .select_from(ScoreAuditLogModel)
            .where(
                ScoreAuditLogModel.student_id == UUID(student_id),
                ScoreAuditLogModel.concept_id == concept_id,
            )
        )
    ).scalar_one()
    pending_after_second = await OutboxRepository(db_session).fetch_pending(limit=100)
    outbox_count_after_second = len(
        [event for event in pending_after_second if event.event_type == "LearningGraphUpdated"]
    )

    assert node_after_first.mastery_score == Decimal("11.11")
    assert node_after_second.mastery_score == node_after_first.mastery_score
    assert node_after_second.row_version == node_after_first.row_version
    assert audit_count_after_second == audit_count_after_first
    assert outbox_count_after_second == outbox_count_after_first
