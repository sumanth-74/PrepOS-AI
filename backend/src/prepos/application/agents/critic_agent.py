from __future__ import annotations

import re
from uuid import uuid4

import structlog

from prepos.application.agents.models import AgentCritiqueRecord, AgentResult, AgentSource

logger = structlog.get_logger(__name__)

CLAIM_PATTERNS = (
    r"\b\d+(?:\.\d+)?%\b",
    r"\breadiness (?:score|is)\s+\d+",
    r"\bprobability (?:of success )?(?:is )?\d+",
    r"\btop recommendation:",
    r"\binstitution health score:",
)

MIN_CRITIQUE_SCORE = 0.65


class CriticAgent:
    """Reviews synthesized answers against tool evidence and citations."""

    agent_type = "critic_agent"

    def review(
        self,
        *,
        execution_id,
        answer: str,
        results: list[AgentResult],
        sources: list[AgentSource],
    ) -> AgentCritiqueRecord:
        unsupported_claims: list[str] = []
        citation_issues: list[str] = []
        evidence_text = " ".join(
            item.reasoning.lower()
            for item in results
            if item.success and item.reasoning
        )

        for pattern in CLAIM_PATTERNS:
            for match in re.finditer(pattern, answer.lower()):
                claim = match.group(0)
                if claim and claim not in evidence_text and not self._claim_supported(claim, results):
                    unsupported_claims.append(claim)

        if results and not sources:
            citation_issues.append("Response has tool results but no citations were attached.")
        if not results:
            citation_issues.append("No supporting tool results were produced.")

        successful = sum(1 for item in results if item.success)
        total = max(len(results), 1)
        score = round((successful / total) * 0.6 + (0.4 if not unsupported_claims else 0.0), 4)
        if citation_issues:
            score = round(score - 0.15, 4)
        score = max(0.0, min(1.0, score))
        passed = score >= MIN_CRITIQUE_SCORE and not unsupported_claims and not citation_issues

        reasoning = (
            "Critique passed: answer is supported by tool evidence."
            if passed
            else "Critique flagged unsupported claims or citation gaps."
        )
        logger.info(
            "agent_critique_completed",
            execution_id=str(execution_id),
            overall_score=score,
            passed=passed,
            unsupported_count=len(unsupported_claims),
        )
        return AgentCritiqueRecord(
            critique_id=uuid4(),
            execution_id=execution_id,
            overall_score=score,
            unsupported_claims=unsupported_claims,
            citation_issues=citation_issues,
            passed=passed,
            reasoning=reasoning,
        )

    @staticmethod
    def _claim_supported(claim: str, results: list[AgentResult]) -> bool:
        normalized_claim = claim.lower()
        for result in results:
            serialized = str(result.data).lower()
            if normalized_claim.strip("%") in serialized:
                return True
        return False
