"""Shared helpers for the search-workshop asset tests.

These tests validate version-controlled facts (dataset integrity, deterministic
naming, custom-role allow/deny lists, infrastructure scaling) with no live Azure
calls, so they run in CI on any machine.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Repository root = two levels up from this file (search-workshop/tests/).
REPO_ROOT = Path(__file__).resolve().parents[2]
SEARCH_WORKSHOP = REPO_ROOT / "search-workshop"
DATA_DIR = SEARCH_WORKSHOP / "data"
INFRA_DIR = REPO_ROOT / "infra" / "search-workshop"
SPECS_DIR = REPO_ROOT / "specs" / "010-azure-ai-search-workshop"

# Make the backend package importable so naming tests validate the single source
# of truth (app.workshop_access.namespace). That module only imports the stdlib,
# so no backend dependencies are required for the asset test suite.
_BACKEND = REPO_ROOT / "backend"
if str(_BACKEND) not in sys.path:
    sys.path.insert(0, str(_BACKEND))

