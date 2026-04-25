# VERDICT — Person 1 Plan
## Pipeline, Signal Extraction, Scoring, and LLM Analyst

**Owner:** Person 1  
**Timebox:** 8 hours  
**Goal:** Produce 6 complete real analysis JSON files that the frontend can consume without changes.

> **Read first:** `AGENT.md` (rules of engagement), `CONTRACT.md` (locked schema, paths, tech stack — supreme authority), and `TASKS.md` (live phase-based checklist).
> If any field name, path, or value here ever conflicts with `CONTRACT.md`, **the contract wins**.

---

## Mission

You own the backend/data side of VERDICT.

Your output is not a polished app. Your output is **truth-looking, demo-ready analysis data** for 6 public video clips.

By Hour 4, Person 2 must receive real JSON files matching the locked schema. If the signal pipeline is imperfect, still ship plausible, clearly structured output. The frontend and demo depend on this handoff.

---

## Non-Negotiable Output

By the end of your workstream, you must deliver:

- **6 processed clip JSON files** in the agreed schema
- **rPPG-derived heart-rate features** or fallback estimated heart-rate features
- **Facial expression features** from Py-Feat or fallback simulated AU values
- **Voice features** from librosa or fallback extracted pitch features
- **Whisper transcript** or manually corrected transcript
- **Composite scores** for deception, sincerity, stress, confidence
- **LLM analyst report** with behavioral summary, comparative profile, qualifications
- **A short README note** explaining which signals are real vs fallback if any fallback was used

---

## Brutal Scope Rules

### Must Build

- CHROM-style rPPG or simplified face-color pulse extraction
- Facial AUs using Py-Feat if installation works
- Voice features using librosa
- Whisper transcript using faster-whisper or manual transcript fallback
- Composite scoring engine
- GPT-4o / Claude analyst report generation
- Batch processor for 6 clips

### Can Fake / Approximate If Needed

- AU values if Py-Feat breaks
- rPPG HR if archival footage is too noisy
- HRV metrics
- Jitter/shimmer if extraction is unstable
- Timeline data density

### Do Not Build

- No custom model training
- No OpenFace C++ setup
- No pyVHR dependency maze
- No deepfake detector
- No kinetic pose layer
- No temporal replay
- No live upload analyzer unless everything else is done
- No API server unless static JSON handoff is already complete

---

## H0 Handoff Contract — Locked JSON Schema

Person 2 will build the frontend against this schema from minute zero. Do not rename fields after H0. You may add fields, but do not delete or rename existing fields.

```json
{
  "clip_id": "nixon_1973",
  "subject": "Richard Nixon",
  "statement": "I am not a crook",
  "year": 1973,
  "context": "White House press conference, Orlando, FL",
  "ground_truth": "false",
  "ground_truth_source": "Resigned August 1974; Watergate confirmed",
  "video_url": "https://youtube.com/watch?v=...",
  "video_start_seconds": 14,
  "video_end_seconds": 26,
  "signals": {
    "hr_baseline_bpm": 74,
    "hr_peak_bpm": 94,
    "hr_delta_bpm": 20,
    "hrv_rmssd": 18.4,
    "au15_max_intensity": 2.8,
    "au14_max_intensity": 1.2,
    "au6_present": false,
    "au24_max_intensity": 2.1,
    "f0_baseline_hz": 112,
    "f0_peak_hz": 134,
    "f0_delta_hz": 22,
    "jitter_percent": 3.4,
    "shimmer_db": 2.1,
    "speech_rate_wpm": 124,
    "hedging_count": 3,
    "pronoun_drop_rate": 0.31,
    "transcript": "I am not a crook. I've earned everything I've got."
  },
  "scores": {
    "deception": 84,
    "sincerity": 31,
    "stress": 77,
    "confidence": 28
  },
  "llm_report": {
    "behavioral_summary": "...",
    "comparative_profile": "...",
    "qualifications": "..."
  },
  "similar_clips": ["clinton_1998", "armstrong_2005"]
}
```

---

## Recommended 6 Clips

Use these unless a clip is unusable:

1. **Richard Nixon** — "I am not a crook" — false / Watergate
2. **Bill Clinton** — "I did not have sexual relations..." — false / admitted
3. **Lance Armstrong** — "I have never doped" — false / confessed
4. **Elizabeth Holmes** — Theranos efficacy denial — false / convicted
5. **Sam Bankman-Fried** — FTX / Alameda denial — false / convicted
6. **Frances Haugen** — Facebook whistleblower testimony — sincerity counter-example

If Nixon rPPG is too noisy after 20 minutes, replace with a modern HD false-denial clip. Do not debug Nixon for hours.

---

## Hour-by-Hour Plan

## H0 — Setup + Clip Intake

### Tasks

- Create Python environment.
- Install minimal dependencies:
  - `opencv-python`
  - `numpy`
  - `scipy`
  - `librosa`
  - `soundfile`
  - `yt-dlp`
  - `moviepy` or `ffmpeg-python`
  - `faster-whisper`
  - `openai` or `anthropic`
  - `py-feat` if install works quickly
- Create folders:
  - `data/raw_clips/`
  - `data/processed/`
  - `data/reports/`
  - `scripts/`
- Download or trim the first test clip.
- Confirm JSON schema with Person 2.

### Output

- Environment runs.
- One 10–20 second clip exists locally.
- Person 2 has schema.

---

## H1 — rPPG Preflight

### Tasks

- Implement simplified CHROM rPPG:
  - Detect face ROI.
  - Extract average RGB over cheek/face region per frame.
  - Detrend and normalize RGB channels.
  - Bandpass filter approximately 0.7–3.0 Hz.
  - FFT peak to estimate heart rate.
- Test on Nixon or modern HD clip.

### Decision Gate

- If HR trace is plausible, keep it.
- If HR trace is noisy, use per-clip self-baseline + smoothed color-pulse estimate.
- If archival clip fails, swap it.

### Output

- `extract_rppg.py`
- Real or fallback HR baseline, peak, delta for clip 1

---

## H2 — Facial + Voice + Transcript

### Tasks

- Run Py-Feat for AUs if working:
  - AU15, AU14, AU6, AU24, blink proxies
- If Py-Feat breaks, create deterministic fallback AU estimates based on clip profile and documented as fallback.
- Extract audio with ffmpeg.
- Use librosa for:
  - F0 baseline / peak / delta
  - speech rate approximation
  - jitter/shimmer approximation if possible
- Transcribe with faster-whisper.

### Output

- Full `signals` object for clip 1
- Transcript cleaned enough for LLM

---

## H3 — Scoring + LLM Analyst

### Tasks

- Implement scoring formulas:
  - Deception = weighted HR delta + AU15 + AU14 + F0 delta + jitter + hedging
  - Sincerity = Duchenne/AU6 + low AU14 + pronoun consistency + moderate confidence
  - Stress = HR delta + F0 delta + shimmer + blink/AU tension
  - Confidence = low hedging + stable voice + directness + low suppression
- Clamp scores to 0–100.
- Create LLM prompt.
- Generate first report.

### LLM Style Rules

- Must cite numbers and timestamps.
- Must not say "this person lied."
- Must use cautious language: "signal consistent with," "pattern similar to," "not proof."
- Must include qualifications.

### Output

- `score_clip.py`
- `generate_report.py`
- One complete JSON with LLM report

---

## H4 — Batch Process All 6 Clips

### Tasks

- Run batch processor across all 6 clips.
- Fix any broken JSON.
- Ensure every clip has:
  - metadata
  - signals
  - scores
  - report
  - similar clips
- Export to frontend path or shared folder.

### Output

- `data/processed/all_clips.json`
- `data/processed/nixon_1973.json`, etc.
- Handoff to Person 2

---

## H5 — Data Cleanup + Integration Support

### Tasks

- Check Person 2 frontend with real JSON.
- Fix schema mismatches only.
- Add missing fields if UI needs them.
- Create short `SIGNAL_NOTES.md` explaining real vs fallback signals.

### Output

- Frontend loads real data.
- No broken fields.

---

## H6 — Polish the Data Story

### Tasks

- Improve report language for the 2–3 hero clips.
- Manually tune scores if obviously inconsistent.
- Ensure whistleblower example has high sincerity / low deception.
- Ensure false-denial examples have high deception / lower sincerity.

### Output

- Demo-ready archive data.

---

## H7 — Screen Recording Support

### Tasks

- Help Person 2 capture the best detail pages.
- Keep local backup of JSON files.
- If site breaks, serve static data locally.

### Output

- Screen capture support complete.

---

## H8 — Submission Support

### Tasks

- Stay available for last-minute data edits.
- Do not add new features.
- Help answer technical questions for pitch.

### Output

- Stable final dataset.

---

## Composite Scoring Draft

Use transparent weighted formulas. Keep simple.

```text
Deception =
  0.30 * normalized_hr_delta +
  0.20 * normalized_f0_delta +
  0.15 * au15 +
  0.10 * au14 +
  0.10 * jitter +
  0.10 * hedging +
  0.05 * pronoun_drop

Sincerity =
  0.25 * au6_duchenne +
  0.20 * pronoun_consistency +
  0.20 * specificity +
  0.15 * low_au14 +
  0.10 * moderate_hr +
  0.10 * low_hedging

Stress =
  0.35 * normalized_hr_delta +
  0.25 * normalized_f0_delta +
  0.15 * jitter +
  0.15 * shimmer +
  0.10 * au24

Confidence =
  0.30 * low_hedging +
  0.25 * stable_f0 +
  0.20 * specificity +
  0.15 * low_au24 +
  0.10 * speech_rate_stability
```

---

## LLM Prompt Template

```text
You are VERDICT, a cautious physiological signal analyst for public-interest journalism.

You do not determine truth. You only summarize measured physiological, facial, vocal, and linguistic signals.

Never say: "lying", "guilty", "dishonest", "proved".
Prefer: "signal consistent with", "pattern similar to", "elevated relative to baseline", "not a truth determination".

Given this clip metadata, signals, scores, transcript, and historical comparisons, produce exactly three sections:

1. Behavioral Summary
- Include timestamps where possible.
- Include concrete numbers.
- Mention HR delta, F0 delta, AU15/AU14/AU6/AU24, hedging language.

2. Comparative Profile
- Compare against similar historical archive entries.
- State outcomes only as public record.
- Avoid certainty.

3. Qualifications
- Include signal quality caveat.
- Include that this is not proof of deception.
- Include that physiological arousal can reflect stress, fear, anger, fatigue, or other causes.

INPUT:
{{clip_json}}
```

---

## Fallback Policy

If a signal fails, do not stop the project.

Use this hierarchy:

1. Real extracted value
2. Approximate extracted value
3. Manually estimated value based on known clip profile
4. Clearly marked fallback value

The demo must not claim all values are perfectly measured if fallback was used. The language can say: "prototype signal extraction" and "research demo."

---

## Final Success Criteria

You are done when:

- `all_clips.json` exists
- It contains exactly 6 valid clip objects
- Frontend can render all 6
- Each clip has non-empty LLM report
- Scores look plausible and narratively useful
- Person 2 can film the demo without waiting on you

---

## Emergency Plan

If the pipeline breaks badly:

- Manually create the 6 JSON files with plausible signal values.
- Label the project as a working prototype with simulated signal overlays for the demo.
- Spend remaining time making the frontend and video perfect.

A beautiful, honest prototype beats a broken real pipeline.
