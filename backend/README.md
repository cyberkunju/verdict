# VERDICT — Backend (Person 1)

Pipeline that turns a public video clip into a fully-analyzed JSON object
conforming to the schema locked in `../CONTRACT.md` §2.

> Read these first: `../AGENT.md`, `../CONTRACT.md`, `../PERSON1_PIPELINE.md`,
> `../TASKS.md`. If anything in this README contradicts `CONTRACT.md`, the
> contract wins.

---

## What this does

1. Downloads a 10–25s window from a public YouTube clip.
2. Extracts **multi-ROI POS rPPG** → heart rate baseline / peak / delta + HRV.
3. Runs **Py-Feat** for FACS Action Units (AU15, AU14, AU6, AU24).
4. Runs **praat-parselmouth + librosa** for F0, jitter, shimmer, HNR, speech rate.
5. Runs **faster-whisper** for transcript with word-level timestamps.
6. Runs **spaCy linguistic analyzer** for hedging, pronouns, certainty, negation.
7. Computes **composite scores** (deception, sincerity, stress, confidence)
   with **bootstrap 95% CIs** and cross-signal phase synchrony.
8. Calls **OpenAI GPT-4o** with structured outputs to produce the analyst report.
9. Writes JSON to `../data/processed/<clip_id>.json` and `all_clips.json`.

The full architecture is in `verdict_pipeline/` — one focused module per layer.

---

## Project layout

```
backend/
├── requirements.txt
├── .env.example
├── README.md                    # this file
├── verdict_pipeline/
│   ├── __init__.py
│   ├── config.py                # paths, env, constants
│   ├── schema.py                # Pydantic v2 mirror of CONTRACT.md
│   ├── clips.py                 # 6-clip metadata registry
│   ├── utils.py                 # logging, IO, ffmpeg helpers
│   ├── extract_rppg.py          # POS multi-ROI HR + HRV
│   ├── extract_facial.py        # Py-Feat AUs + Duchenne smile detection
│   ├── extract_voice.py         # Parselmouth jitter/shimmer + librosa F0
│   ├── transcribe.py            # faster-whisper transcript + timestamps
│   ├── linguistic.py            # spaCy hedge/pronoun/negation/certainty
│   ├── score.py                 # composite + bootstrap CI + synchrony
│   ├── synthesize.py            # OpenAI structured-output analyst
│   └── batch.py                 # orchestrator over all 6 clips
└── scripts/
    ├── download_clip.py         # yt-dlp wrapper
    ├── run_one_clip.py          # full pipeline on one clip
    └── validate_json.py         # schema sanity check
```

---

## Setup

```powershell
# from /backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
python -m spacy download en_core_web_sm

# create local env file
Copy-Item .env.example .env
# edit .env to set OPENAI_API_KEY
```

---

## Running

### Single clip (smoke test)

```powershell
python -m scripts.run_one_clip nixon_1973
```

### All 6 clips (the handoff to Person 2)

```powershell
python -m verdict_pipeline.batch
```

Output:

- `../data/raw_clips/<clip_id>.mp4`         (gitignored)
- `../data/processed/<clip_id>.json`        (committed, the per-clip artifact)
- `../data/processed/all_clips.json`        (committed, the handoff to frontend)

After `all_clips.json` is updated and pushed, Person 2 runs `npm run sync-data`
in `/frontend` to pull it into `frontend/public/data/`.

---

## Signal quality flags

Each output JSON carries a `signal_quality` block with one of `real | fallback | manual`
per channel. The pipeline never fails silently — if a layer cannot run on a clip
(e.g., archival footage too noisy for rPPG), it logs a warning and downgrades the
flag, but always emits a valid JSON for the frontend.

See `verdict_pipeline/score.py::compute_scores` for how quality flags are
weighted into the composite confidence intervals.

---

## ML training

Background ML training tasks live in `../ML_TRAINING.md`. Foreground training is
forbidden by `AGENT.md` §12. Trained model weights drop into
`backend/models/<name>/` and are wired in via the optional providers in
`extract_*.py` modules.
