from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from prepos.application.learning_graph.dto import WeaknessItemResponse
from prepos.application.pyq.ports import PyqStatisticRecord
from prepos.application.recommendations.recommendation_engine import (
    LearningRecommendationEngine,
    RecommendationContext,
    format_concept_name,
)
from prepos.application.twin.twin_dto import TwinDashboardResponse


def _context(*, weaknesses: list[WeaknessItemResponse], pyq_stats: list[PyqStatisticRecord]) -> RecommendationContext:
    return RecommendationContext(
        tenant_id=uuid4(),
        student_id=uuid4(),
        exam_id="upsc_cse",
        dashboard=TwinDashboardResponse(
            readiness_score=Decimal("55"),
            gap_to_goal=Decimal("20"),
        ),
        weaknesses=weaknesses,
        goal=None,
        study_plan_items=[],
        twin_recommendations=[],
        pyq_statistics=pyq_stats,
    )


def test_format_concept_name() -> None:
    assert format_concept_name("upsc.polity_federalism") == "Polity Federalism"


def test_engine_orders_by_impact_score_deterministically() -> None:
    now = datetime.now(UTC)
    weaknesses = [
        WeaknessItemResponse(
            concept_id="upsc.polity_federalism",
            mastery_score=Decimal("30"),
            importance_score=Decimal("80"),
            weakness_score=Decimal("85"),
        ),
        WeaknessItemResponse(
            concept_id="upsc.history_ancient",
            mastery_score=Decimal("40"),
            importance_score=Decimal("50"),
            weakness_score=Decimal("55"),
        ),
    ]
    pyq_stats = [
        PyqStatisticRecord(
            exam_id="upsc_cse",
            concept_id="upsc.polity_federalism",
            pyq_count=14,
            first_appearance_year=2015,
            last_appearance_year=2024,
            frequency_score=75.0,
            trend_score=1.0,
            updated_at=now,
        ),
        PyqStatisticRecord(
            exam_id="upsc_cse",
            concept_id="upsc.history_ancient",
            pyq_count=2,
            first_appearance_year=2018,
            last_appearance_year=2020,
            frequency_score=20.0,
            trend_score=0.5,
            updated_at=now,
        ),
    ]
    engine = LearningRecommendationEngine()
    context = _context(weaknesses=weaknesses, pyq_stats=pyq_stats)

    first = engine.generate(context=context, limit=2)
    second = engine.generate(context=context, limit=2)

    assert first == second
    assert first[0].concept_id == "upsc.polity_federalism"
    assert first[0].impact_score >= first[1].impact_score
    assert "weakness" in first[0].reason_codes
    assert "high_pyq_frequency" in first[0].reason_codes


def test_engine_explain_returns_matching_concept() -> None:
    now = datetime.now(UTC)
    weaknesses = [
        WeaknessItemResponse(
            concept_id="upsc.economy_gst",
            mastery_score=Decimal("35"),
            importance_score=Decimal("70"),
            weakness_score=Decimal("75"),
        ),
    ]
    pyq_stats = [
        PyqStatisticRecord(
            exam_id="upsc_cse",
            concept_id="upsc.economy_gst",
            pyq_count=8,
            first_appearance_year=2017,
            last_appearance_year=2023,
            frequency_score=60.0,
            trend_score=1.0,
            updated_at=now,
        ),
    ]
    engine = LearningRecommendationEngine()
    context = _context(weaknesses=weaknesses, pyq_stats=pyq_stats)
    explained = engine.explain(context=context, concept_id="upsc.economy_gst")
    assert explained is not None
    assert explained.concept_name == "Economy Gst"
    assert explained.estimated_readiness_gain > 0
