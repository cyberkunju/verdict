# M3 rPPG Acquisition Checklist

## Direct / Public First

- [ ] UBFC-rPPG: download official/requested archive or permitted mirror.
- [ ] PURE: request official dataset archive from TU Ilmenau contact.
- [ ] LGI-PPGI: download available large archives if host is reachable and usage is acceptable.
- [ ] Verify hashes and record archive paths.
- [ ] Expand into `M3-data/raw/public/<dataset>`.
- [ ] Run `python M3-data/scripts/validate_rppg_dataset_layout.py`.

## Restricted / Agreement Required

- [ ] MMPD: complete release agreement from eligible institution.
- [ ] MMPD: request full or mini dataset through official process.
- [ ] VIPL-HR-V2: request through institute/university email if eligible.
- [ ] UBFC-Phys: request access through dat@UBFC contact.
- [ ] VitalVideos: request/license relevant subset.
- [ ] Store restricted datasets under `M3-data/raw/restricted/<dataset>`.
- [ ] Record access owner, license, and allowed use in a private access log.

## Own Capture

- [ ] Draft consent language.
- [ ] Select reference sensor.
- [ ] Build capture app/protocol.
- [ ] Validate camera/reference synchronization.
- [ ] Collect pilot set across at least 10 participants.
- [ ] Expand to balanced lighting, motion, skin-tone, and camera conditions.

## Acceptance

- [ ] No participant overlap across train/validation/test.
- [ ] Every clip has synchronized reference HR/PPG.
- [ ] Every clip has metadata for camera, lighting, motion, and signal quality.
- [ ] Every dataset has a license/access record.
