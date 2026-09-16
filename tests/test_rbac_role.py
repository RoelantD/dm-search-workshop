"""Custom-role least-privilege assertions (T019, feature 010).

Parses ``infra/search-workshop/modules/custom-role.bicep`` and enforces the allow-list
and deny-list from contracts/custom-role.contract.md without any live Azure call:

- every required Search object-management action is present;
- no forbidden service-administration or API-key action is present;
- no wildcard action is present.
"""
from __future__ import annotations

import re

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = _REPO_ROOT / "infra" / "search-workshop"

ROLE_BICEP = INFRA_DIR / "modules" / "custom-role.bicep"

REQUIRED_ACTIONS = {
    "Microsoft.Search/searchServices/read",
    "Microsoft.Search/searchServices/indexes/read",
    "Microsoft.Search/searchServices/indexes/write",
    "Microsoft.Search/searchServices/indexes/delete",
    "Microsoft.Search/searchServices/dataSources/read",
    "Microsoft.Search/searchServices/dataSources/write",
    "Microsoft.Search/searchServices/dataSources/delete",
    "Microsoft.Search/searchServices/indexers/read",
    "Microsoft.Search/searchServices/indexers/write",
    "Microsoft.Search/searchServices/indexers/delete",
    "Microsoft.Search/searchServices/skillsets/read",
    "Microsoft.Search/searchServices/skillsets/write",
    "Microsoft.Search/searchServices/skillsets/delete",
    "Microsoft.Search/searchServices/knowledgeSources/read",
    "Microsoft.Search/searchServices/knowledgeSources/write",
    "Microsoft.Search/searchServices/knowledgeSources/delete",
    "Microsoft.Search/searchServices/knowledgeBases/read",
    "Microsoft.Search/searchServices/knowledgeBases/write",
    "Microsoft.Search/searchServices/knowledgeBases/delete",
    "Microsoft.Search/operations/read",
}

FORBIDDEN_ACTIONS = {
    "Microsoft.Search/searchServices/write",
    "Microsoft.Search/searchServices/delete",
    "Microsoft.Search/searchServices/listAdminKeys/action",
    "Microsoft.Search/searchServices/regenerateAdminKey/action",
    "Microsoft.Search/searchServices/listQueryKeys/action",
    "Microsoft.Search/searchServices/createQueryKey/action",
    "Microsoft.Authorization/roleAssignments/write",
}

# Any single-quoted token that looks like an ARM action (namespace/resource form).
_ACTION_TOKEN = re.compile(r"'([A-Za-z0-9./*_-]*(?:/[A-Za-z0-9./*_-]+)+)'")


def _bicep_text() -> str:
    assert ROLE_BICEP.exists(), f"missing custom role bicep: {ROLE_BICEP}"
    return ROLE_BICEP.read_text(encoding="utf-8")


def _declared_actions() -> set[str]:
    """Return only the action tokens inside the ``actions`` array."""
    text = _bicep_text()
    match = re.search(r"var actions = \[(.*?)\]", text, re.DOTALL)
    assert match, "could not locate the 'actions' array in the bicep"
    return set(_ACTION_TOKEN.findall(match.group(1)))


def test_all_required_actions_present() -> None:
    declared = _declared_actions()
    missing = REQUIRED_ACTIONS - declared
    assert not missing, f"custom role is missing required actions: {sorted(missing)}"


def test_no_forbidden_action_present() -> None:
    declared = _declared_actions()
    present = FORBIDDEN_ACTIONS & declared
    assert not present, f"custom role contains forbidden actions: {sorted(present)}"


def test_no_wildcard_action() -> None:
    declared = _declared_actions()
    wildcards = {a for a in declared if "*" in a}
    assert not wildcards, f"custom role uses wildcard actions: {sorted(wildcards)}"


def test_data_actions_are_empty() -> None:
    text = _bicep_text()
    assert "dataActions: []" in text, "custom role must declare empty dataActions"
    assert "notActions: []" in text, "custom role must declare empty notActions"


def test_role_is_custom() -> None:
    text = _bicep_text()
    assert "'CustomRole'" in text, "role type must be CustomRole"
