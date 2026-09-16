# Stage 3 starter: automate ingestion

The data source (`datasource.json`) is complete. It connects to the shared archive container by
**managed identity** using the `ResourceId=` form: there is no account key and no secret anywhere.
Your team Search service has already been granted Storage Blob Data Reader on the container.

The indexer (`indexer.json`) is only partly wired. Two field mappings are done (`id` to `recordId`,
`subject` to `subject`). Finish the rest so every archive field lands in the right index field:

| Source (blob JSON) | Target (index field) |
|--------------------|----------------------|
| `recordType` | `recordType` |
| `branch` | `branch` |
| `department` | `department` |
| `createdAt` | `date` |
| `content` | `content` |

Add those five mappings to `fieldMappings`, then create the indexer and run it. If you fall
behind, apply the Stage 3 baseline instead:

```
search-workshop/baseline/3/
```

Placeholders (`{{namespace}}`, `{{searchEndpoint}}`, `{{storageResourceId}}`,
`{{storageContainer}}`) are filled with your own values by the facilitator setup or
`workshop.ps1`. Your objects always begin with your `tNN-pNN-` namespace, so you never touch a
teammate's data source or indexer.
