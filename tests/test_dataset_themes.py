"""Search-theme coverage tests (T017, feature 010).

Asserts that the recurring business themes the workshop queries in Stage 4 and Stage 6
each appear in enough records to return recognizable results (FR-021). These are the
themes the sample queries and Foundry IQ multi-record questions depend on.
"""
from __future__ import annotations

import json

from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = _REPO_ROOT / "search-workshop" / "data"

ARCHIVE = DATA_DIR / "corporate-archive.json"

# Theme -> minimum number of records whose text mentions the theme keyword.
THEME_KEYWORDS = {
    "printer": 5,
    "paper": 8,
    "complaint": 4,
    "fire": 4,
    "warehouse": 4,
    "sales": 6,
}


@pytest.fixture(scope="module")
def records() -> list[dict]:
    assert ARCHIVE.exists(), f"missing dataset: {ARCHIVE} (run generate-dataset.py)"
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(("keyword", "minimum"), sorted(THEME_KEYWORDS.items()))
def test_theme_has_enough_records(records: list[dict], keyword: str, minimum: int) -> None:
    hits = sum(
        1
        for r in records
        if keyword in f"{r['subject']} {r['content']}".lower()
    )
    assert hits >= minimum, f"theme '{keyword}' appears in {hits} records, expected >= {minimum}"


def test_multi_record_themes_span_multiple_branches(records: list[dict]) -> None:
    # A Foundry IQ question about a theme should combine records from several branches.
    for keyword in ("printer", "fire", "complaint"):
        branches = {
            r["branch"]
            for r in records
            if keyword in f"{r['subject']} {r['content']}".lower()
        }
        assert len(branches) >= 2, f"theme '{keyword}' should span multiple branches"
