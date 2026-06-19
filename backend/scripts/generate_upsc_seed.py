#!/usr/bin/env python3
"""Generate UPSC CSE catalog seed JSON from seed_catalog.py."""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = BACKEND_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from prepos.application.exam.seed_catalog import (  # noqa: E402
    CATALOG_VERSION,
    EXAM_ID,
    SubjectTargetCounts,
    build_catalog_seed,
    count_active_concepts_by_subject,
)

OUTPUT_PATH = BACKEND_ROOT.parent / "seeds" / "upsc_cse_concepts_v1_0.json"


def main() -> int:
    seed = build_catalog_seed()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        json.dump(seed, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    active_concepts = [concept for concept in seed["concepts"] if concept["status"] == "active"]
    subject_counts = count_active_concepts_by_subject()
    topic_counts = Counter(concept["topic_id"] for concept in active_concepts)

    print(f"Wrote {OUTPUT_PATH}")
    print(f"Exam: {EXAM_ID} catalog_version={CATALOG_VERSION}")
    print(f"Subjects: {len(seed['subjects'])} | Topics: {len(seed['topics'])} | Tracks: {len(seed['tracks'])}")
    print(f"Active concepts: {len(active_concepts)} | Relationships: {len(seed['relationships'])}")

    print("\nConcept counts by subject:")
    for subject_slug, target in SubjectTargetCounts.items():
        actual = subject_counts.get(subject_slug, 0)
        marker = "OK" if actual >= target else "BELOW TARGET"
        print(f"  {subject_slug:24s} {actual:3d} (target {target:3d}) {marker}")

    low_topics = [
        topic_id
        for topic_id in {topic["topic_id"] for topic in seed["topics"] if topic["status"] == "active"}
        if topic_counts[topic_id] < 3
    ]
    if low_topics:
        print("\nWARNING: topics with fewer than 3 active concepts:")
        for topic_id in sorted(low_topics):
            print(f"  {topic_id}: {topic_counts[topic_id]}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
