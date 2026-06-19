from __future__ import annotations

import json
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Protocol
from uuid import UUID

from prepos.domain.learning_graph.entities import ConceptProgressNode, StudentGraphSummary


class _AsyncRedisClient(Protocol):
    async def set(self, name: str, value: str, *, ex: int | None = None) -> bool | None: ...

    async def get(self, name: str) -> str | bytes | None: ...

    async def delete(self, *names: str) -> int: ...


class LearningGraphCachePort(ABC):
    @abstractmethod
    async def get_node(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        raise NotImplementedError

    @abstractmethod
    async def set_node(self, node: ConceptProgressNode) -> None:
        raise NotImplementedError

    @abstractmethod
    async def get_summary(self, tenant_id: UUID, student_id: UUID) -> StudentGraphSummary | None:
        raise NotImplementedError

    @abstractmethod
    async def set_summary(self, summary: StudentGraphSummary) -> None:
        raise NotImplementedError

    @abstractmethod
    async def invalidate_student(self, tenant_id: UUID, student_id: UUID) -> None:
        raise NotImplementedError

    @abstractmethod
    async def invalidate_summary(self, tenant_id: UUID, student_id: UUID) -> None:
        raise NotImplementedError


def node_cache_key(tenant_id: UUID, student_id: UUID, concept_id: str) -> str:
    return f"lg:node:{tenant_id}:{student_id}:{concept_id}"


def summary_cache_key(tenant_id: UUID, student_id: UUID) -> str:
    return f"lg:summary:{tenant_id}:{student_id}"


def rollup_cache_key(tenant_id: UUID, student_id: UUID, dimension: str) -> str:
    return f"lg:rollup:{tenant_id}:{student_id}:{dimension}"


def _decimal_or_none(value: object) -> Decimal | None:
    if value is None:
        return None
    return Decimal(str(value))


class NoOpLearningGraphCache(LearningGraphCachePort):
    async def get_node(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        return None

    async def set_node(self, node: ConceptProgressNode) -> None:
        return None

    async def get_summary(self, tenant_id: UUID, student_id: UUID) -> StudentGraphSummary | None:
        return None

    async def set_summary(self, summary: StudentGraphSummary) -> None:
        return None

    async def invalidate_student(self, tenant_id: UUID, student_id: UUID) -> None:
        return None

    async def invalidate_summary(self, tenant_id: UUID, student_id: UUID) -> None:
        return None


class RedisLearningGraphCache(LearningGraphCachePort):
    def __init__(self, redis_client: _AsyncRedisClient, *, ttl_seconds: int = 300) -> None:
        self._redis = redis_client
        self._ttl = ttl_seconds

    async def get_node(
        self,
        tenant_id: UUID,
        student_id: UUID,
        concept_id: str,
    ) -> ConceptProgressNode | None:
        _ = (tenant_id, student_id, concept_id)
        return None

    async def set_node(self, node: ConceptProgressNode) -> None:
        await self._redis.set(
            node_cache_key(node.tenant_id, node.student_id, node.concept_id),
            "1",
            ex=self._ttl,
        )

    async def get_summary(self, tenant_id: UUID, student_id: UUID) -> StudentGraphSummary | None:
        raw = await self._redis.get(summary_cache_key(tenant_id, student_id))
        if raw is None:
            return None
        data = json.loads(raw)
        return StudentGraphSummary(
            tenant_id=UUID(data["tenant_id"]),
            student_id=UUID(data["student_id"]),
            exam_id=data["exam_id"],
            total_nodes=data["total_nodes"],
            active_nodes=data["active_nodes"],
            average_mastery=_decimal_or_none(data.get("average_mastery")),
            average_retention=_decimal_or_none(data.get("average_retention")),
            average_confidence=_decimal_or_none(data.get("average_confidence")),
            weakest_concept_ids=tuple(data["weakest_concept_ids"]),
        )

    async def set_summary(self, summary: StudentGraphSummary) -> None:
        payload = json.dumps(
            {
                "tenant_id": str(summary.tenant_id),
                "student_id": str(summary.student_id),
                "exam_id": summary.exam_id,
                "total_nodes": summary.total_nodes,
                "active_nodes": summary.active_nodes,
                "average_mastery": None if summary.average_mastery is None else str(summary.average_mastery),
                "average_retention": None if summary.average_retention is None else str(summary.average_retention),
                "average_confidence": None if summary.average_confidence is None else str(summary.average_confidence),
                "weakest_concept_ids": list(summary.weakest_concept_ids),
            }
        )
        await self._redis.set(summary_cache_key(summary.tenant_id, summary.student_id), payload, ex=self._ttl)

    async def invalidate_student(self, tenant_id: UUID, student_id: UUID) -> None:
        await self.invalidate_summary(tenant_id, student_id)

    async def invalidate_summary(self, tenant_id: UUID, student_id: UUID) -> None:
        await self._redis.delete(summary_cache_key(tenant_id, student_id))
