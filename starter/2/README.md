# Stage 2 starter: your corporate index

This is a partial index definition. The key and the two searchable text fields (`subject`,
`content`) are done for you. The remaining schema decisions are yours to make in Stage 2.

Decide and set the attributes for these fields, then create the index:

| Field | Set which attributes? | Hint |
|-------|-----------------------|------|
| `recordType` | filterable, facetable | You will filter and group results by record type. |
| `branch` | filterable, facetable | Branch is a natural facet for "results by branch". |
| `department` | filterable, facetable | Department is a natural facet and filter. |
| `date` | filterable, sortable | You will sort newest-first and filter by date range. |

Leave `recordId` as the key (already set). Every field stays `retrievable` so you can show it in
results. If you fall behind, apply the Stage 2 baseline instead:

```
search-workshop/baseline/2/index.json
```

Placeholders (`{{namespace}}`, `{{searchEndpoint}}`) are filled with your own values. Never edit
another participant's index: your objects always begin with your `tNN-pNN-` namespace.
