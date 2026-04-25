# VERDICT Own-Capture rPPG Protocol

Public datasets are not enough for exceptional performance. We need a consented
internal set matching target cameras and use cases.

## Hardware

- Camera: laptop webcam, phone front camera, and at least one higher-quality USB
  webcam.
- Ground truth: fingertip pulse oximeter with waveform export, or chest strap /
  ECG-grade HR reference.
- Optional: ambient light sensor or manual lighting labels.

## Per-Session Metadata

- participant_id pseudonym
- consent version
- age bucket
- Fitzpatrick skin tone or self-reported skin-tone category
- camera model
- resolution, FPS, bitrate, codec
- lighting type and approximate intensity
- glasses, facial hair, makeup, mask/occlusion
- task label
- reference sensor model
- synchronization method

## Required Tasks

- rest, neutral face: 60 seconds
- natural speech: 60 seconds
- reading aloud: 60 seconds
- arithmetic/stress task: 60 seconds
- post-exercise elevated HR: 60 seconds
- head rotation/nods: 60 seconds
- low-light and mixed-light variants when safe

## Split Rule

Split by participant, never by clip. No participant can appear in more than one
of train/validation/test.

## Safety

Do not collect medical claims or sensitive identity data. Store consent and raw
video outside git. Every derived artifact must be traceable to consent and
access permissions.
