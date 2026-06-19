from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from prepos.domain.scoring.confidence_v1 import CONFIDENCE_V1
from prepos.domain.scoring.importance_copy_v1 import IMPORTANCE_COPY_V1
from prepos.domain.scoring.mastery_nonmcq_v1 import MASTERY_NONMCQ_V1
from prepos.domain.scoring.mastery_v1 import MASTERY_V1
from prepos.domain.scoring.retention_v1 import RETENTION_V1


@dataclass(frozen=True, slots=True)
class MasteryScore:
    value: Decimal
    version: str = MASTERY_V1


@dataclass(frozen=True, slots=True)
class ConfidenceScore:
    value: Decimal
    version: str = CONFIDENCE_V1


@dataclass(frozen=True, slots=True)
class RetentionScore:
    value: Decimal | None
    version: str = RETENTION_V1


@dataclass(frozen=True, slots=True)
class ImportanceScore:
    value: Decimal
    version: str = IMPORTANCE_COPY_V1


@dataclass(frozen=True, slots=True)
class NodeVersion:
    value: int

    def next(self) -> NodeVersion:
        return NodeVersion(self.value + 1)


DEFAULT_NODE_SCORING_VERSIONS: dict[str, str] = {
    "mastery": MASTERY_V1,
    "mastery_nonmcq": MASTERY_NONMCQ_V1,
    "retention": RETENTION_V1,
    "confidence": CONFIDENCE_V1,
    "importance": IMPORTANCE_COPY_V1,
}
