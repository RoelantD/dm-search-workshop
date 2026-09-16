"""Stage 4 challenge-query verification (T060, feature 010).

Stage 4 asks attendees to run three example queries against their index. There is no live
Search service in CI, so this suite proves the queries return recognizable results by running
a deterministic offline lexical proxy over the real dataset
(``search-workshop/data/corporate-archive.json``). If these assertions hold, the same queries
return a non-trivial, recognizable set once the data is indexed (FR-021). Paths are computed
from ``__file__``; the check is fully offline and deterministic.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
ARCHIVE = _REPO_ROOT / "search-workshop" / "data" / "corporate-archive.json"


@pytest.fixture(scope="module")
def records() -> list[dict]:
    assert ARCHIVE.exists(), f"missing dataset: {ARCHIVE} (run generate-dataset.py)"
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))


def _text(record: dict) -> str:
    return f"{record['subject']} {record['content']}".lower()


def _matches(records: list[dict], *terms: str) -> list[dict]:
    """Records whose searchable text contains every term (lexical AND proxy)."""
    needles = [t.lower() for t in terms]
    return [r for r in records if all(n in _text(r) for n in needles)]


def test_printer_complaints_query_returns_recognizable_set(records: list[dict]) -> None:
    # Stage 4 query: printer problems and customer complaints about printers.
    hits = _matches(records, "printer")
    assert len(hits) >= 10, f"expected many printer records, got {len(hits)}"
    types = {r["recordType"] for r in hits}
    assert "internal-memo" in types, "printer records should include internal memos"


def test_fire_safety_named_employee_query_returns_recognizable_set(records: list[dict]) -> None:
    # Stage 4 query: fire safety incident involving a named employee (Alan Prentice).
    hits = _matches(records, "fire", "Alan Prentice")
    assert hits, "expected fire-safety records mentioning Alan Prentice"
    branches = {r["branch"] for r in hits}
    assert {"Rochester", "Nashua"} <= branches, f"expected Rochester and Nashua, got {branches}"
    assert all(r["recordType"] == "policy" for r in hits), "fire-safety records are policy records"


def test_branch_sales_grouped_by_department_returns_recognizable_set(records: list[dict]) -> None:
    # Stage 4 query: Stamford branch activity, filtered by branch and faceted by department.
    stamford = [r for r in records if r["branch"] == "Stamford"]
    assert stamford, "expected Stamford branch records"
    by_department = Counter(r["department"] for r in stamford)
    assert "Sales" in by_department, "Stamford should have Sales records"
    assert by_department["Sales"] >= 1
    assert len(by_department) >= 2, "faceting by department should yield more than one group"


def test_challenge_query_names_are_real_dataset_names(records: list[dict]) -> None:
    # Guardrail: the documented queries use real employees/branches, so no Office knowledge
    # is required to run them (Principle XII).
    all_text = " ".join(_text(r) for r in records)
    all_branches = {r["branch"] for r in records}
    assert "alan prentice" in all_text, "Alan Prentice must appear in the dataset"
    assert "Stamford" in all_branches, "Stamford must be a real branch in the dataset"
