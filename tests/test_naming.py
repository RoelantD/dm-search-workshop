"""Deterministic naming tests (T013, feature 010, quickstart A).

Validates the single source of truth in ``app.workshop_access.namespace`` against
the fixed examples from research.md R6 and asserts that teams beyond 99 are rejected
rather than silently truncated. The backend package is placed on ``sys.path`` by the
conftest; the namespace module imports only the standard library.
"""
from __future__ import annotations

import pytest

from app.workshop_access.namespace import (
    NamespaceError,
    derive_namespace,
    is_valid_namespace,
    parse_namespace,
    resource_group_name,
)


@pytest.mark.parametrize(
    ("team", "slot", "expected"),
    [
        (1, 1, "t01-p01"),
        (4, 2, "t04-p02"),
        (10, 3, "t10-p03"),
        (99, 99, "t99-p99"),
    ],
)
def test_derive_namespace_examples(team: int, slot: int, expected: str) -> None:
    assert derive_namespace(team, slot) == expected


def test_namespace_is_zero_padded_two_digits() -> None:
    ns = derive_namespace(7, 5)
    assert ns == "t07-p05"
    assert is_valid_namespace(ns)


def test_parse_round_trips() -> None:
    for team in (1, 4, 10, 42, 99):
        for slot in (1, 2, 3):
            ns = derive_namespace(team, slot)
            assert parse_namespace(ns) == (team, slot)


def test_team_above_99_is_rejected() -> None:
    with pytest.raises(NamespaceError):
        derive_namespace(100, 1)


def test_team_zero_or_negative_is_rejected() -> None:
    with pytest.raises(NamespaceError):
        derive_namespace(0, 1)
    with pytest.raises(NamespaceError):
        derive_namespace(-1, 1)


def test_slot_above_99_is_rejected() -> None:
    with pytest.raises(NamespaceError):
        derive_namespace(1, 100)


@pytest.mark.parametrize(
    "bad",
    ["", "t1-p1", "t001-p01", "T01-P01", "t01_p01", "t01-p1", "team01-p01", None],
)
def test_invalid_namespace_strings_rejected(bad: object) -> None:
    assert not is_valid_namespace(bad)  # type: ignore[arg-type]
    with pytest.raises(NamespaceError):
        parse_namespace(bad)  # type: ignore[arg-type]


def test_resource_group_name_matches_naming_convention() -> None:
    assert resource_group_name(1) == "rg-dmsearch-01"
    assert resource_group_name(10) == "rg-dmsearch-10"
    with pytest.raises(NamespaceError):
        resource_group_name(100)
