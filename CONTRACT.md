# VERDICT — CONTRACT.md
## The Locked Technical Contract

**Version:** v1.0  
**Status:** Immutable after Phase 0 sign-off.  
**Authority:** This file overrides any conflicting field name, path, or value in `VERDICT.md`, `PERSON1_PIPELINE.md`, or `PERSON2_FRONTEND_PRODUCT.md`.

If `CONTRACT.md` says it, it is true. If it does not say it, it does not exist in this build.

---

## 1. Repo Structure (Locked)

```
verdict/
├── README.md
├── AGENT.md
├── CONTRACT.md
├── TASKS.md
├── VERDICT.md
├── PERSON1_PIPELINE.md
├── PERSON2_FRONTEND_PRODUCT.md
├── .gitignore
├── data/                              # OWNER: Person 1
│   ├── raw_clips/                     # gitignored
│   │   └── <clip_id>.mp4
│   ├── processed/                     # COMMITTED
│   │   ├── all_clips.json             # the handoff artifact
│   │   └── <clip_id>.json
│   └── reports/                       # gitignored, scratch
├── backend/                           # OWNER: Person 1
│   ├── requirements.txt
│   ├── .env                           # gitignored
│   ├── .env.example                   # committed template
│   ├── verdict_pipeline/
│   │   ├── __init__.py
│   │   ├── extract_rppg.py
│   │   ├── extract_facial.py
│   │   ├── extract_voice.py
│   │   ├── transcribe.py
│   │   ├── score.py
│   │   ├── synthesize.py
│   │   └── batch.py
│   ├── scripts/
│   │   ├── download_clip.py
│   │   └── run_one_clip.py
│   └── README.md
└── frontend/                          # OWNER: Person 2
    ├── package.json
    ├── tsconfig.json
    ├── tailwind.config.ts
    ├── next.config.mjs
    ├── .env.local                     # gitignored
    ├── .env.example                   # committed template
    ├── app/
    │   ├── layout.tsx
    │   ├── page.tsx                   # /
    │   ├── archive/
    │   │   ├── page.tsx               # /archive
    │   │   └── [clip_id]/page.tsx     # /archive/[clip_id]
    │   └── calibration/
    │       └── page.tsx               # /calibration
    ├── components/
    │   ├── archive-grid.tsx
    │   ├── clip-card.tsx
    │   ├── score-card.tsx
    │   ├── signal-chart.tsx
    │   ├── analyst-report.tsx
    │   └── ui/                        # shadcn components
    ├── lib/
    │   ├── types.ts                   # mirrors schema below
    │   ├── clips.ts                   # single import surface
    │   └── mock-clips.ts              # mock dataset
    ├── public/
    │   └── data/
    │       └── all_clips.json         # synced from /data/processed
    ├── scripts/
    │   └── sync-data.mjs              # copies data into public/
    └── README.md
```

### Path Constants (Locked)

| Constant | Value |
|---|---|
| `HANDOFF_FILE` | `data/processed/all_clips.json` |
| `FRONTEND_DATA_FILE` | `frontend/public/data/all_clips.json` |
| `MOCK_FILE` | `frontend/lib/mock-clips.ts` |
| `TYPES_FILE` | `frontend/lib/types.ts` |
| `CLIPS_API` | `frontend/lib/clips.ts` |

---

## 2. Locked JSON Schema (v1.0)

The single object shape produced by Person 1 and consumed by Person 2.

```json
{
  "schema_version": "1.0",
  "clip_id": "nixon_1973",
  "subject": "Richard Nixon",
  "statement": "I am not a crook",
  "year": 1973,
  "context": "White House press conference, Orlando, FL",
  "ground_truth": "false",
  "ground_truth_source": "Resigned August 1974; Watergate confirmed",
  "video_url": "https://www.youtube.com/watch?v=...",
  "video_start_seconds": 14,
  "video_end_seconds": 26,
  "thumbnail_url": "https://img.youtube.com/vi/.../hqdefault.jpg",
  "signals": {
    "hr_baseline_bpm": 74,
    "hr_peak_bpm": 94,
    "hr_delta_bpm": 20,
    "hrv_rmssd_ms": 18.4,
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
    "transcript": "I am not a crook. I've earned everything I've got.",
    "timeline": [
      { "t": 0.0,  "hr": 76, "f0": 115, "au15": 0.4, "deception": 28 },
      { "t": 0.5,  "hr": 78, "f0": 119, "au15": 0.7, "deception": 34 }
    ]
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
  "similar_clips": ["clinton_1998", "armstrong_2005"],
  "signal_quality": {
    "rppg": "real",
    "facial_au": "real",
    "voice": "real",
    "transcript": "real"
  }
}
```

### Field Rules (Read Carefully)

| Field | Type | Required | Range / Notes |
|---|---|---|---|
| `schema_version` | string | yes | Always `"1.0"` for this build. |
| `clip_id` | string | yes | Lowercase snake_case. Must be one of the 6 locked IDs (Section 3). |
| `subject` | string | yes | Display name. |
| `statement` | string | yes | The denial sentence shown to the user. |
| `year` | integer | yes | 4-digit. |
| `context` | string | yes | One sentence. |
| `ground_truth` | enum | yes | One of `"true"`, `"false"`, `"sincere"`. |
| `ground_truth_source` | string | yes | Public-record citation. |
| `video_url` | string | yes | YouTube URL preferred. |
| `video_start_seconds` | number | yes | 0+. |
| `video_end_seconds` | number | yes | > start. |
| `thumbnail_url` | string | yes | Public CDN URL. |
| `signals.*` | mixed | yes | All signal fields required even if fallback. |
| `signals.timeline` | array | yes | At least 10 points. Keys: `t`, `hr`, `f0`, `au15`, `deception`. |
| `scores.*` | integer | yes | All four required, **0–100**, integer. |
| `llm_report.*` | string | yes | All three required, plain text or markdown. |
| `similar_clips` | string[] | yes | Other clip_ids; can be empty array. |
| `signal_quality.*` | enum | yes | Each one of `"real"`, `"fallback"`, `"manual"`. |

### Forbidden Renames

These names are **immutable**. Any rename requires both persons to co-sign in `TASKS.md` and bump `schema_version`.

`clip_id`, `signals`, `scores`, `deception`, `sincerity`, `stress`, `confidence`, `llm_report`, `behavioral_summary`, `comparative_profile`, `qualifications`, `signal_quality`.

---

## 3. Locked Clip List

The archive contains exactly **6 clips**. No additions, no removals during the build.

| # | `clip_id` | Subject | Statement (short) | Year | Ground Truth |
|---|---|---|---|---|---|
| 1 | `nixon_1973` | Richard Nixon | "I am not a crook" | 1973 | `false` |
| 2 | `clinton_1998` | Bill Clinton | "I did not have sexual relations..." | 1998 | `false` |
| 3 | `armstrong_2005` | Lance Armstrong | "I have never doped" | 2005 | `false` |
| 4 | `holmes_2018` | Elizabeth Holmes | Theranos efficacy denial | 2018 | `false` |
| 5 | `sbf_2022` | Sam Bankman-Fried | FTX / Alameda denial | 2022 | `false` |
| 6 | `haugen_2021` | Frances Haugen | Whistleblower testimony | 2021 | `sincere` |

If a clip becomes unusable (e.g., archival rPPG fails), Person 1 can swap it **only** with another clip that has clear public ground truth. The new clip_id must be added to this table in the same commit.

---

## 4. Score Definitions (Locked)

All four scores are integers in **0–100**. Higher means more of that quality.

| Score | Meaning |
|---|---|
| `deception` | Signal pattern consistency with historically deceptive denials. |
| `sincerity` | Signal pattern consistency with truthful, vulnerable testimony. |
| `stress` | Physiological arousal independent of valence. |
| `confidence` | Linguistic and vocal directness; absence of hedging. |

Frontend never displays a score outside 0–100. Frontend never invents a fifth score.

---

## 5. Signal Units (Locked)

| Field | Unit |
|---|---|
| `hr_*_bpm` | beats per minute |
| `hrv_rmssd_ms` | milliseconds |
| `f0_*_hz` | hertz |
| `jitter_percent` | percent (0–100) |
| `shimmer_db` | decibels |
| `speech_rate_wpm` | words per minute |
| `au*_max_intensity` | Py-Feat 0–5 scale |
| `au6_present` | boolean |
| `pronoun_drop_rate` | 0.0–1.0 ratio |
| `hedging_count` | integer |
| `timeline.t` | seconds from clip start |

---

## 6. Tech Stack Lock

### Backend (Person 1)

- **Python:** 3.11 or 3.12 (3.10 acceptable)
- **Core libs:** `opencv-python`, `numpy`, `scipy`, `librosa`, `soundfile`, `yt-dlp`, `faster-whisper`, `py-feat`, `openai`, `python-dotenv`
- **Approved additions (Round 1, co-signed):** `imageio-ffmpeg` (bundled ffmpeg binary, no system install), `praat-parselmouth` (Praat-grade jitter/shimmer/HNR), `pydantic>=2` (schema validation), `mediapipe` (FaceMesh for ROI definition — face only, **not pose**), `spacy` + `en_core_web_sm` (linguistic features), `rich` (CLI), `tqdm` (progress), `jsonschema` (output validation).
- **Tooling:** `ruff` for lint
- **No allowed swaps:** no PyTorch model training in foreground (background training tracked in `ML_TRAINING.md` is allowed), **no MediaPipe Pose** (FaceMesh is allowed and explicitly approved above), no OpenFace 2.0 C++ build, no pyVHR.

### Frontend (Person 2)

- **Framework:** Next.js 14 (App Router)
- **Language:** TypeScript strict
- **Styling:** Tailwind CSS
- **Components:** shadcn/ui (Radix primitives)
- **Charts:** Recharts
- **Icons:** Lucide
- **Deploy:** Vercel
- **No allowed swaps:** no Pages Router, no MUI, no Chakra, no Chart.js, no plain CSS modules.

### Optional (only if time)

- Frontend: `framer-motion` for one hero animation.
- Backend: `parselmouth` for jitter/shimmer if `librosa` proxy is too rough.

Adding anything else requires both persons to co-sign in `TASKS.md`.

---

## 7. Environment Variables

### Backend `.env`

```
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o
WHISPER_MODEL=small
```

### Frontend `.env.local`

```
NEXT_PUBLIC_SITE_URL=http://localhost:3000
```

Both `.env.example` files are committed with placeholder values. Real secrets never enter git.

---

## 8. Ports

| Service | Port |
|---|---|
| Frontend dev | `3000` |
| Backend | none (CLI only) |
| Frontend production preview | `3000` |

No other ports may be opened during this build.

---

## 9. Data Refresh Protocol

The exact handoff sequence. Both sides must follow it.

1. Person 1 runs `python -m verdict_pipeline.batch`.
2. Pipeline writes per-clip files and `data/processed/all_clips.json`.
3. Person 1 commits the new JSON on a `data/*` branch and merges to `main`.
4. Person 2 pulls `main`.
5. Person 2 runs `npm run sync-data` (defined in `frontend/package.json`) which executes `node scripts/sync-data.mjs`. The script copies `../data/processed/all_clips.json` to `frontend/public/data/all_clips.json`.
6. Frontend reads from `public/data/all_clips.json` at build time via `lib/clips.ts`.

No live API. No fetch from `localhost`. No CORS.

---

## 10. Mock-to-Real Swap Rule

The frontend contains exactly **one** import surface for clip data: `frontend/lib/clips.ts`.

```ts
// lib/clips.ts
import mock from "./mock-clips";
import type { Clip } from "./types";

export const USE_MOCK = false; // flip to true if real data missing

const real: Clip[] = USE_MOCK
  ? mock
  : (await import("../public/data/all_clips.json")).default as Clip[];

export function getAllClips(): Clip[] { return real; }
export function getClip(id: string): Clip | undefined {
  return real.find(c => c.clip_id === id);
}
```

The swap is one boolean flip. No component imports `mock-clips.ts` or `all_clips.json` directly.

---

## 11. TypeScript Type Mirror

`frontend/lib/types.ts` mirrors the schema. Updated in the same commit as any schema change.

```ts
export type GroundTruth = "true" | "false" | "sincere";
export type SignalQualityFlag = "real" | "fallback" | "manual";

export interface ClipSignals {
  hr_baseline_bpm: number;
  hr_peak_bpm: number;
  hr_delta_bpm: number;
  hrv_rmssd_ms: number;
  au15_max_intensity: number;
  au14_max_intensity: number;
  au6_present: boolean;
  au24_max_intensity: number;
  f0_baseline_hz: number;
  f0_peak_hz: number;
  f0_delta_hz: number;
  jitter_percent: number;
  shimmer_db: number;
  speech_rate_wpm: number;
  hedging_count: number;
  pronoun_drop_rate: number;
  transcript: string;
  timeline: Array<{
    t: number;
    hr: number;
    f0: number;
    au15: number;
    deception: number;
  }>;
}

export interface ClipScores {
  deception: number;
  sincerity: number;
  stress: number;
  confidence: number;
}

export interface ClipReport {
  behavioral_summary: string;
  comparative_profile: string;
  qualifications: string;
}

export interface SignalQuality {
  rppg: SignalQualityFlag;
  facial_au: SignalQualityFlag;
  voice: SignalQualityFlag;
  transcript: SignalQualityFlag;
}

export interface Clip {
  schema_version: "1.0";
  clip_id: string;
  subject: string;
  statement: string;
  year: number;
  context: string;
  ground_truth: GroundTruth;
  ground_truth_source: string;
  video_url: string;
  video_start_seconds: number;
  video_end_seconds: number;
  thumbnail_url: string;
  signals: ClipSignals;
  scores: ClipScores;
  llm_report: ClipReport;
  similar_clips: string[];
  signal_quality: SignalQuality;
}
```

---

## 12. Versioning

- `schema_version` starts at `"1.0"`.
- Bumping requires:
  1. Both persons co-sign in `TASKS.md` `### Schema Changes` section.
  2. The bump and field changes happen in **one** commit.
  3. `lib/types.ts`, all sample data, and any docs are updated in the same commit.

---

## 13. Acknowledgment

Sign off in `TASKS.md`:

- `[ ] BOTH: CONTRACT.md v1.0 reviewed and locked.`

After this, the contract is read-only for the rest of the build.
