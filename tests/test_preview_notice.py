"""Preview-notice isolation test (T072, feature 010).

Only Stage 6 uses a preview Azure AI Search API (``2026-08-01-preview`` for grounded answer
synthesis); every other stage is generally available. FR-026 requires the preview dependency to
be clearly labeled and isolated to that one page. This test enforces that exactly the Stage 6
page carries the preview notice and no other stage page does. Paths are computed from
``__file__`` so the suite runs anywhere.
"""
from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
STAGES_DIR = _REPO_ROOT / "docs" / "search" / "stages"

# The marker that identifies the preview notice on a stage page.
PREVIEW_NOTICE_MARKER = "Preview notice"
FOUNDRY_STAGE = "06-foundry-iq.md"


def _stage_pages() -> list[Path]:
    pages = sorted(STAGES_DIR.glob("*.md"))
    assert pages, "no stage pages found"
    return pages


def test_only_foundry_stage_carries_the_preview_notice() -> None:
    foundry = STAGES_DIR / FOUNDRY_STAGE
    assert foundry.exists(), "missing Stage 6 Foundry IQ page"
    assert PREVIEW_NOTICE_MARKER in foundry.read_text(encoding="utf-8"), (
        "Stage 6 must carry the preview notice"
    )


def test_no_other_stage_carries_the_preview_notice() -> None:
    offenders = [
        page.name
        for page in _stage_pages()
        if page.name != FOUNDRY_STAGE
        and PREVIEW_NOTICE_MARKER in page.read_text(encoding="utf-8")
    ]
    assert not offenders, f"preview notice leaked onto non-Stage-6 pages: {offenders}"
