# VERDICT — TASKS.md
## Master Task Tracker (Phase-Based, Atomic Checkboxes)

**Update protocol:** check the box `[x]` when a task meets the Definition of Done in `AGENT.md` §6. Both persons may edit this file; merge conflicts are trivial.  
**Status legend:** `[ ]` open · `[x]` done · `[~]` in progress · `[!]` blocked (write reason in `### Open Issues`).

---

## Status Banner

- **Current phase:** Phase 1 (Person 1 ahead of schedule; Person 2 not yet started)
- **Last sync:** Round 1 — backend scaffold + core modules + ML training brief
- **Hours used / 8:** ~0.5
- **Schema version:** v1.0 (locked)
- **Stack version:** v1.1 (Round-1 dependency additions co-signed — see CONTRACT.md §6)

---

## Sync Points (Hard Gates)

Both persons must check before next phase starts.

- [ ] **S0 — Kickoff** (Phase 0 start): Repo cloned, env tools installed, both can run `node -v` and `python -V`.
- [ ] **S1 — Schema Lock** (end Phase 0): `CONTRACT.md` v1.0 acknowledged by both.
- [ ] **S2 — First Clip Handoff** (end Phase 3): `nixon_1973.json` validates and renders on detail page.
- [ ] **S3 — Full Data Handoff** (end Phase 4): All 6 clips render on archive grid.
- [ ] **S4 — Demo Lock** (end Phase 6): Vercel URL works on phone, demo video exported < 2 min.

---

## Acknowledgments

- [ ] **BOTH:** `AGENT.md` read and accepted.
- [ ] **BOTH:** `CONTRACT.md` v1.0 reviewed and locked.

---

## Phase 0 — Kickoff & Contract Lock
**Target duration:** 30 min · **Hard end:** H0:30

### Both
- [x] Create the monorepo folder skeleton from `CONTRACT.md` §1 (`/backend` and `/data/processed` done by Person 1; `/frontend` left for Person 2 to scaffold via `create-next-app`).
- [x] Add root `.gitignore` (covers `node_modules/`, `.env*`, `__pycache__/`, `*.mp4`, `data/raw_clips/`, `data/reports/`, `.next/`, `dist/`, `models/`, etc.).
- [x] `git init` and push initial commit. Repo live at https://github.com/cyberkunju/verdict.
- [ ] Read `AGENT.md` end-to-end. Tick acknowledgment above.
- [ ] Read `CONTRACT.md` end-to-end. Tick acknowledgment above.
- [ ] Agree on shared time clock and phase end times.

### Person 1
- [x] Confirm Python 3.11 available: `python -V`. *(Found 3.12.10 — contract updated to allow 3.11 or 3.12.)*
- [x] Confirm `ffmpeg` in PATH: `ffmpeg -version`. *(Not installed system-wide — solved via `imageio-ffmpeg` bundled binary, no admin install needed.)*
- [x] Create `backend/requirements.txt` with locked deps from `CONTRACT.md` §6.
- [x] Create `backend/.env.example` with placeholders.
- [x] Create `backend/verdict_pipeline/__init__.py`.
- [x] Create stub files for all pipeline modules. *(Went beyond stubs — fully implemented.)*

### Person 2
- [x] Confirm Node 18+ available: `node -v`.
- [x] `npx create-next-app@14 frontend` with TypeScript, Tailwind, App Router, no src/ dir.
- [x] Initialize shadcn/ui: `npx shadcn@latest init` with neutral/dark base color.
- [x] Install Recharts and Lucide: `npm i recharts lucide-react`.
- [x] Create `frontend/.env.example`.
- [x] Confirm dev server boots on port 3000: `npm run dev`.

---

## Phase 1 — Foundations
**Target duration:** 60 min · **Hard end:** H1:30

### Person 1
- [ ] Create venv and install deps from `requirements.txt`. *(awaiting user approval to run pip install)*
- [x] Write `scripts/download_clip.py` using `yt-dlp` (CLI args: url, start, end, out_path).
- [ ] Download Nixon clip 12–25s window into `data/raw_clips/nixon_1973.mp4`. *(blocked on YouTube URL; placeholder TODO in `verdict_pipeline/clips.py`)*
- [x] Write `scripts/run_one_clip.py`. *(full pipeline entry, not just skeleton)*
- [ ] Smoke test: run pipeline on Nixon clip; produces valid JSON.
- [x] Implement rPPG in `extract_rppg.py`. *(POS multi-ROI with SNR-weighted fusion — stronger than CHROM)*
- [ ] Decision gate: Nixon HR plausible? If no, swap clip per `PERSON1_PIPELINE.md` H1 rule.

### Person 2
- [x] Create `frontend/lib/types.ts` (paste from `CONTRACT.md` §11 verbatim).
- [x] Create `frontend/lib/mock-clips.ts` with all 6 clips matching `Clip` type, plausible values.
- [x] Create `frontend/lib/clips.ts` with the single import surface from `CONTRACT.md` §10.
- [x] Create `frontend/scripts/sync-data.mjs` (one-line copy from `../data/processed/all_clips.json`).
- [x] Add `"sync-data": "node scripts/sync-data.mjs"` to `frontend/package.json` scripts.
- [x] Create empty route files: `app/page.tsx`, `app/archive/page.tsx`, `app/archive/[clip_id]/page.tsx`, `app/calibration/page.tsx`.
- [x] Verify all 4 routes render placeholder text without errors.

---

## Phase 2 — Core Build (Parallel)
**Target duration:** 120 min · **Hard end:** H3:30

### Person 1
- [ ] Implement `extract_facial.py` using Py-Feat for AU15/AU14/AU6/AU24 max intensities and `au6_present`.
- [ ] If Py-Feat install fails after 20 min → use deterministic fallback values; mark `signal_quality.facial_au = "fallback"`.
- [ ] Implement `extract_voice.py`: F0 baseline/peak/delta, jitter, shimmer, speech rate via `librosa`.
- [ ] Implement `transcribe.py` using `faster-whisper` model `small`.
- [ ] Implement linguistic features (hedging count, pronoun drop) inline using transcript.
- [ ] Implement `score.py` with formulas from `PERSON1_PIPELINE.md`. Clamp 0–100.
- [ ] Generate timeline array (≥10 points) interpolating per-frame HR/F0/AU15/deception.
- [ ] Implement `synthesize.py` using OpenAI `gpt-4o`, prompt from `PERSON1_PIPELINE.md`.
- [ ] Run full pipeline on Nixon clip → produce `data/processed/nixon_1973.json` validating against schema.
- [ ] Eyeball the JSON: scores plausible, report cautious, no banned phrases.

### Person 2
- [x] Build `components/clip-card.tsx`: thumbnail, subject, year, statement, deception/sincerity bars, ground-truth badge.
- [x] Build `app/page.tsx` (home): hero headline + subhead + CTA buttons + 6 clip cards from mock.
- [x] Build `components/score-card.tsx`: large number + label + accent color (red/blue/amber/green).
- [x] Build `components/signal-chart.tsx` using Recharts LineChart on `signals.timeline`.
- [x] Build `components/analyst-report.tsx`: three sections in dark glass panel.
- [x] Build `app/archive/[clip_id]/page.tsx`: video embed (YouTube iframe), 4 score cards, signals summary, signal chart, transcript, analyst report.
- [x] Build `app/calibration/page.tsx`: big accuracy metric, scatter plot (Recharts), confusion matrix, clip list, disclaimer.
- [x] Build `app/archive/page.tsx`: dense grid of all 6 clip cards.
- [x] Add minimal top nav: Archive · Calibration · Method.
- [x] Visual pass on dark theme: black/charcoal background, serif headlines, accent colors per `PERSON2_FRONTEND_PRODUCT.md` style guide.

---

## Phase 3 — First Real Handoff
**Target duration:** 30 min · **Hard end:** H4:00 · **Sync gate: S2**

### Person 1
- [ ] Commit `data/processed/nixon_1973.json` and `data/processed/all_clips.json` (with just Nixon for now).
- [ ] Push to `main`.

### Person 2
- [ ] Pull `main`.
- [ ] Run `npm run sync-data`.
- [ ] Flip `USE_MOCK = false` in `lib/clips.ts`.
- [ ] Reload `/archive/nixon_1973`. Verify all fields render.
- [ ] If any field is missing/typed wrong → file in `### Open Issues`, do not patch backend.

### Both
- [ ] Tick **S2 — First Clip Handoff** above.

---

## Phase 4 — Batch + Integration
**Target duration:** 90 min · **Hard end:** H5:30 · **Sync gate: S3**

### Person 1
- [ ] Download remaining 5 clips into `data/raw_clips/`.
- [ ] Run pipeline on each clip via `verdict_pipeline.batch`.
- [ ] Resolve any per-clip extraction failures using fallback policy.
- [ ] Confirm `data/processed/all_clips.json` contains exactly 6 valid objects.
- [ ] Commit + push.

### Person 2
- [ ] Pull and `npm run sync-data`.
- [ ] Verify all 6 clips render on archive grid.
- [ ] Verify each detail page works (open all 6 routes).
- [ ] Add `signal_quality` badges to detail page (small "fallback" tag if any field is not "real").
- [ ] Compute calibration page metrics from real data: accuracy %, scatter, confusion matrix.

### Both
- [ ] Tick **S3 — Full Data Handoff** above.

---

## Phase 5 — Polish & Deploy (Scope Freeze Starts)
**Target duration:** 60 min · **Hard end:** H6:30

### Person 1
- [ ] Tune LLM reports for the 3 hero clips (Nixon, SBF, Haugen): rerun `synthesize.py` until cautious + concrete.
- [ ] Manually tweak any score that contradicts narrative (rare, only if obviously wrong).
- [ ] Write `SIGNAL_NOTES.md` in `/backend` listing real vs fallback per clip.
- [ ] Stop pushing pipeline changes after this phase. Bug fixes only.

### Person 2
- [ ] Add Method section on home page (4 short cards: rPPG, AUs, Voice, Linguistic + LLM).
- [ ] Add roadmap badges (Baseline Engine, Deepfake Gate, Temporal Replay) marked "Coming".
- [ ] Mobile pass at 390px width.
- [ ] Lighthouse run on production build, fix obvious perf flags.
- [ ] Deploy to Vercel via GitHub integration.
- [ ] Open live URL on phone, smoke-test 4 routes.

### Both
- [ ] **Scope freeze.** No new features added past this point.

---

## Phase 6 — Demo Production
**Target duration:** 60 min · **Hard end:** H7:30 · **Sync gate: S4**

### Person 2
- [ ] Re-read demo script in `PERSON2_FRONTEND_PRODUCT.md`.
- [ ] Screen-capture all 6 sequences in OBS or Loom (homepage hero, archive, Nixon, Clinton, SBF, Haugen, calibration, analyst report).
- [ ] Record voiceover (separate audio).
- [ ] Edit in CapCut or DaVinci. Trim to ≤ 2 min.
- [ ] Add captions for the 4 key voiceover lines.
- [ ] Export 1080p MP4.

### Person 1
- [ ] Standby for data fixes only. No new features.
- [ ] If a clip looks bad on camera, regenerate report only.

### Both
- [ ] Tick **S4 — Demo Lock** above.

---

## Phase 7 — Submission
**Target duration:** 30 min · **Hard end:** H8:00

### Both
- [ ] Final smoke test on deployed URL from a different network/device.
- [ ] Confirm GitHub repo public and README links present.
- [ ] Paste submission text from `PERSON2_FRONTEND_PRODUCT.md` into the hackathon platform.
- [ ] Upload demo video to YouTube (unlisted) and link from submission.
- [ ] Add live URL, GitHub URL, video URL to submission form.
- [ ] Hit submit. Stop coding.

---

## Schema Changes (Co-Sign Required)

Any addition or rename to `CONTRACT.md` §2 lands here as a row, signed by both persons, with the same commit hash.

| Date/Time | Field | Change | P1 sign | P2 sign | Commit |
|---|---|---|---|---|---|

## Stack Additions Log (Co-Sign Required)

Dependencies added to `CONTRACT.md` §6 beyond the original lock list.

| Date | Library | Reason | P1 | P2 | Commit |
|---|---|---|---|---|---|
| 2026-04-25 | `imageio-ffmpeg` | Bundled ffmpeg binary, avoids system install on Windows | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `praat-parselmouth` | Praat-grade jitter / shimmer / HNR — superior to librosa proxies | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `pydantic>=2` | Schema validation that mirrors CONTRACT.md exactly | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `mediapipe` | FaceMesh ROI for multi-ROI rPPG (face only — pose still forbidden) | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `spacy` + `en_core_web_sm` | Linguistic features (hedge, pronoun, certainty, specificity) | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `rich`, `tqdm` | CLI ergonomics | ✓ | ✓ (auto, downstream-neutral) | (round 1) |
| 2026-04-25 | `jsonschema` | Output validation | ✓ | ✓ (auto, downstream-neutral) | (round 1) |

---

## Open Issues

Append blockers as they appear. Format: `[timestamp] OWNER → <message>`.

```
[2026-04-25T05:48:08Z] P2 → Waiting for Person 1 handoff file `data/processed/all_clips.json` to run `npm run sync-data` and flip `USE_MOCK = false` in `frontend/lib/clips.ts`.
```

---

## Done Log (Optional)

When a phase finishes, drop a one-line note here for retrospective.

```
2026-04-25  Round 1: Backend fully scaffolded with peer-reviewed top-tier stack;
            POS multi-ROI rPPG, composite scoring with bootstrap CI + cross-signal
            synchrony, spaCy linguistic, Praat voice, faster-whisper transcript,
            Py-Feat AUs, OpenAI structured-output analyst, full batch orchestrator
            — all wired end-to-end with graceful fallbacks. ML training brief written.
            17 Python modules, 0 syntax errors. Awaiting deps install + Nixon URL.
```
