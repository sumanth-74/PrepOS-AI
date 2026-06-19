from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from prepos.application.exam.seed_catalog import CATALOG_VERSION, EXAM_ID
from prepos.application.learning_graph.services import LearningGraphService
from prepos.domain.learning_graph.entities import ConceptProgressNode
from prepos.domain.learning_graph.exceptions import OptimisticLockFailureError
from prepos.domain.learning_graph.policies import NodeStatus
from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1
from prepos.domain.scoring.importance_copy_v1 import IMPORTANCE_COPY_V1
from prepos.domain.scoring.mastery_nonmcq_v1 import MASTERY_NONMCQ_V1
from prepos.domain.scoring.mastery_v1 import MASTERY_V1
from prepos.domain.scoring.retention_v1 import RETENTION_V1
from prepos.infrastructure.cache.learning_graph_cache import NoOpLearningGraphCache
from prepos.infrastructure.db.models.exam import ConceptModel
from prepos.infrastructure.db.repositories.learning_graph_repository import SqlAlchemyLearningGraphRepository


async def _seed_exam(client: AsyncClient, db_session: AsyncSession) -> None:
    from prepos.infrastructure.db.models.foundation import RoleModel, UserRoleModel

    register_response = await client.post(
        "/api/v1/auth/register",
        json={
            "tenant_name": "Lock Test Institute",
            "tenant_slug": "lg-lock-tenant",
            "email": "admin-lock@example.com",
            "password": "SecurePass123!",
            "full_name": "Admin User",
        },
    )
    assert register_response.status_code == 201
    token = register_response.json()["access_token"]

    me = (await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})).json()
    role = (await db_session.execute(select(RoleModel).where(RoleModel.name == "super_admin"))).scalar_one()
    db_session.add(
        UserRoleModel(
            tenant_id=me["tenant_id"],
            user_id=me["id"],
            role_id=role.id,
        )
    )
    await db_session.commit()

    login = await client.post(
        "/api/v1/auth/login",
        json={"tenant_slug": "lg-lock-tenant", "email": "admin-lock@example.com", "password": "SecurePass123!"},
    )
    admin_token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    assert (await client.post("/api/v1/syllabus/seed/import", headers=headers)).status_code == 200
    assert (
        await client.post(
            f"/api/v1/syllabus/{EXAM_ID}/catalog/versions/{CATALOG_VERSION}/publish",
            headers=headers,
            json={"change_summary": "Optimistic lock test publish"},
        )
    ).status_code == 200


def _progress_node(*, tenant_id, student_id, concept_row: ConceptModel) -> ConceptProgressNode:
    now = datetime.now(UTC)
    return ConceptProgressNode(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        concept_id=concept_row.concept_id,
        subject_id=concept_row.subject_id,
        topic_id=concept_row.topic_id,
        mastery_score=Decimal("0"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=None,
        confidence_score=None,
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=0,
        mcq_correct_count=0,
        nonmcq_attempt_count=0,
        revision_count=0,
        study_minutes=0,
        node_state=NodeStatus.UNRATED,
        mastery_version=MASTERY_V1,
        mastery_nonmcq_version=MASTERY_NONMCQ_V1,
        retention_version=RETENTION_V1,
        confidence_version=CONFIDENCE_V1,
        importance_version=IMPORTANCE_COPY_V1,
        first_seen_at=now,
        last_activity_at=None,
        row_version=1,
    )


@pytest.mark.asyncio
async def test_repository_save_node_conflict_raises_optimistic_lock_failure(
    client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    from uuid import UUID

    from prepos.core.security import hash_password
    from prepos.infrastructure.db.models.foundation import RoleModel, UserModel, UserRoleModel
    from prepos.infrastructure.db.models.student import StudentModel

    await _seed_exam(client, db_session)

    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "tenant_slug": "lg-lock-tenant",
            "email": "admin-lock@example.com",
            "password": "SecurePass123!",
        },
    )
    admin_token = login_response.json()["access_token"]
    me = (
        await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {admin_token}"},
        )
    ).json()
    tenant_id = UUID(me["tenant_id"])

    user = UserModel(
        tenant_id=tenant_id,
        email="student-lock@example.com",
        password_hash=hash_password("SecurePass123!"),
        full_name="Lock Student",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()
    student_role = (await db_session.execute(select(RoleModel).where(RoleModel.name == "student"))).scalar_one()
    db_session.add(UserRoleModel(tenant_id=tenant_id, user_id=user.id, role_id=student_role.id))
    student = StudentModel(
        tenant_id=tenant_id,
        user_id=user.id,
        target_exam_id=EXAM_ID,
        onboarding_completed=True,
    )
    db_session.add(student)
    await db_session.flush()

    concept_row = (await db_session.execute(select(ConceptModel).limit(1))).scalar_one()
    repo = SqlAlchemyLearningGraphRepository(db_session)
    node = _progress_node(tenant_id=tenant_id, student_id=student.id, concept_row=concept_row)
    await repo.bulk_insert_nodes((node,))
    await db_session.commit()

    stale = ConceptProgressNode(
        id=node.id,
        tenant_id=node.tenant_id,
        student_id=node.student_id,
        exam_id=node.exam_id,
        catalog_version=node.catalog_version,
        concept_id=node.concept_id,
        subject_id=node.subject_id,
        topic_id=node.topic_id,
        mastery_score=Decimal("11.11"),
        mastery_nonmcq_score=node.mastery_nonmcq_score,
        retention_score=node.retention_score,
        confidence_score=node.confidence_score,
        importance_score=node.importance_score,
        overconfidence_flag=node.overconfidence_flag,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=node.nonmcq_attempt_count,
        revision_count=node.revision_count,
        study_minutes=node.study_minutes,
        node_state=NodeStatus.RATED,
        mastery_version=node.mastery_version,
        mastery_nonmcq_version=node.mastery_nonmcq_version,
        retention_version=node.retention_version,
        confidence_version=node.confidence_version,
        importance_version=node.importance_version,
        first_seen_at=node.first_seen_at,
        last_activity_at=datetime.now(UTC),
        row_version=node.row_version,
    )

    with pytest.raises(OptimisticLockFailureError):
        await repo.save_node(stale, expected_row_version=999)


@pytest.mark.asyncio
async def test_learning_graph_service_retries_after_optimistic_lock_conflict() -> None:
    tenant_id = uuid4()
    student_id = uuid4()
    now = datetime.now(UTC)
    node = ConceptProgressNode(
        id=uuid4(),
        tenant_id=tenant_id,
        student_id=student_id,
        exam_id=EXAM_ID,
        catalog_version=CATALOG_VERSION,
        concept_id="history.ancient.indus_valley",
        subject_id="history",
        topic_id="history.ancient",
        mastery_score=Decimal("0"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=None,
        confidence_score=None,
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=0,
        mcq_correct_count=0,
        nonmcq_attempt_count=0,
        revision_count=0,
        study_minutes=0,
        node_state=NodeStatus.UNRATED,
        mastery_version=MASTERY_V1,
        mastery_nonmcq_version=MASTERY_NONMCQ_V1,
        retention_version=RETENTION_V1,
        confidence_version=CONFIDENCE_V1,
        importance_version=IMPORTANCE_COPY_V1,
        first_seen_at=now,
        last_activity_at=None,
        row_version=1,
    )
    saved = ConceptProgressNode(
        id=node.id,
        tenant_id=node.tenant_id,
        student_id=node.student_id,
        exam_id=node.exam_id,
        catalog_version=node.catalog_version,
        concept_id=node.concept_id,
        subject_id=node.subject_id,
        topic_id=node.topic_id,
        mastery_score=Decimal("11.11"),
        mastery_nonmcq_score=Decimal("0"),
        retention_score=Decimal("100.00"),
        confidence_score=Decimal("55.56"),
        importance_score=Decimal("50"),
        overconfidence_flag=False,
        mcq_attempt_count=1,
        mcq_correct_count=1,
        nonmcq_attempt_count=0,
        revision_count=0,
        study_minutes=0,
        node_state=NodeStatus.RATED,
        mastery_version=MASTERY_V1,
        mastery_nonmcq_version=MASTERY_NONMCQ_V1,
        retention_version=RETENTION_V1,
        confidence_version=CONFIDENCE_V1,
        importance_version=IMPORTANCE_COPY_V1,
        first_seen_at=node.first_seen_at,
        last_activity_at=now,
        row_version=2,
    )

    repo = AsyncMock()
    repo.get_node = AsyncMock(return_value=node)
    repo.save_node = AsyncMock(
        side_effect=[
            OptimisticLockFailureError("conflict", details={}),
            saved,
        ]
    )
    repo.append_score_audit = AsyncMock()
    repo.append_graph_event = AsyncMock()

    outbox = AsyncMock()
    outbox.enqueue_learning_graph_updated = AsyncMock()

    service = LearningGraphService(
        repo=repo,
        exam_uow=AsyncMock(),
        outbox=outbox,
        cache=NoOpLearningGraphCache(),
        max_retries=3,
    )

    result = await service.handle_assessment_completed(
        tenant_id=tenant_id,
        student_id=student_id,
        concept_id=node.concept_id,
        mcq_correct=True,
        self_confidence=None,
        correlation_id="corr-retry",
        causation_id="cause-retry",
    )

    assert result.mastery_score == Decimal("11.11")
    assert result.confidence_score == Decimal("55.56")
    assert result.row_version == 2
    assert repo.save_node.await_count == 2
