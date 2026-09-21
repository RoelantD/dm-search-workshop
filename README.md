# Dunder Mifflin — Azure AI Search Workshop assets

Dataset, reference definitions, per-stage baselines, and tooling for the **Azure AI Search
Workshop**: a two-hour, portal-first path that turns a messy corporate archive into an
AI-enriched, grounded enterprise search solution.

**The workshop itself lives at <https://www.dundermifflin.nl/search/>.** You do not need this
repo to complete it; everything is done in the Azure portal. Clone it if you want to read the
archive offline, compare your work against the reference definitions, or take the templates home.

```bash
git clone https://github.com/RoelantD/dm-search-workshop.git
```

## What is in here

| Path | What it is |
|------|-----------|
| `data/corporate-archive.sample.json` | 15 readable records, used in Stage 1. |
| `data/corporate-archive.json` | The full 132-record archive that gets indexed. |
| `definitions/` | The reference definition for every object you build, as version-controlled JSON. |
| `baseline/<stage>/` | A known-good snapshot per stage, for catching up. |
| `starter/<stage>/` | Partially completed definitions you finish yourself. |
| `tests/` | Offline checks on the dataset, definitions, naming, and RBAC rules. |

## Placeholders

Definitions and baselines are templates. Every `{{placeholder}}` is filled in at apply time:

| Placeholder | Value |
|-------------|-------|
| `{{namespace}}` | Your personal namespace, `tNN-pNN` |
| `{{searchEndpoint}}` | Your team Search service endpoint |
| `{{apiVersion}}` | `2026-04-01` (generally available) |
| `{{storageResourceId}}`, `{{storageContainer}}` | The shared archive container |
| `{{foundryEndpoint}}` | The shared Foundry endpoint |
| `{{modelDeploymentName}}`, `{{modelName}}` | Chat deployment name, and the base model behind it |
| `{{embeddingDeploymentName}}`, `{{embeddingModelName}}` | The same two, for the Stage 8 vector stretch |

`deploymentId` and `modelName` are **not** the same string, and mixing them up is the most common
Stage 6 failure. The workshop's Session values page lists this session's actual values.

## Baselines

Every technical stage has a portal fallback documented on its workshop page: paste the matching
`baseline/<stage>/*.json` under your own namespace, replacing the placeholders above. That is the
expected path, and it needs nothing but a browser.

Facilitator tooling (access assignment, dataset upload, scripted baseline restore) lives in the
private workshop repository, not here. If you are stuck and the portal fallback is not working,
ask your facilitator.

No API key, connection string, or other secret appears anywhere in this repo, and the test suite
enforces that.

## Tests

Offline and deterministic; no Azure calls, no credentials.

```bash
python -m pytest tests/ -q
```

They check the dataset's integrity and themes, that the documented Stage 4 queries return a
recognizable set, that every definition is valid JSON using only known placeholders and the
pinned API versions, and that no secret material appears anywhere.

> Note: several suites deliberately reach into the parent workshop repository (the docs pages,
> the Bicep templates, the backend namespace module), so they only pass when run from the parent
> repo, where this is the `search-workshop/` submodule. A standalone clone can run the dataset
> and definition checks, not the whole suite.

## Upstream

This repo is consumed as a submodule by
[RoelantD/dunder-mifflin-package-management](https://github.com/RoelantD/dunder-mifflin-package-management),
which builds the workshop site. Changing anything here needs two commits: one here, and one there
moving the submodule pointer.
