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


# The Stage 8 stretch proves vector retrieval by asking a question whose words are absent from
# the archive but whose meaning is present. Both halves of that have to hold in the data.
VECTOR_DEMO_QUERY_TERMS = (
    "temperature",
    "unhappy",
    "air conditioning",
    "thermostat",
    "hvac",
)
WORKPLACE_ENVIRONMENT_MARKERS = (
    "cooling unit",
    "radiator",
    "draught",
    "boiler",
    "damp air",
    "ventilation",
)


def test_workplace_environment_records_exist_for_the_vector_demo(records: list[dict]) -> None:
    """Stage 8 asks "staff unhappy about the office temperature" and promises vector search
    surfaces topically related records. Without records about workplace comfort in the archive,
    the query returns arbitrary nearest neighbours and the stage's whole argument falls flat."""
    hits = [
        r
        for r in records
        if any(m in f"{r['subject']} {r['content']}".lower() for m in WORKPLACE_ENVIRONMENT_MARKERS)
    ]
    assert len(hits) >= 6, f"only {len(hits)} workplace-environment records; Stage 8 needs a set"
    assert len({r["branch"] for r in hits}) >= 3, "workplace-environment records should span branches"


@pytest.mark.parametrize("term", VECTOR_DEMO_QUERY_TERMS)
def test_vector_demo_query_terms_are_absent_from_the_archive(records: list[dict], term: str) -> None:
    """The demo only lands because lexical retrieval cannot reach these records.

    If a later dataset edit introduces the word "temperature" (or a near synonym the query
    uses), lexical search starts matching too and Stage 8 stops demonstrating anything.
    """
    hits = [r["id"] for r in records if term in f"{r['subject']} {r['content']}".lower()]
    assert not hits, f"'{term}' now appears in {hits}; the Stage 8 vocabulary-mismatch demo breaks"
