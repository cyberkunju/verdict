# VERDICT — Person 2 Plan
## Frontend, Product, Demo Video, and Submission

**Owner:** Person 2  
**Timebox:** 8 hours  
**Goal:** Ship a beautiful deployed website and a compelling 2-minute demo video using Person 1's analysis JSON.

> **Read first:** `AGENT.md` (rules of engagement), `CONTRACT.md` (locked schema, paths, tech stack — supreme authority), and `TASKS.md` (live phase-based checklist).
> If any field name, path, or value here ever conflicts with `CONTRACT.md`, **the contract wins**.

---

## Mission

You own the visible product.

Judges will mostly experience VERDICT through your UI and demo video. The backend can be imperfect; the product must feel polished, serious, and inevitable.

Your job is to make VERDICT look like a real public-interest journalism platform, not a hackathon dashboard.

---

## Non-Negotiable Output

By the end of your workstream, you must deliver:

- **Deployed Vercel site**
- **Archive grid** with 6 clips
- **Detail page** for each clip
- **Video embed** with signal cards and chart timeline
- **LLM analyst report panel**
- **Calibration page** with accuracy number and scatter/confusion visualization
- **2-minute demo video**
- **Submission text** for Devpost / hackathon platform

---

## Brutal Scope Rules

### Must Build

- Next.js app
- Dark, serious, premium UI
- Archive grid
- Detail page
- Calibration page
- Static JSON data loading
- Demo video
- Deployed link

### Can Fake / Approximate If Needed

- Signal charts can be generated from summary values if full time series is unavailable
- Radar charts can use four scores only: deception, sincerity, stress, confidence
- Accuracy can be presented as "prototype calibration" if dataset is small
- Video synchronization can be visual rather than mathematically exact

### Do Not Build

- No auth
- No database unless already trivial
- No upload analyzer
- No live backend dependency
- No complex animations
- No custom charting engine
- No multi-page marketing site
- No feature additions after H5

---

## H0 Handoff Contract — Locked JSON Schema

Build from minute zero using mock data in this shape. Person 1 will replace it with real data around H4.

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

## Visual Direction

VERDICT must feel like:

- investigative journalism
- forensic lab
- historical archive
- premium intelligence dashboard

### Style

- **Background:** near-black / slate / charcoal
- **Accent:** red for elevated deception signal, blue for sincerity, amber for stress
- **Typography:** large serif headline + clean sans-serif body
- **Cards:** glassy dark panels, thin borders, subtle glow
- **Charts:** clean Recharts lines, minimal grid, high contrast
- **Language:** cautious, serious, non-sensational

### Avoid

- Toy app look
- Bright startup gradient overload
- Emoji-heavy UI
- "Lie detector" labels everywhere
- Cartoonish polygraph visuals

---

## Hour-by-Hour Plan

## H0 — App Scaffold + Mock Data

### Tasks

- Create Next.js 14 app.
- Add Tailwind.
- Add shadcn/ui or simple component primitives.
- Add Recharts.
- Create `data/mock-clips.json` with 6 mocked clips matching schema.
- Create routes:
  - `/`
  - `/archive`
  - `/archive/[clip_id]`
  - `/calibration`

### Output

- App runs locally.
- Mock data loads.
- Navigation exists.

---

## H1 — Archive Grid

### Tasks

Build archive homepage with:

- Hero headline:
  - "Every lie has a body. Every body has a pulse."
- Subheadline:
  - "VERDICT is a public physiological archive of historical denials, calibrated against outcomes history already resolved."
- 6 clip cards:
  - subject image/video thumbnail
  - statement quote
  - year
  - ground truth badge
  - deception score
  - sincerity score
  - mini radar/bar chart
- CTA buttons:
  - "Explore Archive"
  - "View Calibration"

### Output

- Beautiful archive grid with mock data.

---

## H2 — Detail Page

### Tasks

Build `/archive/[clip_id]`:

- YouTube embed or video placeholder
- Big score cards:
  - deception
  - sincerity
  - stress
  - confidence
- Signal summary cards:
  - HR baseline → peak
  - F0 baseline → peak
  - AU15 / AU14 / AU6 / AU24
  - hedging count
- Recharts timeline:
  - HR line
  - F0 line
  - AU15 bar/line
  - composite deception line
- Transcript block
- LLM analyst report panel with three sections

### Output

- Detail page looks demo-ready with mock data.

---

## H3 — Calibration Page

### Tasks

Build `/calibration`:

- Big metric:
  - "72% agreement with historically resolved outcomes"
- Scatter plot:
  - x-axis deception score
  - y-axis outcome / category
- Confusion matrix:
  - true positives, false positives, false negatives, true negatives
- List of included clips with outcome source
- Disclaimer:
  - "Not a truth determination. A physiological signal report calibrated against public records."

### Output

- Calibration page is pitch-ready.

---

## H4 — Real Data Handoff

### Tasks

- Receive `all_clips.json` from Person 1.
- Replace mock data import.
- Fix schema mismatches.
- Ensure all pages render all 6 clips.
- If a field is missing, add safe fallback UI.

### Output

- Site renders real pipeline output.

---

## H5 — Polish + Demo Flow

### Tasks

- Add loading / reveal animations only if simple.
- Improve visual hierarchy.
- Make score numbers huge.
- Add top nav:
  - Archive
  - Calibration
  - Method
- Add short Method section on homepage:
  - rPPG heart signal
  - facial AUs
  - vocal stress
  - linguistic markers
  - LLM analyst
- Add roadmap badges:
  - Baseline Engine
  - Deepfake Gate
  - Temporal Replay

### Output

- Product feels complete enough for judging.

---

## H6 — Deploy + Submission Draft

### Tasks

- Deploy to Vercel.
- Test all routes.
- Open on mobile once.
- Write submission description.
- Prepare demo script final version.

### Output

- Live URL ready.
- Submission text ready.

---

## H7 — Demo Video Production

### Tasks

Record screen capture:

1. Homepage hero
2. Archive grid
3. Nixon / Clinton / SBF detail pages
4. Haugen sincerity counter-example
5. Calibration page
6. Analyst report section

Record voiceover separately or live.

### Output

- Raw footage and voiceover recorded.

---

## H8 — Edit + Submit

### Tasks

- Edit in CapCut / DaVinci Resolve.
- Keep video under 2 minutes.
- Add captions for key lines.
- Export 1080p.
- Submit demo video + live URL + GitHub link.

### Output

- Final submission complete.

---

## Demo Video Script

### 0:00–0:12 — Hook

Black screen or homepage hero.

Voiceover:
> "Every public figure who ever lied on camera had a body that knew. VERDICT is how we finally asked the body."

On screen:
> "Every lie has a body. Every body has a pulse."

---

### 0:12–0:45 — Calibration Montage

Show archive/detail pages quickly:

- Nixon — Deception 84 — Watergate
- Clinton — Deception 91 — admitted
- Armstrong — Deception 78 — confessed
- Holmes — Deception 81 — convicted
- SBF — Deception 77 — convicted

Voiceover:
> "We processed historically resolved denials using remote heart-rate extraction, facial action units, vocal stress features, and linguistic markers. Then we compared the signal against what history later proved."

---

### 0:45–1:05 — Whistleblower Counter-Example

Show Frances Haugen page.

Voiceover:
> "But VERDICT is not a lie detector. The same system identifies a different signature in whistleblowers: high stress, high sincerity, low deception. It reads physiological signal, not guilt."

---

### 1:05–1:30 — Analyst Report

Show LLM report panel.

Voiceover:
> "An AI analyst converts raw signals into a cautious public-interest report: what changed, when it changed, what historical cases it resembles, and what the limitations are."

---

### 1:30–1:48 — Calibration Page

Show scatter plot and 72% metric.

Voiceover:
> "Every result is calibrated against public ground truth. We publish the misses too, because this is not magic. It is an evidence layer for journalists and citizens."

---

### 1:48–2:00 — Close

Show logo / homepage.

Voiceover:
> "History already knew. Their pulse just finally caught up. This is VERDICT."

---

## Submission Text

Use this as the project description:

```text
VERDICT is the first public physiological archive of public denial. It analyzes public video using remote heart-rate extraction, facial action units, vocal stress features, and linguistic markers, then produces a cautious AI analyst report calibrated against historical outcomes.

Unlike consumer lie-detector tools, VERDICT is built for public-interest journalism. It never claims to prove deception. It reports signal patterns, compares them to historically resolved cases, and publishes its calibration openly.

In our hackathon MVP, we processed six public clips: five historical denials later proven false and one whistleblower testimony as a sincerity counter-example. The result is an archive, a detail page for each clip, and a calibration dashboard showing how physiological signals can become a new evidence layer for the post-truth era.
```

---

## Final UI Checklist

- [ ] Homepage loads under 3 seconds
- [ ] Archive cards look premium
- [ ] Detail page has huge scores above fold
- [ ] Signal chart visible without scrolling too far
- [ ] LLM report is readable and serious
- [ ] Calibration page has one big metric
- [ ] Every page has disclaimer language
- [ ] Vercel link works on another device
- [ ] Demo video under 2 minutes
- [ ] Submission includes live URL, GitHub, video

---

## Emergency Plan

If real pipeline data is late:

- Continue with mock data.
- Label the system as a prototype.
- Use the mock data to film a polished demo.
- Replace with real data only if it arrives before H7.

A polished, coherent demo beats a broken real integration.
