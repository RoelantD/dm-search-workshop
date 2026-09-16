"""Baseline and definition validity tests (T062, feature 010).

Every canonical Search object definition and every per-stage baseline is a
version-controlled asset that ``workshop.ps1 baseline apply`` and the facilitator setup
resolve at apply time. These tests keep those assets trustworthy without any live Azure
call: each file must be syntactically valid JSON, use only the allowed namespace
placeholders, reference only the GA API version, and contain no secret material
(Principles VII, IX, X). Paths are computed from ``__file__`` so the suite runs anywhere.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
SEARCH_WORKSHOP = _REPO_ROOT / "search-workshop"
DEFINITIONS_DIR = SEARCH_WORKSHOP / "definitions"
BASELINE_DIR = SEARCH_WORKSHOP / "baseline"

# The only placeholders any template or baseline may contain (search-objects.contract.md).
ALLOWED_PLACEHOLDERS = {
    "namespace",
    "searchEndpoint",
    "apiVersion",
    "storageResourceId",
    "storageContainer",
    "foundryEndpoint",
    "foundryResourceId",
    "modelDeploymentName",
}

# The single GA API version every generally available asset may reference.
GA_API_VERSION = "2026-04-01"

# The pinned preview API version, allowed only in the Stage 6 answer-synthesis finale files.
PREVIEW_API_VERSION = "2026-08-01-preview"

# Files explicitly allowed to reference the pinned preview API version. These are the Stage 6
# answer-synthesis finale variant only; every other asset stays generally available.
PREVIEW_ALLOWED: set[str] = {
    "search-workshop/definitions/knowledge-base-synthesis.template.json",
    "search-workshop/baseline/6/knowledge-base-synthesis.json",
}

_PLACEHOLDER = re.compile(r"\{\{\s*(\w+)\s*\}\}")
_API_VERSION = re.compile(r"\b20\d\d-\d\d-\d\d(?:-preview)?\b")

# Secret material that must never appear in a participant-facing asset. The managed-identity
# datasource uses ``connectionString`` with the ``ResourceId=`` form, which carries no secret,
# so the word ``connectionString`` itself is intentionally not on this list.
_SECRET_PATTERNS = [
    re.compile(p, re.IGNORECASE)
    for p in (
        r"accountkey\s*=",
        r"sharedaccesskey",
        r"[?&]sig=",
        r"listkeys",
        r"primarykey",
        r"secondarykey",
        r"adminkey",
        r'"api-key"',
        r"apikey\s*[:=]",
    )
]


def _iter_asset_files() -> list[Path]:
    files: list[Path] = sorted(DEFINITIONS_DIR.glob("*.template.json"))
    files += sorted(BASELINE_DIR.rglob("*.json"))
    return files


ASSET_FILES = _iter_asset_files()


def test_assets_exist() -> None:
    assert DEFINITIONS_DIR.glob("*.template.json"), "no definition templates found"
    assert (BASELINE_DIR / "2").exists(), "missing Stage 2 baseline"
    assert (BASELINE_DIR / "3").exists(), "missing Stage 3 baseline"
    assert (BASELINE_DIR / "4").exists(), "missing Stage 4 baseline"
    assert (BASELINE_DIR / "5").exists(), "missing Stage 5 baseline"
    assert (BASELINE_DIR / "6").exists(), "missing Stage 6 baseline"


@pytest.mark.parametrize("path", ASSET_FILES, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_asset_is_valid_json(path: Path) -> None:
    json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize("path", ASSET_FILES, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_asset_uses_only_allowed_placeholders(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    used = set(_PLACEHOLDER.findall(text))
    unknown = used - ALLOWED_PLACEHOLDERS
    assert not unknown, f"{path.name} uses disallowed placeholders: {sorted(unknown)}"


@pytest.mark.parametrize("path", ASSET_FILES, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_asset_references_only_ga_api_version(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    versions = set(_API_VERSION.findall(text))
    if not versions:
        return  # only the {{apiVersion}} placeholder is present, which is fine
    rel = path.relative_to(_REPO_ROOT).as_posix()
    if rel in PREVIEW_ALLOWED:
        assert versions <= {GA_API_VERSION, PREVIEW_API_VERSION}, (
            f"{rel} references unexpected versions: {sorted(versions)}"
        )
        return
    assert versions == {GA_API_VERSION}, f"{path.name} references non-GA versions: {sorted(versions)}"


@pytest.mark.parametrize("path", ASSET_FILES, ids=lambda p: str(p.relative_to(_REPO_ROOT)))
def test_asset_has_no_secrets(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    for pattern in _SECRET_PATTERNS:
        assert not pattern.search(text), f"{path.name} contains secret-like material: {pattern.pattern}"


def test_managed_identity_datasource_uses_resourceid_form() -> None:
    ds = json.loads((DEFINITIONS_DIR / "datasource.template.json").read_text(encoding="utf-8"))
    conn = ds["definition"]["credentials"]["connectionString"]
    assert conn.startswith("ResourceId="), "datasource must connect by managed identity (ResourceId= form)"
    assert "AccountKey" not in conn, "datasource must not contain an account key"


def test_every_object_name_carries_namespace_prefix() -> None:
    for path in ASSET_FILES:
        obj = json.loads(path.read_text(encoding="utf-8"))
        if "name" in obj:
            assert obj["name"].startswith("{{namespace}}-"), f"{path.name} object name is not namespaced"
