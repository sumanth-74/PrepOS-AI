#!/usr/bin/env python3
"""Seed PrepOS demo tenant with users, syllabus, learning graph, goals, and projections.

Usage:
  cd backend
  source .venv/bin/activate
  python scripts/seed_demo_data.py

Optional env:
  DATABASE_URL, SECRET_KEY, SMOKE_SKIP_MIGRATE=1
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

from sqlalchemy import func, select

BACKEND_ROOT = Path(__file__).resolve().parents[1]

from demo_seed_support import (  # noqa: E402
    CATALOG_VERSION,
    DEMO_ADMIN_EMAIL,
    DEMO_FACULTY_EMAIL,
    DEMO_PASSWORD,
    DEMO_STUDENT_EMAIL,
    DEMO_TENANT_SLUG,
    EXAM_ID,
    complete_student_onboarding,
    configure_demo_env,
    create_app_client,
    create_user_with_role,
    default_goal_payload,
    dispose_demo_resources,
    drain_outbox,
    ensure_demo_mentor_case,
    login,
    provision_learning_graph,
    register_or_login_admin,
    seed_exam_catalog,
)
from prepos.infrastructure.db.models.learning_graph import StudentConceptProgressModel  # noqa: E402


def run_migrations() -> None:
    if os.environ.get("SMOKE_SKIP_MIGRATE") == "1":
        print("==> Skipping migrations (SMOKE_SKIP_MIGRATE=1)")
        return
    print("==> Running alembic upgrade head")
    subprocess.run(
        [str(BACKEND_ROOT / ".venv/bin/alembic"), "upgrade", "head"],
        cwd=BACKEND_ROOT,
        env={**os.environ, **{"PYTHONPATH": str(BACKEND_ROOT / "src")}},
        check=True,
    )
    current = subprocess.run(
        [str(BACKEND_ROOT / ".venv/bin/alembic"), "current"],
        cwd=BACKEND_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    print(current.stdout.strip())


async def seed_demo_data() -> dict[str, object]:
    settings = configure_demo_env()
    _, client, session_factory = await create_app_client(settings)

    try:
        async with session_factory() as session:
            tenant_id, admin_token = await register_or_login_admin(client, session)
            await create_user_with_role(
                session,
                tenant_id=UUID(tenant_id),
                email=DEMO_FACULTY_EMAIL,
                full_name="Demo Faculty Mentor",
                role_name="faculty",
            )
            await create_user_with_role(
                session,
                tenant_id=UUID(tenant_id),
                email=DEMO_STUDENT_EMAIL,
                full_name="Demo Student",
                role_name="student",
            )

            import_body = await seed_exam_catalog(client, admin_token)
            student_token = await login(client, email=DEMO_STUDENT_EMAIL)
            student_id, expected_nodes = await complete_student_onboarding(
                client,
                session,
                student_token=student_token,
            )
            try:
                provisioned = await provision_learning_graph(
                    session,
                    tenant_id=UUID(tenant_id),
                    student_id=UUID(student_id),
                )
            except Exception:
                provisioned = (
                    await session.execute(
                        select(func.count())
                        .select_from(StudentConceptProgressModel)
                        .where(StudentConceptProgressModel.student_id == UUID(student_id))
                    )
                ).scalar_one()
            onboarding_events = await drain_outbox(session)

            goal_headers = {"Authorization": f"Bearer {student_token}"}
            existing_goal = await client.get(
                "/api/v1/goals",
                headers=goal_headers,
                params={"exam_id": EXAM_ID},
            )
            if existing_goal.status_code == 200 and existing_goal.json() is not None:
                goal_events: list[str] = []
            else:
                goal = await client.post(
                    "/api/v1/goals",
                    headers=goal_headers,
                    json=default_goal_payload(),
                )
                goal.raise_for_status()
                goal_events = await drain_outbox(session)

            concept_id = (
                await session.execute(
                    select(StudentConceptProgressModel.concept_id)
                    .where(StudentConceptProgressModel.student_id == UUID(student_id))
                    .order_by(StudentConceptProgressModel.concept_id.asc())
                    .limit(1)
                )
            ).scalar_one()

            study = await client.post(
                "/api/v1/learning-graph/activities/study-session",
                headers=goal_headers,
                json={
                    "exam_id": EXAM_ID,
                    "concept_id": concept_id,
                    "engaged_minutes": 45,
                },
            )
            study.raise_for_status()

            revision = await client.post(
                "/api/v1/learning-graph/activities/revision",
                headers=goal_headers,
                json={
                    "exam_id": EXAM_ID,
                    "concept_id": concept_id,
                    "recall_grade": "good",
                },
            )
            revision.raise_for_status()

            activity_events = await drain_outbox(session)

            mentor_headers_preview = {"Authorization": f"Bearer {await login(client, email=DEMO_FACULTY_EMAIL)}"}
            mentor_queue_preview = (
                await client.get("/api/v1/mentor/queue", headers=mentor_headers_preview)
            ).json()
            demo_case_id: str | None = None
            if not mentor_queue_preview:
                demo_case_id = await ensure_demo_mentor_case(
                    session,
                    tenant_id=UUID(tenant_id),
                    student_id=UUID(student_id),
                )

            readiness_before = (
                await client.get("/api/v1/learning-graph/readiness", headers=goal_headers)
            ).json()
            recommendations = (
                await client.get("/api/v1/twin/recommendations", headers=goal_headers)
            ).json()
            study_plan = (await client.get("/api/v1/study-plan", headers=goal_headers)).json()
            twin_dashboard = (
                await client.get("/api/v1/twin/dashboard", headers=goal_headers)
            ).json()

            faculty_token = await login(client, email=DEMO_FACULTY_EMAIL)
            mentor_headers = {"Authorization": f"Bearer {faculty_token}"}
            mentor_dashboard = (
                await client.get("/api/v1/mentor/dashboard", headers=mentor_headers)
            ).json()
            mentor_queue = (
                await client.get("/api/v1/mentor/queue", headers=mentor_headers)
            ).json()

            summary = {
                "tenant_slug": DEMO_TENANT_SLUG,
                "tenant_id": tenant_id,
                "credentials": {
                    "admin": {"email": DEMO_ADMIN_EMAIL, "password": DEMO_PASSWORD},
                    "faculty": {"email": DEMO_FACULTY_EMAIL, "password": DEMO_PASSWORD},
                    "student": {"email": DEMO_STUDENT_EMAIL, "password": DEMO_PASSWORD},
                },
                "exam": {
                    "exam_id": EXAM_ID,
                    "catalog_version": CATALOG_VERSION,
                    "concepts_imported": import_body.get("concepts_imported"),
                },
                "student": {
                    "student_id": student_id,
                    "expected_nodes": expected_nodes,
                    "provisioned_nodes": provisioned,
                    "sample_concept_id": concept_id,
                },
                "events_drained": {
                    "onboarding": len(onboarding_events),
                    "goal": len(goal_events),
                    "activity": len(activity_events),
                    "activity_types": sorted(set(activity_events)),
                },
                "projections": {
                    "readiness_overall_score": readiness_before.get("overall_score"),
                    "recommendation_count": len(recommendations),
                    "study_plan_daily_items": len(study_plan.get("daily_plan", [])),
                    "twin_dashboard_readiness": twin_dashboard.get("readiness_score"),
                    "mentor_queue_size": len(mentor_queue),
                    "mentor_effectiveness_score": mentor_dashboard.get("mentor_effectiveness_score"),
                    "demo_case_seeded": demo_case_id,
                },
            }
            print(json.dumps(summary, indent=2, default=str))
            return summary
    finally:
        await dispose_demo_resources(client)


def main() -> int:
    sys.path.insert(0, str(BACKEND_ROOT / "scripts"))
    sys.path.insert(0, str(BACKEND_ROOT / "src"))
    try:
        run_migrations()
        asyncio.run(seed_demo_data())
    except Exception as exc:
        print(f"Demo seed FAILED: {exc}", file=sys.stderr)
        return 1
    print("Demo seed PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
