"""Dataset integrity tests (T016, feature 010).

Validates the version-controlled corporate archive against the participant-facing
contract in specs/010-azure-ai-search-workshop/contracts/dataset.schema.json:
unique ids, required fields, valid ISO dates, allowed record types, corporate-only
content (no television-production metadata), and 100 to 300 record volume.
"""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = _REPO_ROOT / "search-workshop" / "data"

ARCHIVE = DATA_DIR / "corporate-archive.json"
SAMPLE = DATA_DIR / "corporate-archive.sample.json"

REQUIRED_FIELDS = {"id", "recordType", "branch", "department", "createdAt", "subject", "content"}
ALLOWED_RECORD_TYPES = {
    "meeting-note",
    "sales-note",
    "customer-call",
    "internal-memo",
    "warehouse-note",
    "hr-note",
    "complaint",
    "policy",
    "branch-update",
}
# Television-production vocabulary must never appear as a field name or in content.
FORBIDDEN_TOKENS = {"episode", "season", "scene", "script", "actor", "character", "airdate", "network"}

_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]+$")
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@pytest.fixture(scope="module")
def records() -> list[dict]:
    assert ARCHIVE.exists(), f"missing dataset: {ARCHIVE} (run generate-dataset.py)"
    return json.loads(ARCHIVE.read_text(encoding="utf-8"))


def test_volume_within_100_to_300(records: list[dict]) -> None:
    assert 100 <= len(records) <= 300, f"expected 100-300 records, got {len(records)}"


def test_ids_unique_and_valid(records: list[dict]) -> None:
    ids = [r["id"] for r in records]
    assert len(ids) == len(set(ids)), "record ids are not unique"
    assert all(_ID_PATTERN.match(i) for i in ids), "record ids contain invalid characters"


def test_required_fields_present(records: list[dict]) -> None:
    for r in records:
        assert REQUIRED_FIELDS <= set(r), f"record {r.get('id')} missing fields"
        assert set(r) == REQUIRED_FIELDS, f"record {r.get('id')} has unexpected fields: {set(r) - REQUIRED_FIELDS}"


def test_record_types_valid(records: list[dict]) -> None:
    for r in records:
        assert r["recordType"] in ALLOWED_RECORD_TYPES, f"invalid recordType: {r['recordType']}"


def test_dates_valid_iso(records: list[dict]) -> None:
    for r in records:
        value = r["createdAt"]
        assert _DATE_PATTERN.match(value), f"createdAt not ISO date: {value}"
        # Raises ValueError if not a real calendar date.
        date.fromisoformat(value)


def test_subject_and_content_bounds(records: list[dict]) -> None:
    for r in records:
        assert 1 <= len(r["subject"]) <= 200, f"subject length out of range in {r['id']}"
        assert len(r["content"]) >= 40, f"content too short in {r['id']}"


def test_no_television_metadata(records: list[dict]) -> None:
    for r in records:
        # No forbidden field names.
        assert not (set(r) & FORBIDDEN_TOKENS), f"record {r['id']} has forbidden field"
        haystack = f"{r['subject']} {r['content']}".lower()
        for token in FORBIDDEN_TOKENS:
            assert not re.search(rf"\b{re.escape(token)}\b", haystack), (
                f"record {r['id']} content contains forbidden token '{token}'"
            )


def test_dimensions_repeat_for_retrieval(records: list[dict]) -> None:
    # Repeated branches and departments make faceting and multi-record retrieval meaningful.
    branches = {r["branch"] for r in records}
    departments = {r["department"] for r in records}
    assert len(branches) >= 3, "expected several branches"
    assert len(departments) >= 3, "expected several departments"


def test_sample_is_subset_shape(records: list[dict]) -> None:
    assert SAMPLE.exists(), f"missing sample dataset: {SAMPLE}"
    sample = json.loads(SAMPLE.read_text(encoding="utf-8"))
    assert 10 <= len(sample) <= 20, f"sample should be 10-20 records, got {len(sample)}"
    for r in sample:
        assert set(r) == REQUIRED_FIELDS
