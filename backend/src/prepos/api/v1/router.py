from __future__ import annotations

from fastapi import APIRouter

from prepos.api.v1.auth.router import router as auth_router
from prepos.api.v1.concepts.router import router as concepts_router
from prepos.api.v1.exams.router import router as exams_router
from prepos.api.v1.goals.router import router as goals_router
from prepos.api.v1.learning_graph.router import router as learning_graph_router
from prepos.api.v1.mentor.router import router as mentor_router
from prepos.api.v1.students.router import router as students_router
from prepos.api.v1.study_plan.router import router as study_plan_router
from prepos.api.v1.syllabus.router import router as syllabus_router
from prepos.api.v1.twin.router import router as twin_router

router = APIRouter()
router.include_router(auth_router)
router.include_router(exams_router)
router.include_router(syllabus_router)
router.include_router(concepts_router)
router.include_router(students_router)
router.include_router(learning_graph_router)
router.include_router(study_plan_router)
router.include_router(goals_router)
router.include_router(mentor_router)
router.include_router(twin_router)
