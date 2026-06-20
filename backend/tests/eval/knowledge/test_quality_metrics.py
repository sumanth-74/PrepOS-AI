from __future__ import annotations

import json
from pathlib import Path

GOLDEN_PATH = Path(__file__).resolve().parent / "golden_questions.json"


def test_golden_question_suite_has_minimum_coverage() -> None:
    cases = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    assert len(cases) >= 100
    categories = {case["category"] for case in cases}
    for expected in {"Polity", "Economy", "History", "Geography", "Environment", "Current Affairs", "PYQ"}:
        assert expected in categories


def test_golden_questions_include_required_fields() -> None:
    cases = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    for case in cases:
        assert case["query"]
        assert case["exam_id"] == "upsc_cse"
        assert case["category"]
