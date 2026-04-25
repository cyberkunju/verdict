# M1 Collection Status

Last updated from local collection scripts.

## Collected Locally

| Category | Count |
|---|---:|
| Cataloged sources | 30 |
| Seed VERDICT claim metadata rows | 6 |
| Raw open text/fact-check files | 7 |
| Processed text/fact-check JSONL files | 5 |
| Processed text/fact-check rows | 210,403 |
| DOJ resolution candidate rows | 702 |
| Model-ready multimodal fusion rows | 0 |
| Extracted multimodal feature rows | 0 |

## Processed Text / Fact-Check Rows

| Label bucket | Rows |
|---|---:|
| `resolved_false` | 119,501 |
| `resolved_true` | 24,630 |
| `contested_or_partial` | 65,955 |
| `unclear` | 317 |

## Important Interpretation

The 210,403 rows are useful for linguistic pretraining, claim verification,
entity mining, and ground-truth discovery. They are not yet direct
`VerdictFusion-v1` multimodal training rows because they do not include aligned
video/audio/face/rPPG/voice timelines.

The fusion model still needs audited claim windows and extracted multimodal
features before supervised fusion training can begin.
