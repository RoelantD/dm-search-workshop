"""Deterministic infra naming and scaling assertions (T027, feature 010).

Pure-Python, no Azure calls. Proves that changing ``environmentCount`` alone changes
only the number of team resource groups / Search services (FR-040/SC-003) and that the
deterministic base names are collision-free and follow research.md R6. The Search-service
global-uniqueness suffix (a Bicep ``uniqueString``) is opaque here, so uniqueness is
asserted on the deterministic ``rg-<prefix>-NN`` and ``srch-<prefix>-NN-`` base names,
and the orchestrator is parsed to confirm the naming functions it uses.
"""
from __future__ import annotations

import re

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
MAIN_BICEP = _REPO_ROOT / "infra" / "search-workshop" / "main.bicep"

PREFIX = "dmsearch"
COUNTS = [2, 5, 10, 15]

RG_RE = re.compile(r"^rg-dmsearch-\d{2}$")
SEARCH_BASE_RE = re.compile(r"^srch-dmsearch-\d{2}-$")


def team_resource_group(team_number: int, prefix: str = PREFIX) -> str:
    """Deterministic team resource group name (mirrors main.bicep)."""
    assert 1 <= team_number <= 99
    return f"rg-{prefix}-{team_number:02d}"


def team_search_base(team_number: int, prefix: str = PREFIX) -> str:
    """Deterministic Search service name prefix, minus the uniqueString suffix."""
    assert 1 <= team_number <= 99
    return f"srch-{prefix}-{team_number:02d}-"


def _names(count: int) -> tuple[list[str], list[str]]:
    rgs = [team_resource_group(i) for i in range(1, count + 1)]
    searches = [team_search_base(i) for i in range(1, count + 1)]
    return rgs, searches


def test_resource_group_names_unique_and_formatted() -> None:
    for count in COUNTS:
        rgs, _ = _names(count)
        assert len(rgs) == count
        assert len(set(rgs)) == count, f"duplicate team RG names at count={count}"
        assert all(RG_RE.match(name) for name in rgs), f"RG names off-scheme at count={count}"


def test_search_service_base_names_unique_and_formatted() -> None:
    for count in COUNTS:
        _, searches = _names(count)
        assert len(set(searches)) == count, f"duplicate Search base names at count={count}"
        assert all(SEARCH_BASE_RE.match(name) for name in searches), (
            f"Search base names off-scheme at count={count}"
        )


def test_scaling_is_additive_only() -> None:
    """Growing environmentCount only appends new teams; existing names never change."""
    for smaller, larger in zip(COUNTS, COUNTS[1:]):
        small_rgs, small_searches = _names(smaller)
        large_rgs, large_searches = _names(larger)
        assert large_rgs[:smaller] == small_rgs
        assert large_searches[:smaller] == small_searches


def test_fixed_examples() -> None:
    assert team_resource_group(1) == "rg-dmsearch-01"
    assert team_resource_group(10) == "rg-dmsearch-10"
    assert team_search_base(4).startswith("srch-dmsearch-04-")


def _main_bicep_text() -> str:
    assert MAIN_BICEP.exists(), f"missing orchestrator: {MAIN_BICEP}"
    return MAIN_BICEP.read_text(encoding="utf-8")


def test_orchestrator_uses_deterministic_naming_functions() -> None:
    text = _main_bicep_text()
    # Team loop is driven by environmentCount alone.
    assert "range(0, environmentCount)" in text
    # Zero-padded two-digit team number.
    assert "padLeft(string(i + 1), 2, '0')" in text
    # Global-uniqueness suffix from a deterministic uniqueString (no random()).
    assert "uniqueString(subscription().id" in text
    assert "random(" not in text
    # Names follow research.md R6.
    assert "'rg-${resourceNamePrefix}-" in text
    assert "'srch-${resourceNamePrefix}-" in text


def test_orchestrator_scales_by_count_only() -> None:
    """The team RG / Search / RBAC loops all use the same environmentCount driver."""
    text = _main_bicep_text()
    loops = re.findall(r"in teamContexts", text)
    # team RGs, team module, storage RBAC, foundry RBAC, manifest summaries.
    assert len(loops) >= 4, f"expected the team loops to share teamContexts; found {len(loops)}"
