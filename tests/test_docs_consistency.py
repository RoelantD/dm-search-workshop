"""Workshop documentation consistency tests.

The stage budget is stated in three places (each stage's frontmatter, the agenda on the
overview page, and the facilitator run sheet) and the shared per-event resource names are
regenerated for every workshop run. Both drifted between deliveries, which is expensive: a
facilitator paces from one table while attendees read another, or a whole room pastes a dead
Foundry endpoint into their skillset. These checks are offline and read only the Markdown.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = _REPO_ROOT / "docs" / "search"
STAGES_DIR = DOCS / "stages"

# Stages that make up the two-hour budget. Stage 8 is an optional stretch outside it.
CORE_STAGES = range(0, 8)
TOTAL_BUDGET_MINUTES = 120

_DURATION = re.compile(r'estimatedDuration:\s*"~(\d+) min"')
_ORDER = re.compile(r"^order:\s*(\d+)", re.MULTILINE)


def _stage_pages() -> dict[int, Path]:
    pages = {DOCS / "onboarding.md": None} | {p: None for p in STAGES_DIR.glob("*.md")}
    by_order: dict[int, Path] = {}
    for page in pages:
        text = page.read_text(encoding="utf-8")
        order = _ORDER.search(text)
        assert order, f"{page.name} has no 'order' in its frontmatter"
        by_order[int(order.group(1))] = page
    return by_order


def _frontmatter_budget() -> dict[int, int]:
    budgets = {}
    for order, page in _stage_pages().items():
        duration = _DURATION.search(page.read_text(encoding="utf-8"))
        assert duration, f"{page.name} has no estimatedDuration"
        budgets[order] = int(duration.group(1))
    return budgets


def _agenda_budget() -> dict[int, int]:
    text = (DOCS / "index.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(\d)\s*\|\s*\[.*?\].*?\|\s*~(\d+) min\s*\|", text, re.MULTILINE)
    return {int(stage): int(minutes) for stage, minutes in rows}


def _facilitator_budget() -> dict[int, int]:
    text = (DOCS / "facilitator.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(\d)\s*\|\s*[A-Za-z].*?\|\s*~(\d+) min\s*\|", text, re.MULTILINE)
    return {int(stage): int(minutes) for stage, minutes in rows}


@pytest.mark.parametrize("stage", CORE_STAGES)
def test_stage_budget_agrees_across_all_three_sources(stage: int) -> None:
    frontmatter, agenda, facilitator = _frontmatter_budget(), _agenda_budget(), _facilitator_budget()
    assert stage in frontmatter, f"stage {stage} has no page with estimatedDuration"
    assert stage in agenda, f"stage {stage} is missing from the overview agenda"
    assert stage in facilitator, f"stage {stage} is missing from the facilitator time budget"
    assert frontmatter[stage] == agenda[stage] == facilitator[stage], (
        f"stage {stage} budget disagrees: frontmatter={frontmatter[stage]}, "
        f"agenda={agenda[stage]}, facilitator={facilitator[stage]}"
    )


def test_core_stages_add_up_to_the_two_hour_budget() -> None:
    total = sum(_agenda_budget()[stage] for stage in CORE_STAGES)
    assert total == TOTAL_BUDGET_MINUTES, (
        f"the agenda budgets {total} minutes for stages 0 to 7, not {TOTAL_BUDGET_MINUTES}"
    )


def test_facilitator_elapsed_targets_are_contiguous_and_end_at_two_hours() -> None:
    """Each stage must start where the previous one ended, with no gaps or overlaps."""
    text = (DOCS / "facilitator.md").read_text(encoding="utf-8")
    rows = re.findall(r"^\|\s*(\d)\s*\|.*?\|\s*~\d+ min\s*\|\s*(\d):(\d\d) to (\d):(\d\d)\s*\|",
                      text, re.MULTILINE)
    assert len(rows) == len(list(CORE_STAGES)), "facilitator time budget is missing stages"
    previous_end = 0
    for stage, sh, sm, eh, em in rows:
        start, end = int(sh) * 60 + int(sm), int(eh) * 60 + int(em)
        assert start == previous_end, f"stage {stage} starts at {start} min, previous ended at {previous_end}"
        previous_end = end
    assert previous_end == TOTAL_BUDGET_MINUTES, f"run sheet ends at {previous_end} min"


def test_no_per_event_resource_names_are_hardcoded_in_stage_pages() -> None:
    """Shared Foundry resources are redeployed per workshop run.

    A concrete endpoint baked into a stage page silently goes stale on the next delivery, and
    the failure only shows up minutes later as a Cognitive Services error. Stage pages must
    point at the Session values page instead.
    """
    # An obvious placeholder (aif-dmsearch-xxxxxx) is fine; a real-looking suffix is not.
    endpoint = re.compile(r"https://aif-[a-z0-9-]+\.services\.ai\.azure\.com")
    offenders = [
        page.name
        for page in sorted(STAGES_DIR.glob("*.md"))
        for match in endpoint.findall(page.read_text(encoding="utf-8"))
        if "xxx" not in match
    ]
    assert not offenders, (
        f"stage pages hardcode a per-event Foundry endpoint: {offenders}. "
        "Use a placeholder and link to session-values.md."
    )


def test_session_values_page_exists_and_lists_every_per_event_value() -> None:
    page = DOCS / "session-values.md"
    assert page.exists(), "missing docs/search/session-values.md"
    text = page.read_text(encoding="utf-8")
    for key in (
        "foundryEndpoint",
        "modelDeploymentName",
        "modelName",
        "embeddingDeploymentName",
        "embeddingModelName",
        "storageAccountName",
    ):
        assert key in text, f"session-values.md does not mention the manifest key {key}"


def test_environment_manifest_emits_every_value_the_session_page_needs() -> None:
    """The facilitator copies these from the deployment manifest, so it has to emit them."""
    main_bicep = (_REPO_ROOT / "infra" / "search-workshop" / "main.bicep").read_text(encoding="utf-8")
    manifest = main_bicep[main_bicep.index("output environmentManifest"):]
    for key in ("foundryEndpoint", "modelDeploymentName", "modelName",
                "embeddingDeploymentName", "embeddingModelName", "storageAccountName"):
        assert f"{key}:" in manifest, f"environmentManifest does not emit {key}"
