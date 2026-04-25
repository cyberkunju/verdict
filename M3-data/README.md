# M3-data: Specialist Extractors

M3 is the data and model program for VERDICT specialist extractors. The first
priority is camera-based heart-rate extraction using remote
photoplethysmography (rPPG).

Primary model family:

- `M3-A`: rPPG heart-rate and pulse-waveform specialist.
- `M3-B`: rPPG quality/reject specialist.
- `M3-C`: face/skin ROI specialist.
- `M3-D`: motion and illumination correction.
- `M3-E`: HRV specialist, only enabled when signal quality is high.

Policy:

- Public metadata, scripts, and manifests may be committed.
- Raw biometric videos and physiological signals stay out of git.
- Restricted datasets are acquired only through their official access process.
- Every training/eval run must report accuracy and coverage; rejecting a bad
  window is better than fabricating heart rate.

Top-level folders:

- `raw/public`: direct-download public datasets after user acquisition.
- `raw/restricted`: access-controlled datasets after formal approval.
- `raw/own-capture`: internally recorded consented data.
- `processed`: normalized clips, labels, window indexes, and feature caches.
- `models`: local model outputs only; cloud artifacts should be mirrored by
  manifest.
- `sources`: small metadata/source repositories and release forms.
- `registry`: source catalog and schema files.
- `manifests`: collection, inventory, and evaluation status.
- `scripts`: acquisition, inventory, validation, and training helpers.
