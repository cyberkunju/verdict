# M3 rPPG Data Plan

Goal: maximize camera heart-rate accuracy while preserving reliability. The
model must output heart-rate only when the video contains enough physiological
signal; otherwise it must reject or mark low confidence.

## Target Metrics

Controlled webcam/mobile conditions:

- HR MAE <= 2-3 BPM on accepted windows.
- At least 95 percent of accepted windows within 5 BPM.
- Calibration: predicted confidence should track absolute BPM error.

Real-world compressed/interview video:

- HR MAE <= 5-8 BPM on accepted windows.
- Explicit reject/low-confidence output for bad lighting, face motion,
  compression, occlusion, or unstable ROI.
- Report coverage alongside accuracy; high accuracy with low coverage is not
  enough.

## Required Dataset Mix

P0:

- UBFC-rPPG for webcam-style HR benchmark.
- PURE for controlled motion benchmark.
- MMPD for mobile, lighting, motion, talking, walking, skin-tone diversity.
- VitalVideos if licensed, for scale and fairness.
- VERDICT own capture for the exact deployment distribution.

P1:

- UBFC-Phys for stress/speech/arithmetic tasks.
- VIPL-HR/V2 for larger less-constrained HR estimation.
- SCAMPS or other synthetic data for pretraining and augmentation only.

P2:

- COHFACE, MAHNOB-HCI, and related multimodal physiology datasets for
  cross-domain robustness checks.

## Model Strategy

Train and evaluate an ensemble, not a single extractor:

- Classical baselines: GREEN, ICA, CHROM, POS, LGI, PBV, OMIT.
- Neural baselines: DeepPhys, PhysNet, TS-CAN, EfficientPhys, PhysFormer,
  PhysMamba, RhythmFormer, FactorizePhys, iBVPNet where available.
- Quality/reject model: predicts per-window usability and expected error.
- Temporal smoother: enforces physiologically plausible HR dynamics.
- Fusion head: combines candidates by SNR, motion, lighting, skin ROI
  stability, face-track stability, and learned confidence.

## Acceptance Gates

No M3 rPPG model is production-accepted unless it passes:

- within-dataset benchmark gates,
- cross-dataset gates,
- skin-tone/fairness slices,
- lighting slices,
- motion/talking/walking slices,
- camera/compression slices,
- reject-rate and confidence-calibration gates,
- own-capture validation gates.

## Critical Warning

rPPG cannot be perfect on arbitrary camera footage. Bad lighting, compression,
motion, makeup, face angle, frame-rate issues, and skin visibility can remove
the pulse signal. A top-quality system must refuse bad windows instead of
inventing BPM.
