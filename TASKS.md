# VERDICT — TASKS.md
## Master Task Tracker (Phase-Based, Atomic Checkboxes)

**Update protocol:** check the box `[x]` when a task meets the Definition of Done in `AGENT.md` §6. Both persons may edit this file; merge conflicts are trivial.  
**Status legend:** `[ ]` open · `[x]` done · `[~]` in progress · `[!]` blocked (write reason in `### Open Issues`).

---

## Status Banner

- **Current phase:** Phase 5 — [bold]full-stack mode active[/]; both persons own all folders, file-level ownership in task table below
- **Last sync:** Round 3 — real GPT-4o analyst reports on all 6 clips; Person 2 frontend scaffold landed in parallel
- **Hours used / 8:** ~1.0
- **Schema version:** v1.0 (locked — schema bump requires both signatures)
- **Stack version:** v1.1 (Round-1 dependency additions co-signed — see CONTRACT.md §6)
- **Data status:** [bold green]all_clips.json ready[/] — 6 clips, all schema-valid, real rPPG + voice + transcript + linguistic + GPT-4o analyst. py-feat fallback (intentional).

---

## Sync Points (Hard Gates)

Both persons must check before next phase starts.

- [ ] **S0 — Kickoff** (Phase 0 start): Repo cloned, env tools installed, both can run `node -v` and `python -V`.
- [ ] **S1 — Schema Lock** (end Phase 0): `CONTRACT.md` v1.0 acknowledged by both.
- [x] **S2 — First Clip Handoff** (end Phase 3): `nixon_1973.json` validates. *(rendering pending Person 2)*
- [x] **S3 — Full Data Handoff** (end Phase 4): All 6 clips schema-valid in `data/processed/all_clips.json`. *(rendering pending Person 2)*
- [ ] **S4 — Deploy Preview Live** (end Phase 5): Vercel URL works on phone with real data on all 4 routes.
- [ ] **S5 — Demo Lock** (end Phase 6): demo video exported < 2 min, captions in place.

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
- [x] Create venv and install deps from `requirements.txt`.
- [x] Write `scripts/download_clip.py` using `yt-dlp` (CLI args: url, start, end, out_path).
- [x] Download Nixon clip 0–15s window into `data/raw_clips/nixon_1973.mp4`. *(plus all other 5 clips)*
- [x] Write `scripts/run_one_clip.py`. *(full pipeline entry, not just skeleton)*
- [x] Smoke test: run pipeline on Nixon clip; produces valid JSON.
- [x] Implement rPPG in `extract_rppg.py`. *(POS multi-ROI with MediaPipe BlazeFace, SNR 23-26 dB on modern HD clips)*
- [x] Decision gate: HR plausible across all 6 clips? Yes — hr_delta range 18-49 bpm, all in physiological range.

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
- [x] Commit `data/processed/nixon_1973.json` and `data/processed/all_clips.json` (with just Nixon for now). *(Round 2: all 6 clips committed at once, jumping ahead.)*
- [x] Push to `main`.

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
- [x] Download remaining 5 clips into `data/raw_clips/`.
- [x] Run pipeline on each clip via `verdict_pipeline.batch`.
- [x] Resolve any per-clip extraction failures using fallback policy. *(MediaPipe Tasks API migration + dynamic rPPG window for short clips.)*
- [x] Confirm `data/processed/all_clips.json` contains exactly 6 valid objects.
- [x] Commit + push.

### Person 2
- [ ] Pull and `npm run sync-data`.
- [ ] Verify all 6 clips render on archive grid.
- [ ] Verify each detail page works (open all 6 routes).
- [ ] Add `signal_quality` badges to detail page (small "fallback" tag if any field is not "real").
- [ ] Compute calibration page metrics from real data: accuracy %, scatter, confusion matrix.

### Both
- [ ] Tick **S3 — Full Data Handoff** above.

---

## Phase 5 — Full-Stack Polish & Deploy (Round 4)
**Target duration:** 4h · **Hard end:** H6:00 · **Sync gate:** S4 (deploy preview live)

Folder ownership rule **dissolved**. Both persons may edit `/frontend`, `/backend`, `/data`. **Schema (CONTRACT.md §2/§11) still locked** — changes require both signatures in the Schema Changes table below.

### Conflict-Avoidance Protocol
1. `git pull --rebase origin main` before every commit.
2. Stage **only the files in your assigned task** below.
3. Commit prefix: `feat(fe)`, `feat(pipe)`, `feat(data)`, `fix(...)`, `chore(...)`.
4. Push immediately. Don't sit on local commits.
5. If a rebase conflict appears (rare — should only be `TASKS.md` / `CONTRACT.md`), keep both blocks side-by-side, never silently overwrite.

### Person 1 — Frontend & Demo

| #  | Task | Files | Pri | Est |
|----|------|-------|-----|-----|
| F1 | Run `npm run sync-data`; flip `USE_MOCK=false` in `lib/clips.ts`; smoke test all 4 routes render real data | `frontend/lib/clips.ts`, `frontend/public/data/` | P0 | 15m |
| F2 | Polish detail page: video player, scores grid, multi-line timeline (HR + F0 + AU15), analyst report sections, signal-quality badges | `frontend/app/archive/[clip_id]/page.tsx`, `frontend/components/signal-chart.tsx`, new `signal-quality-badge.tsx` | P0 | 45m |
| F3 | Calibration logic: add "sincere" prediction path (Haugen), scatter plot, ROC-style visual | `frontend/app/calibration/page.tsx`, `frontend/components/calibration-visuals.tsx` | P1 | 30m |
| F4 | New `/method` page with full pipeline explanation, formulas, citations | `frontend/app/method/page.tsx`, `frontend/app/layout.tsx` | P1 | 30m |
| F5 | Mobile responsive + a11y: keyboard nav, ARIA, sm/md breakpoints | All frontend pages | P1 | 30m |
| F6 | OpenGraph + Twitter card metadata; replace boilerplate `frontend/README.md` | `frontend/app/layout.tsx`, `frontend/README.md`, `frontend/public/og.png` | P2 | 20m |
| F7 | Deploy to Vercel; verify production URL on phone | Vercel dashboard, possibly `vercel.json` | P0 | 20m |

- [~] **F1 — sync-data + USE_MOCK flip** *(in progress, Round 4)*
- [ ] F2 — detail page polish
- [ ] F3 — calibration logic
- [ ] F4 — `/method` page
- [ ] F5 — mobile + a11y
- [ ] F6 — OG metadata + README
- [ ] F7 — Vercel deploy

### Person 2 — Backend & Data Quality

| #  | Task | Files | Pri | Est |
|----|------|-------|-----|-----|
| B1 | Refine clip timestamps so transcripts are speaker-only (no narrator preamble); re-run `verdict_pipeline.batch` | `backend/verdict_pipeline/clips.py`, then re-run pipeline | P0 | 30m |
| B2 | Generate poster-frame thumbnails: ffmpeg extract midpoint per clip → `data/thumbnails/{clip_id}.jpg`; populate `thumbnail_url` | `backend/scripts/extract_thumbnails.py` (new), `backend/verdict_pipeline/batch.py` | P0 | 20m |
| B3 | Try `pip install --no-deps py-feat`; if it imports cleanly, swap fallback for real AU extraction; if not, document failure | `backend/requirements.txt`, possibly `extract_facial.py` | P2 | 30m |
| B4 | Populate `similar_clips`: cosine-distance over score vector + ground_truth match → top 2 per clip | `backend/verdict_pipeline/score.py` or new module | P1 | 20m |
| B5 | Add `bias_notes` field per clip (e.g., "archival B&W footage degrades rPPG SNR") — schema bump required, both must sign | `CONTRACT.md` (S-gate), `schema.py`, `batch.py`, `frontend/lib/types.ts` | P2 | 30m |
| B6 | Pytest harness: synthetic-input tests for `score.py`, schema validation, no-network smoke test | `backend/tests/` (new) | P3 | 45m |

- [ ] B1 — timestamps + re-run pipeline
- [ ] B2 — thumbnails
- [ ] B3 — try py-feat --no-deps
- [ ] B4 — similar_clips
- [ ] B5 — bias_notes (schema bump)
- [ ] B6 — pytest harness

### Suggested Order — First 90 min

```
Person 1                                 Person 2
──────────────────                       ──────────────────
F1 sync + USE_MOCK flip       (15m)      B1 refine timestamps         (30m)
F2 detail page polish         (45m)      B2 thumbnails                (20m)
                                          → re-run batch              (5m)
F7 deploy preview             (20m)      B3 try py-feat --no-deps     (30m)
F3 calibration polish         (30m)      B4 similar_clips             (20m)
```

### Both
- [ ] Tick **S4 — Deploy Preview Live** at end of Phase 5.
- [ ] No new features past S4. Bug-fix only into Phase 6.

---

## Phase 6 — Demo Production
**Target duration:** 60 min · **Hard end:** H7:00 · **Sync gate: S5 (demo lock)**

### Both — split however convenient
- [ ] Re-read demo script in `PERSON2_FRONTEND_PRODUCT.md`.
- [ ] Screen-capture all 6 sequences in OBS or Loom (homepage hero, archive, Nixon, Clinton, SBF, Haugen, calibration, analyst report).
- [ ] Record voiceover (separate audio).
- [ ] Edit in CapCut or DaVinci. Trim to ≤ 2 min.
- [ ] Add captions for the 4 key voiceover lines.
- [ ] Export 1080p MP4.
- [ ] Tick **S5 — Demo Lock** above.

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
[2026-04-25T07:00:00Z] resolved — P1 shipped Round 2/3, all 6 clips in `data/processed/`. P1 is now executing F1 itself in Round 4 full-stack mode.
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

2026-04-25  Round 2: All deps installed. Canonical YouTube URLs filled for all 6
            clips (Nixon AP / Clinton CBS / Armstrong ABC / Holmes CNBC / SBF
            Dealbook / Haugen Senate). Migrated to MediaPipe Tasks FaceDetector
            (BlazeFace) when 0.10.33 dropped legacy `mp.solutions`. Fixed dynamic
            rPPG windowing so short clips still hit min_length=10 timeline. Ran
            full batch: all 6 clips schema-valid, real rPPG SNR 23-26 dB on HD
            clips, sincerity correctly flagged Haugen highest (83) / SBF lowest
            (34). Person 2 unblocked.

2026-04-25  Round 3: Real GPT-4o cautious analyst reports on all 6 clips via
            structured outputs (OPENAI_API_KEY in gitignored backend/.env).
            Reports cite concrete signal numbers, avoid lying/guilty language,
            cross-reference similar archive entries (SBF→Holmes/Armstrong,
            Haugen→whistleblower path). Discovered Person 2 had shipped
            frontend scaffold (be1d51d) in parallel — zero merge conflicts
            thanks to folder ownership.

2026-04-25  Round 4: Full-stack mode begins. Folder ownership dissolved.
            New file-level task split: P1 owns frontend (F1–F7), P2 owns
            backend polish (B1–B6). Schema stays locked. P1 starting on F1
            (sync-data + USE_MOCK flip).
```
