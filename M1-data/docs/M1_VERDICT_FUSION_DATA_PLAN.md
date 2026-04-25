# M1 VerdictFusion-v1 Exceptional Data Plan

## Objective

Build the best possible claim-level dataset for a calibrated multimodal fusion
model. The dataset must teach the model how signals combine, when they disagree,
and when the system should abstain.

## Data Streams

1. Public resolved claim archive.
2. Same-subject neutral baseline archive.
3. Specialist benchmark datasets.
4. Hard-negative archive.
5. Integrity/deepfake benchmark data.

## Collection Priority

### P0: Fix The Unit Of Truth

Collect claim windows and ground-truth citations. Do not train on whole videos.
This is the highest leverage improvement over the current project.

### P1: Build VERDICT Gold

Target first 500 claim windows:

- 250 resolved false
- 150 resolved true
- 100 sincere/high-stress truthful disclosures

Every item must have exact timestamps and at least one public outcome source.

### P2: Baseline Mining

For each recurring subject, collect 3-5 neutral videos:

- routine speech
- small talk
- non-controversial interview
- prepared remarks

The fusion model should learn deltas from same-subject baseline, not just
population-level anxiety.

### P3: Specialist Data

Use benchmark datasets to train or validate extractors:

- rPPG: UBFC-rPPG, PURE, UBFC-Phys, MMPD, SCAMPS.
- Face/AU: DISFA, BP4D/BP4D+, EmotioNet, Aff-Wild2.
- Voice: RAVDESS, IEMOCAP, CREMA-D, MSP-Podcast.
- Integrity: FaceForensics++, DFDC, Celeb-DF, DeeperForensics, FakeAVCeleb.

### P4: Hard Negatives

Collect examples that break naive systems:

- truthful people under intense stress
- calm false statements
- grief/anger/fear unrelated to deception
- media-trained speakers
- poor-quality archival footage
- edited news packages with voiceover contamination

## Model-Ready Output

The final feature table should have one row per claim:

- summary features
- timeline features
- modality quality values
- baseline deltas
- ground-truth label
- split metadata

The model should train on leave-subject-out and leave-event-out splits first.
