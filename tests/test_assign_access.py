"""Attendee least-privilege assertions (T033, feature 010, Slice G).

Pure-Python, no Azure calls. Asserts that the attendee access surface (the
``assign-access.ps1`` facilitator script and the ``attendee-roles.bicep`` /
``attendee-storage-reader.bicep`` modules) grants exactly the four intended role
assignments (three distinct role names, Reader used twice at two scopes) and never
Contributor, Owner, key actions, or any RBAC-admin role (FR-006/FR-007, SC-004/SC-005),
and that no key is ever printed.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
ASSIGN_SCRIPT = _REPO_ROOT / "search-workshop" / "scripts" / "assign-access.ps1"
ATTENDEE_ROLES_BICEP = _REPO_ROOT / "infra" / "search-workshop" / "modules" / "attendee-roles.bicep"
ATTENDEE_STORAGE_READER_BICEP = (
    _REPO_ROOT / "infra" / "search-workshop" / "modules" / "attendee-storage-reader.bicep"
)

INTENDED_ROLES = {
    "Dunder Mifflin Workshop Search Developer",
    "Search Index Data Contributor",
    "Reader",
}

FORBIDDEN_ROLES = {
    "Contributor",
    "Owner",
    "Search Service Contributor",
    "User Access Administrator",
    "Role Based Access Control Administrator",
}

# Built-in role definition IDs that must never appear in the attendee module.
FORBIDDEN_ROLE_IDS = {
    "b24988ac-6180-42a0-ab88-20f7382dd24c",  # Contributor
    "8e3af657-a8ff-443c-a75c-2fe8c4bcb635",  # Owner
    "7ca78c08-252a-4471-8644-bb5ff32d4ba0",  # Search Service Contributor
    "18d7d88d-d35e-4fb5-a5c3-7773c20a72d9",  # User Access Administrator
    "f58310d9-a9f6-439a-9e8d-f62e7b41a168",  # Role Based Access Control Administrator
}

# Intended built-in role definition IDs.
SEARCH_INDEX_DATA_CONTRIBUTOR = "8ebe5a00-799e-43f5-93ac-243d3dce84a7"
READER = "acdd72a7-3385-48ef-bd42-f606fba81ae7"


def _read(path: Path) -> str:
    assert path.exists(), f"missing file: {path}"
    return path.read_text(encoding="utf-8")


def test_script_declares_only_the_three_intended_roles() -> None:
    text = _read(ASSIGN_SCRIPT)
    for role in INTENDED_ROLES:
        assert role in text, f"assign-access.ps1 must grant '{role}'"


def test_script_guardrail_refuses_forbidden_roles_with_exit_4() -> None:
    text = _read(ASSIGN_SCRIPT)
    assert "$ForbiddenRoles" in text, "script must declare a forbidden-role guardrail"
    for role in FORBIDDEN_ROLES:
        assert role in text, f"guardrail must name forbidden role '{role}'"
    assert "exit 4" in text, "guardrail refusal must exit with code 4"
    # Guardrail runs before any assignment is attempted.
    assert "Assert-NoForbiddenRole" in text


def test_script_never_prints_a_key() -> None:
    text = _read(ASSIGN_SCRIPT)
    for token in ("listAdminKeys", "listQueryKeys", "primaryKey", "account-key", "--query-key"):
        assert token not in text, f"assign-access.ps1 must not touch keys ({token})"


def test_attendee_module_grants_intended_roles_only() -> None:
    text = _read(ATTENDEE_ROLES_BICEP)
    assert SEARCH_INDEX_DATA_CONTRIBUTOR in text, "Search Index Data Contributor id missing"
    assert READER in text, "Reader id missing"
    # Custom role comes in by parameter, not a hard-coded privileged id.
    assert "customRoleDefinitionId" in text


def test_attendee_module_excludes_forbidden_roles() -> None:
    text = _read(ATTENDEE_ROLES_BICEP)
    for role_id in FORBIDDEN_ROLE_IDS:
        assert role_id not in text, f"attendee module must not grant role id {role_id}"


def test_attendee_module_scopes_reader_to_resource_group_only() -> None:
    text = _read(ATTENDEE_ROLES_BICEP)
    # Reader is scoped to the resource group, not the subscription.
    assert "scope: resourceGroup()" in text
    assert "subscription().id" not in text


def test_script_also_grants_reader_on_shared_storage_account() -> None:
    text = _read(ASSIGN_SCRIPT)
    assert "Resolve-SharedStorageAccount" in text, "script must resolve the shared storage account"
    assert "Microsoft.Storage/storageAccounts" in text
    assert "sharedStorageScope" in text


def test_attendee_module_delegates_shared_storage_reader() -> None:
    text = _read(ATTENDEE_ROLES_BICEP)
    # The shared-storage Reader assignment is a nested module (cross-resource-group
    # scope), not a direct resource in this file.
    assert "attendee-storage-reader.bicep" in text
    assert "sharedResourceGroupName" in text
    assert "sharedStorageAccountName" in text


def test_attendee_storage_reader_module_grants_only_reader() -> None:
    text = _read(ATTENDEE_STORAGE_READER_BICEP)
    assert READER in text, "Reader id missing"
    for role_id in FORBIDDEN_ROLE_IDS:
        assert role_id not in text, f"attendee storage-reader module must not grant role id {role_id}"
