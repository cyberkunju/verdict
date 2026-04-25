# M3 rPPG Collection Status

Generated: 2026-04-25

## Current Local Assets

- `M3-data` folder created.
- MMPD metadata repository collected at `M3-data/sources/MMPD_rPPG_dataset`.
- MMPD release agreement and data usage protocol are present locally.
- MMPD metadata rows inventoried: `660`.
- UBFC-rPPG official Drive download was attempted. Folder enumeration worked,
  but Google Drive quota blocked the first large `vid.avi`; one small
  `gtdump.xmp` file was downloaded.
- MCD-rPPG metadata CSV files were collected from the public code repository.
- rPPG-Trends README and bibliography were collected.
- COHFACE Zenodo metadata was collected; raw files are restricted.
- Figshare public benchmark metadata was collected; direct file is
  `data.zip`, `18,022,127,161` bytes, MD5
  `629ce2a498be99ef58a7bb6847625816`.
- Existing rPPG-Toolbox checkout found at `research-data/pretrained/rppg_toolbox`.
- Existing pretrained rPPG-Toolbox checkpoints inventoried: `36`.

Checkpoint groups:

- `UBFC-rPPG`: `8`
- `PURE`: `9`
- `SCAMPS`: `6`
- `MA-UBFC`: `4`
- `BP4D`: `7`
- `iBVP`: `2`

## Raw Dataset Status

No complete full raw rPPG video/physiology dataset is present yet under
`M3-data/raw`.

This is expected for restricted biometric datasets. Full MMPD, VIPL-HR-V2,
VitalVideos, UBFC-Phys, and similar datasets must be acquired through their
official access processes.

## P0 Acquisition Queue

1. UBFC-rPPG: retry official Drive download or download manually in browser.
2. UBFC-Phys: download/request via dataUBFC portal if storage allows.
3. rPPG-10: download from Mendeley.
4. Figshare public benchmark: download `data.zip` if storage allows.
5. MMPD: submit official release agreement from eligible institution.
6. VitalVideos / MCD-rPPG: request/license dataset access.
7. VERDICT own capture: start consented internal collection.

## Immediate Training Readiness

We can start benchmark integration and inference testing with existing
rPPG-Toolbox code and pretrained checkpoints, but we should not claim a newly
trained top-quality M3 model until raw datasets are acquired and split by
subject.

## Hard Rule

Do not scrape random public videos as HR ground truth. Without synchronized PPG,
ECG, or pulse-oximeter labels, they are not valid training data for accurate
heart-rate estimation.
