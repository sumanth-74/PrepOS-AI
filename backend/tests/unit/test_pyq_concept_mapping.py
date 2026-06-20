from __future__ import annotations

import pytest

from prepos.domain.knowledge.pyq import map_concepts_from_pyq_text, parse_pyq_upload


def test_parse_json_pyq_upload_and_map_concepts() -> None:
    content = """
    [
      {
        "year": 2023,
        "exam_stage": "prelims",
        "paper": "GS2",
        "question_text": "Which article deals with President's Rule under federalism?",
        "answer_text": "Article 356",
        "concept_ids": []
      }
    ]
    """
    questions = parse_pyq_upload(content=content)
    assert len(questions) == 1
    assert questions[0].year == 2023
    assert questions[0].paper == "GS2"
    mapped = map_concepts_from_pyq_text(questions[0].question_text)
    assert "polity_article_356" in mapped


def test_parse_text_block_pyq_format() -> None:
    content = """2022 | prelims | GS1 | What is the basic structure doctrine?
Answer: Kesavananda Bharati case established it."""
    questions = parse_pyq_upload(content=content)
    assert len(questions) == 1
    assert questions[0].year == 2022
    assert "basic structure" in questions[0].question_text.lower()
