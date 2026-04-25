# VERDICT — TASKS.md
## Master Task Tracker (Phase-Based, Atomic Checkboxes)

**Update protocol:** check the box `[x]` when a task meets the Definition of Done in `AGENT.md` §6. Both persons may edit this file; merge conflicts are trivial.  
**Status legend:** `[ ]` open · `[x]` done · `[~]` in progress · `[!]` blocked (write reason in `### Open Issues`).

---

## Status Banner

- **Current phase:** Phase 0
- **Last sync:** —
- **Hours used / 8:** 0
- **Schema version:** v1.0 (locked)

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
- [ ] Create the monorepo folder skeleton from `CONTRACT.md` §1 (empty `/backend`, `/frontend`, `/data/raw_clips`, `/data/processed`, `/data/reports`).
- [ ] Add root `.gitignore` (covers `node_modules/`, `.env*`, `__pycache__/`, `*.mp4`, `data/raw_clips/`, `data/reports/`, `.next/`, `dist/`).
- [ ] `git init` if not already, first commit: `chore(infra): scaffold repo`.
- [ ] Read `AGENT.md` end-to-end. Tick acknowledgment above.
- [ ] Read `CONTRACT.md` end-to-end. Tick acknowledgment above.
- [ ] Agree on shared time clock and phase end times.

### Person 1
- [ ] Confirm Python 3.11 available: `python -V`.
- [ ] Confirm `ffmpeg` in PATH: `ffmpeg -version`.
- [ ] Create `backend/requirements.txt` with locked deps from `CONTRACT.md` §6.
- [ ] Create `backend/.env.example` with placeholders.
- [ ] Create `backend/verdict_pipeline/__init__.py` (empty).
- [ ] Create empty stub files: `extract_rppg.py`, `extract_facial.py`, `extract_voice.py`, `transcribe.py`, `score.py`, `synthesize.py`, `batch.py` (each with module docstring).

### Person 2
- [ ] Confirm Node 18+ available: `node -v`.
- [ ] `npx create-next-app@14 frontend` with TypeScript, Tailwind, App Router, no src/ dir.
- [ ] Initialize shadcn/ui: `npx shadcn@latest init` with neutral/dark base color.
- [ ] Install Recharts and Lucide: `npm i recharts lucide-react`.
- [ ] Create `frontend/.env.example`.
- [ ] Confirm dev server boots on port 3000: `npm run dev`.

---

## Phase 1 — Foundations
**Target duration:** 60 min · **Hard end:** H1:30

### Person 1
- [ ] Create venv and install deps from `requirements.txt`.
- [ ] Write `scripts/download_clip.py` using `yt-dlp` (CLI args: url, start, end, out_path).
- [ ] Download Nixon clip 12–25s window into `data/raw_clips/nixon_1973.mp4`.
- [ ] Write `scripts/run_one_clip.py` skeleton (loads clip, calls each extractor stub, writes JSON).
- [ ] Smoke test: run skeleton on Nixon clip; produces empty-but-valid JSON shell.
- [ ] Implement minimum CHROM rPPG in `extract_rppg.py` (ROI → RGB mean → bandpass → FFT peak).
- [ ] Decision gate: Nixon HR plausible? If no, swap clip per `PERSON1_PIPELINE.md` H1 rule.

### Person 2
- [ ] Create `frontend/lib/types.ts` (paste from `CONTRACT.md` §11 verbatim).
- [ ] Create `frontend/lib/mock-clips.ts` with all 6 clips matching `Clip` type, plausible values.
- [ ] Create `frontend/lib/clips.ts` with the single import surface from `CONTRACT.md` §10.
- [ ] Create `frontend/scripts/sync-data.mjs` (one-line copy from `../data/processed/all_clips.json`).
- [ ] Add `"sync-data": "node scripts/sync-data.mjs"` to `frontend/package.json` scripts.
- [ ] Create empty route files: `app/page.tsx`, `app/archive/page.tsx`, `app/archive/[clip_id]/page.tsx`, `app/calibration/page.tsx`.
- [ ] Verify all 4 routes render placeholder text without errors.

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
- [ ] Build `components/clip-card.tsx`: thumbnail, subject, year, statement, deception/sincerity bars, ground-truth badge.
- [ ] Build `app/page.tsx` (home): hero headline + subhead + CTA buttons + 6 clip cards from mock.
- [ ] Build `components/score-card.tsx`: large number + label + accent color (red/blue/amber/green).
- [ ] Build `components/signal-chart.tsx` using Recharts LineChart on `signals.timeline`.
- [ ] Build `components/analyst-report.tsx`: three sections in dark glass panel.
- [ ] Build `app/archive/[clip_id]/page.tsx`: video embed (YouTube iframe), 4 score cards, signals summary, signal chart, transcript, analyst report.
- [ ] Build `app/calibration/page.tsx`: big accuracy metric, scatter plot (Recharts), confusion matrix, clip list, disclaimer.
- [ ] Build `app/archive/page.tsx`: dense grid of all 6 clip cards.
- [ ] Add minimal top nav: Archive · Calibration · Method.
- [ ] Visual pass on dark theme: black/charcoal background, serif headlines, accent colors per `PERSON2_FRONTEND_PRODUCT.md` style guide.

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

---

## Open Issues

Append blockers as they appear. Format: `[timestamp] OWNER → <message>`.

```
(empty)
```

---

## Done Log (Optional)

When a phase finishes, drop a one-line note here for retrospective.

```
(empty)
```
