"""Service-to-service RBAC and secret-free assertions (T031, feature 010, Slice F).

Pure-Python, no Azure calls. Parses the ``infra/search-workshop`` Bicep to assert:

- the Search MI receives Storage Blob Data Reader scoped to the archive container;
- the Search MI receives Cognitive Services User on the shared Foundry account;
- both service-to-service modules are wired into the orchestrator;
- no key or connection-string function appears anywhere in the deployment (FR-007,
  Principle VII), and the manifest emits no secret.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
INFRA_DIR = _REPO_ROOT / "infra" / "search-workshop"
MODULES_DIR = INFRA_DIR / "modules"
MAIN_BICEP = INFRA_DIR / "main.bicep"
STORAGE_RBAC = MODULES_DIR / "rbac-search-to-storage.bicep"
FOUNDRY_RBAC = MODULES_DIR / "rbac-search-to-foundry.bicep"

# Built-in role definition IDs.
STORAGE_BLOB_DATA_READER = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
COGNITIVE_SERVICES_USER = "a97b65f3-24c7-4388-baec-2e87135dc908"

# Functions that would surface a secret; must never appear in the deployment.
SECRET_FUNCTIONS = [
    "listAdminKeys",
    "listQueryKeys",
    "listKeys",
    "primaryConnectionString",
    "connectionString",
    "primaryKey",
    "accountKey",
]


def _read(path: Path) -> str:
    assert path.exists(), f"missing bicep: {path}"
    return path.read_text(encoding="utf-8")


def test_storage_rbac_grants_blob_data_reader_on_container() -> None:
    text = _read(STORAGE_RBAC)
    assert STORAGE_BLOB_DATA_READER in text, "Storage Blob Data Reader role id missing"
    # Scoped to the archive container, not the whole account.
    assert "archiveContainer" in text
    assert "scope: storage::blobService::archiveContainer" in text
    assert "principalType: 'ServicePrincipal'" in text
    assert "searchPrincipalId" in text


def test_foundry_rbac_grants_cognitive_services_user_on_foundry() -> None:
    text = _read(FOUNDRY_RBAC)
    assert COGNITIVE_SERVICES_USER in text, "Cognitive Services User role id missing"
    assert "scope: foundry" in text
    assert "principalType: 'ServicePrincipal'" in text
    assert "searchPrincipalId" in text


def test_both_rbac_modules_are_wired_into_orchestrator() -> None:
    text = _read(MAIN_BICEP)
    assert "modules/rbac-search-to-storage.bicep" in text
    assert "modules/rbac-search-to-foundry.bicep" in text
    # Both consume each team Search service's managed identity principal.
    assert "teams[i].outputs.searchPrincipalId" in text


def test_no_secret_function_anywhere_in_deployment() -> None:
    for bicep in INFRA_DIR.rglob("*.bicep"):
        text = bicep.read_text(encoding="utf-8")
        for fn in SECRET_FUNCTIONS:
            assert fn not in text, f"{bicep.name} contains a secret function: {fn}"


def test_manifest_output_is_secret_free() -> None:
    text = _read(MAIN_BICEP)
    start = text.index("output environmentManifest")
    manifest = text[start:]
    for token in ("key", "secret", "password", "connectionString"):
        assert token.lower() not in manifest.lower(), (
            f"manifest output must not reference '{token}'"
        )
