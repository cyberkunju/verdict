# M1-data: VerdictFusion-v1 Data Program

This folder is the data collection and governance workspace for the first core
model: `VerdictFusion-v1`.

`VerdictFusion-v1` is not a raw lie detector. It is a calibrated multimodal
fusion model trained on claim-level public statements. It receives extracted
physiological, facial, vocal, linguistic, context, and quality features and
outputs pattern scores with uncertainty and abstention reasons.

## Directory Map

| Path | Purpose |
|---|---|
| `registry/` | Source catalogs, schemas, and dataset metadata. |
| `manifests/` | Claim/video/source manifests ready for acquisition or labeling. |
| `annotations/` | Human labeling outputs from Label Studio/CVAT or manual review. |
| `scripts/` | Acquisition, validation, and catalog utilities. |
| `docs/` | Data policy, labeling guide, and collection plan. |
| `licenses/` | License notes and dataset access agreements. |
| `raw/` | Local raw data cache. Gitignored. |
| `processed/` | Clean normalized examples. Gitignored. |
| `features/` | Extracted model-ready feature tables/timelines. Gitignored. |
| `models/` | Local experimental model outputs. Gitignored. |

## Non-Negotiable Data Rule

Every training item must have provenance:

- original source URL or dataset ID
- license / terms status
- claim start/end timestamps
- active speaker identity
- ground-truth source
- label confidence
- train/eval eligibility
- quality flags

Unproven, contested, private, or unclear items are allowed in discovery
manifests, but not in supervised training labels.

## First Model Target

Training row = one claim window.

Minimum useful dataset:

- 500 resolved public claims
- 1,500 same-subject neutral baseline clips
- extracted features from rPPG, face, voice, language, and quality gates
- leave-subject-out and leave-event-out evaluation splits

Exceptional target:

- 10,000+ resolved public claims
- 30,000+ neutral baselines
- 100+ public figures
- multilingual expansion
- audited high-stress truthful and calm-false hard negatives
