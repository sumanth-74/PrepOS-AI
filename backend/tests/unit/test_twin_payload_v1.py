from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from prepos.domain.scoring.readiness_drivers_v1 import ReadinessDriversV1
from prepos.domain.scoring.readiness_v1_1 import READINESS_V1_1, ReadinessResultV1_1
from prepos.domain.twin.entities import PersistedTwinRecommendation
from prepos.domain.twin.profile_versions import TWIN_PROFILE_V1
from prepos.domain.twin.twin_payload_v1 import (
    TwinReadinessPayloadInputs,
    TwinRecommendationsPayloadInputs,
    TwinRevisionQueuePayloadInputs,
    build_twin_payload_v1,
)


def test_build_twin_payload_v1_uses_readiness_v1_1() -> None:
    now = datetime(2026, 6, 18, 12, 0, tzinfo=UTC)
    rec_id = uuid4()
    tenant_id = uuid4()
    student_id = uuid4()
    result = ReadinessResultV1_1(
        overall_score=Decimal("71.50"),
        knowledge_subscore=Decimal("82.00"),
        retention_subscore=Decimal("64.00"),
        confidence_subscore=Decimal("70.00"),
        coverage_subscore=Decimal("48.00"),
        rated_node_count=150,
        total_node_count=320,
        unrated=False,
        version=READINESS_V1_1,
    )
    drivers = ReadinessDriversV1(
        largest_positive_driver="knowledge",
        largest_negative_driver="coverage",
        top_positive_drivers=("knowledge", "confidence"),
        top_negative_drivers=("coverage", "retention"),
    )

    payload = build_twin_payload_v1(
        readiness=TwinReadinessPayloadInputs(result=result, drivers=drivers),
        revision_queue=TwinRevisionQueuePayloadInputs(
            due_revision_count=3,
            high_risk_concept_count=2,
        ),
        recommendations=TwinRecommendationsPayloadInputs(
            recommendation_count=1,
            last_recommendation_at=now,
            top_recommendations=(
                PersistedTwinRecommendation(
                    id=rec_id,
                    tenant_id=tenant_id,
                    student_id=student_id,
                    exam_id="neet",
                    concept_id="concept-a",
                    recommendation_type="REVISION_DUE",
                    recommendation_score=Decimal("88.50"),
                    readiness_gain=Decimal("7.30"),
                    created_at=now,
                ),
            ),
        ),
        drivers=drivers,
    )

    assert payload["profile_version"] == TWIN_PROFILE_V1
    recommendations = payload["recommendations"]
    assert isinstance(recommendations, dict)
    assert recommendations["total_estimated_gain"] == 7.3
    readiness = payload["readiness"]
    assert readiness["version"] == READINESS_V1_1
    assert readiness["overall_score"] == 71.5
    assert readiness["knowledge_subscore"] == 82.0
    assert readiness["coverage_subscore"] == 48.0
    assert readiness["rated_node_count"] == 150
    assert readiness["total_node_count"] == 320
    assert readiness["readiness_score"] == 71.5
    assert payload["drivers"]["top_positive_drivers"] == ["knowledge", "confidence"]
