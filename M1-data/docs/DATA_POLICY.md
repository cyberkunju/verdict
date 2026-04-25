# M1 Data Policy

The collection goal is aggressive, but not indiscriminate. Data must be legally
usable, ethically defensible, and technically traceable.

## Allowed Sources

- Public datasets with clear research terms.
- Public-domain or government video where reuse is allowed.
- Official public hearings, press conferences, and public testimony.
- Public videos used as links/metadata where the source terms permit access.
- Fact-check and court-record metadata used as citation/provenance.

## Restricted Sources

- Private videos, minors, non-public persons, leaked private recordings.
- Sources whose terms prohibit automated collection.
- Paywalled or licensed media copied into the dataset without permission.
- Social media bulk scraping without platform/API compliance.
- Contested claims treated as truth labels.

## Storage Principle

Prefer storing metadata, URLs, timestamps, checksums, and derived features.
Store raw video only when license/terms allow local research copies.

## Label Principle

Use these labels:

- `resolved_false`
- `resolved_true`
- `sincere_disclosure`
- `contested`
- `unclear`
- `exclude`

Only `resolved_false`, `resolved_true`, and carefully reviewed
`sincere_disclosure` examples are eligible for supervised fusion training.

## Abstention Principle

The model must learn when not to score:

- low face visibility
- poor audio
- bad transcript alignment
- probable edit/splice/deepfake
- no exact claim window
- uncertain ground truth
