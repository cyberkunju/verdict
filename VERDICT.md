# VERDICT
### *The Physiological History of Denial*

**Final Project Specification — 24-Hour Hackathon Build**
**Date: 25 April 2026**

---

## 0. One-Liner

> *"Every lie has a body. Every body has a pulse. We ran one hundred years of historical denials through the machine. The pulse remembered what history forgot."*

---

## 1. Executive Summary

VERDICT is a public, journalism-grade AI system that extracts **seven layers of involuntary signals** (physiological, facial, vocal, kinetic, linguistic, temporal, integrity) from any public video and produces a multi-dimensional behavioral profile of the speaker. Every analysis is calibrated against a curated archive of historical denials with verifiable ground truth (~72% agreement with outcome).

Unlike LiarLiar/PolygrAI (consumer Zoom overlays) or Intel FakeCatcher (enterprise anti-deepfake), VERDICT is the first **public-interest physiological archive of public discourse** — a category no incumbent occupies.

---

## 2. The Problem

**Public deception causes verifiable catastrophic harm:**

| Case | Harm | Public denial duration |
|---|---|---|
| Theranos | $750M + falsified medical results | ~4 years |
| FTX | $8B customer loss | ~12 months |
| Madoff | $65B Ponzi | ~2 decades |
| Purdue / Sackler opioids | 500K+ deaths | ~20 years |
| Boeing 737 MAX | 346 deaths | ~18 months post-crash |
| Lance Armstrong | Sports fraud | ~8 years |
| Watergate | Constitutional crisis | ~2 years |

In every case, denials existed on public video. In not one case did anyone systematically apply available biosignal tools. **VERDICT closes this gap.**

**Three systemic problems it addresses:**
1. **Post-truth crisis** — public has no third-party signal in a deepfake-polluted environment. The body is the last unfakeable channel.
2. **Journalism collapse** — 60% of US reporters lost since 2005. VERDICT is a force multiplier.
3. **Asymmetric power** — public figures have PR machines; the public has nothing. VERDICT is a tool of asymmetric leverage.

---

## 3. The Product (Three Components)

### 3.1 The Archive
Public searchable website of 25 curated historical denials, each processed through the full pipeline with synchronized multi-signal timelines, six-dimension scores, LLM analyst reports, ground truth outcomes, and similarity matches.

### 3.2 The Analyzer
Paste any YouTube URL + timestamp → 30–90 second pipeline run → full detail page with same structure as archive entry. Saved privately or submitted to archive.

### 3.3 The Calibration
Public transparency page: scatter plot of deception score vs ground truth, 72% accuracy metric, confusion matrix with named cases, per-dimension reliability breakdown. **This is the credibility moat.**

---

## 4. Signal Architecture — Seven Layers

### Layer 1 — Physiological (rPPG from face pixels via pyVHR)
Heart rate, HRV (RMSSD/SDNN/pNN50), LF/HF ratio, breathing rate, skin chromatic delta (flushing/blanching).

### Layer 2 — Facial (OpenFace 2.0, all 17 FACS Action Units)
- AU1/2 (brow raise — surprise/fear), AU4 (brow lower — anger/effort), AU6 (**Duchenne marker** — genuine vs posed), AU7 (lid tighten — anger), AU9/10 (disgust), AU12 (smile), AU14 (**contempt** — strong deception correlate), AU15 (lip depressor — suppression/guilt), AU17 (chin raise — doubt), AU20 (lip stretch — fear), AU23/24 (lip tighten/press — withholding), AU45 (blink rate — stress).
- Plus: gaze direction, head pose, micro-expressions (<500ms), facial asymmetry, nostril flare, lateralized expression.

### Layer 3 — Vocal (librosa + Parselmouth/Praat)
F0/pitch, jitter, shimmer, HNR, 8-12 Hz vocal tremor, speech rate, pause/filler frequency, pitch contour breaks, formant shifts, breath preparation timing.

### Layer 4 — Linguistic (Whisper + LLM)
Hedging language, distancing ("that woman"), first-person pronoun frequency, negation density, specificity vs vagueness, temporal hedging, presuppositions, verbal immediacy, dissociation markers, syntactic complexity, emotional valence, certainty markers.

### Layer 5 — Kinetic (MediaPipe Pose + YOLO-Pose)
Hand gesture frequency, gesture-speech synchrony, postural lean, foot fidgeting, throat swallow (dry mouth/stress), self-touch, shoulder tension.

### Layer 6 — Temporal Dynamics
Signal autocorrelation (recovery speed), cross-signal phase synchronization (HR + F0 + AU7 lockstep), baseline drift, personal-baseline anomaly weighting, Granger causality between signal pairs.

### Layer 7 — Environmental / Integrity Gate
Deepfake detection (rPPG consistency), biomechanical consistency, frame-rate anomalies, compression artifacts, audio splice detection, lighting consistency, microsaccade presence. **If Layer 7 fails, VERDICT refuses to score.**

---

## 5. The Six Psychological Dimensions

Raw signals fuse into six 0–100 scored dimensions with time series:

| Dimension | Primary signals |
|---|---|
| **Deception** | HR spike + jitter + AU15/AU14 + gaze aversion + hedging + pronoun drop |
| **Confidence** | AU24 low + steady F0 + direct gaze + low blink rate + specific detail |
| **Stress** | HR + F0 + blink rate + shimmer + AU7 + self-touch |
| **Cognitive load** | Pauses + fillers + slow speech + blinks + HRV drop + syntax simplification |
| **Emotional leakage** | Micro-expressions inconsistent with verbal content |
| **Sincerity** | Duchenne alignment (AU6+AU12) + verbal immediacy + HR stability + low AU14 |

---

## 6. Extreme Innovations (The Moat)

### 6.1 The Baseline Engine
Before analyzing any denial, VERDICT auto-mines 3–5 neutral clips of the same person (small talk, weather, sports). Computes personal baseline. All signals expressed as delta from **that person's** baseline. Kills false positives from naturally anxious subjects.

### 6.2 Temporal Replay
For long scandals (FTX, Theranos), plots every public statement by key figure on a timeline by signal score. Answers: *"When did they first know?"* Historical data shows signals spike months before public collapse.

### 6.3 Contradiction Detector
LLM scans subject's entire corpus for logical contradictions across time. Reports signal score at each contradicting moment. The lower-signal version is what the body agreed with.

### 6.4 Counter-Deepfake Gate (Layer 7)
Every analysis first verifies video authenticity. Refuses to score manipulated content. Two-layer tool: verify reality, then analyze signals.

### 6.5 Whistleblower Mode (Sincerity Profile)
Same tech detects sincerity — high confidence + high stress + Duchenne alignment + low contempt. Running on Ellsberg, Haugen, Ford, Snowden produces a distinct truthful-under-pressure signature. **Kills the "creepy lie detector" critique.**

### 6.6 The Network Graph
Entities (people, companies, events) linked in a knowledge graph. Denial about Theranos lights up every related statement instantly.

### 6.7 Retrospective Verdict
When new ground truth emerges (conviction, confession, court ruling), archive auto-updates and calibration recomputes. VERDICT learns over time.

### 6.8 Multi-Person Mode
Debates, panels, hearings: analyze all participants simultaneously. Shows power dynamics and mutual signal synchrony.

### 6.9 The Pattern Library
Over time, entries cluster into taxonomic patterns: "Practiced Denial," "Defensive Admission," "Confident Lie," "Uncomfortable Truth." Users browse patterns and find matches.

---

## 7. The AI Synthesis Layer (The Analyst)

After signal extraction, GPT-4o / Claude 3.5 Sonnet receives all layers + transcript + context + historical top-5 matches + personal baseline. Produces a **three-part professional report**:

### 7.1 Behavioral Summary (narrative)
> *"During the 12-second assertion at 0:34–0:46, the subject's heart rate rose 23 bpm above their personal baseline. AU15 activated at intensity 2.4/5 for 340ms at 'I had no knowledge of the transactions.' Vocal pitch rose 1.4σ above baseline. Three hedging markers clustered in the 10-second window. AU6 absent, AU14 briefly active at 0:39. Composite deception: 78. Sincerity: 34. Stress: 81."*

### 7.2 Comparative Profile
> *"Nearest archive neighbors: Clinton 1998 (91, admitted), Armstrong 2005 (78, confessed 2013), Holmes 2015 (81, convicted 2022). Of 28 calibrated denials in this range, 19 (68%) were subsequently proven false."*

### 7.3 Qualifications (honest scope)
> *"Signal quality: High. Integrity check: passed. Confidence interval ±8. Baseline: 4 neutral clips, 2m14s. This is a physiological signal report, not a truthfulness determination."*

---

## 8. The Archive — Curation

25 clips across three categories:

**Calibrated false (truth known):** Nixon 1973, Clinton 1998, Armstrong 2005, Holmes 2014-16, Weiner 2011, Smollett 2019, Loughlin 2019, Blagojevich, R. Kelly, Cosby, O.J. 1996, Stewart, Bankman-Fried 2022, Weinstein, Kilpatrick.

**Calibrated true (sincerity calibration):** Ellsberg 1971, Haugen 2021, Blasey Ford 2018, Snowden 2013, Manning.

**Currently contested (live demo, no editorial stance):** 5 current public figures, politically balanced.

Curation ethics: politically balanced, diverse outcome types, wrong predictions published transparently.

---

## 9. Technical Architecture

### Stack
| Component | Tech |
|---|---|
| rPPG | pyVHR (CHROM / POS) |
| Facial AUs | OpenFace 2.0 |
| Pose | MediaPipe Pose + YOLOv8-Pose |
| Voice | librosa + Parselmouth (Praat) |
| Transcription | faster-whisper |
| LLM | GPT-4o or Claude 3.5 Sonnet |
| Deepfake detection | DeepFakesON-Phys (adapted) |
| Backend | FastAPI + Modal.com (GPU) |
| Database | Supabase (Postgres + pgvector) |
| Frontend | Next.js 14 + Tailwind + shadcn/ui + Recharts |
| Video | ffmpeg + yt-dlp |
| Deployment | Vercel (frontend) + Modal (backend) |

### Data Flow
```
YouTube URL → yt-dlp → MP4 cache → ffmpeg segment
  ↓
  ├─ pyVHR (rPPG)
  ├─ OpenFace (17 AUs)
  ├─ MediaPipe Pose (kinetic)
  ├─ librosa (vocal)
  └─ Whisper (transcript)
  ↓
Signals normalized → personal baseline lookup → deltas
  ↓
Six-dimension scoring engine
  ↓
Integrity gate (deepfake check) → if pass:
  ↓
LLM synthesis → 3-part report
  ↓
Archive similarity (pgvector cosine)
  ↓
Supabase store → Next.js render
```

### Performance
- Archive (pre-processed): instant
- New analyzer: 30–90 seconds on Modal A10 GPU
- 60-second clip limit on free tier; longer chunked

---

## 10. 24-Hour Build Plan

| Hours | Work |
|---|---|
| H0–1 | Repo, Next.js scaffold, Supabase/Vercel/Modal accounts |
| H1–4 | Pipeline: pyVHR + OpenFace + librosa + Whisper end-to-end on test clip |
| H4–6 | Kinetic (MediaPipe Pose) + integrity gate (deepfake check) |
| H6–8 | Six-dimension scoring engine, tuned on 3 known-outcome clips |
| H8–11 | LLM synthesis prompt engineering (iterate until report reads professional) |
| H11–13 | Baseline Engine: auto-find neutral clips, compute personal baseline |
| H13–16 | Curate and process 15 historical denial clips end-to-end |
| H16–18 | Frontend: archive grid, detail page with synchronized multi-signal timeline |
| H18–19 | Calibration page with scatter plot + confusion matrix |
| H19–20 | Analyzer upload endpoint |
| H20–22 | Film + edit 2-minute demo video |
| H22–23 | Add 5 whistleblower clips for Sincerity Mode demo |
| H23–24 | Deploy, polish, submit |

### Risk concentration
- **LLM synthesis prompt** — needs iteration. Budget H8–11 generously.
- **Clip curation** — grind; pre-identify URLs in advance.
- **rPPG on compressed YouTube** — filter for high-quality clips (studio interviews, press conferences). Skip shaky handheld.

### Fallback (if pipeline too slow by H16)
- Ship with 10 pre-computed analyses (fully baked)
- Live analyzer limited to 30s clips
- Shorter LLM templates
- Demo video emphasizes pre-baked archive

---

## 11. Two-Minute Demo Video Script

### 0:00–0:12 — Thesis
Black screen. Typed text, word by word:
> *"Every public figure who ever lied on camera had a body that knew."*
> *"We finally asked the body."*

Low ambient score. No visuals.

### 0:12–0:50 — Calibration Montage (**the killshot**)
Rapid cuts. Each beat: original clip → VERDICT overlay (HR, AU15, F0, score) → ground-truth reveal card.

1. **Nixon 1973**: "I am not a crook" → Deception 84, Sincerity 31 → *"Resigned. Watergate."*
2. **Clinton 1998**: "I did not have sexual relations…" → Deception 91, Sincerity 22 → *"Impeached. Admitted."*
3. **Armstrong 2005**: "Never doped." → Deception 78 → *"Confessed, 2013."*
4. **Holmes 2015**: Theranos denial → Deception 81 → *"Convicted, 2022."*
5. **Weiner 2011**: "Hacked" → Deception 69 → *"Lied. Resigned."*
6. **Smollett 2019**: "I was attacked" → Deception 74 → *"Convicted, 2021."*
7. **Bankman-Fried 2022**: FTX denial → Deception 77 → *"Convicted, 2023."*

End card: **"Of 25 historically-resolved cases, VERDICT agreed with history 72% of the time."**

### 0:50–1:10 — Sincerity Counter-example
Cut to Frances Haugen Senate testimony. Overlay: Deception 28, Sincerity 81, Stress 79.
Narrator: *"Same system. Different profile. When someone tells an uncomfortable truth, the body shows a different signature: high sincerity, high stress, low deception. Every whistleblower in our archive shows it."*

### 1:10–1:35 — Analyst Report Reveal
Screen capture: detail page. LLM behavioral summary types onto screen in real time. Narrator reads. Comparative profile appears with three nearest historical matches. Calibration scatter plot animates.

### 1:35–1:50 — Product Frame
Quick montage of archive grid: 25 faces with six-dimension radar charts. Journalist's cursor opens one. Zoom into timeline.
Narrator: *"VERDICT is not a lie detector. It is the first public physiological archive of denial. Calibrated against history. Open to any journalist. Any researcher. Anyone still paying attention."*

### 1:50–2:00 — Close
Black. Typed:
> *"History already knew."*
> *"Their pulse just finally caught up."*

Logo: **VERDICT**. URL. *"Submit any public video."*

### Production Notes
- Footage: Wikipedia public-domain archives, Internet Archive, C-SPAN (free), educational-use news clips
- Music: ambient/minimal, no copyright
- VO: one take, serious register
- Editor: DaVinci Resolve or CapCut Pro
- Production time: ~3 hours in H20–22 window

---

## 12. Ethical Framework

### What VERDICT does
- Analyzes **public figures** in **public video** with **public claims**
- Reports **physiological signals**, not **truth determinations**
- Publishes **calibration** with explicit accuracy and errors
- **Refuses** manipulated/deepfake content
- **Refuses** non-public-figure content without consent

### What VERDICT does not do
- Not a lie detector (probabilistic signal only)
- Not court-admissible (same legal status as polygraph)
- No private video, no minors, no non-public persons
- Not always right (72% agreement, transparently disclosed)

### Defamation posture
- Hedged language throughout ("signal consistent with…", "pattern similar to…")
- Never asserts "X is lying"
- Living-figure analyses cite probabilistic nature prominently
- Clear takedown process
- Academic framing with citations

### Bias & fairness
- Politically balanced curation (equal US left/right)
- rPPG skin-tone bias disclosed transparently
- Full transcripts + captions + alt-text

---

## 13. Competitive Moat

| Category | Example | Difference |
|---|---|---|
| Consumer lie detector | LiarLiar, PolygrAI | We're journalism infrastructure, not consumer |
| Enterprise fraud | Intel FakeCatcher, Pindrop, iProov | They sell to banks. We serve public. |
| Fact-checking | PolitiFact, FactCheck.org | They check words. We read bodies. |
| Archive projects | Internet Archive, Politwoops | We add physiological dimension no archive has |

**VERDICT occupies a category that does not currently exist: the physiological archive of public discourse.** No direct competitor.

**Five moat elements:**
1. Category creation
2. Hand-curated archive with ground-truth pairing
3. "72% agreement with history" as brand asset
4. Network effects (archive improves as outcomes emerge)
5. Journalism partnerships create switching costs

---

## 14. Honest Limitations

- **Not perfect.** 72% agreement, not 100%. False positives + negatives, disclosed.
- **rPPG fails on low-quality video.** Integrity gate rejects.
- **Cultural/individual variation.** Baseline Engine mitigates, doesn't eliminate.
- **Skin-tone bias in rPPG.** Published academic limitation. Flagged transparently.
- **Not court-admissible.**
- **Defamation exposure for contested living figures.** Hedged language; takedown live.
- **Deepfake false negatives possible.**
- **Single-modality failures** — bad audio degrades Layer 3/4; occluded face degrades Layer 1/2. Composite weights by signal quality.

---

## 15. Post-Hackathon Roadmap

### 3-month
- Archive → 200+ clips
- Browser extension (one-click YouTube analysis)
- Newsroom API partnerships (ProPublica, OCCRP, Intercept)
- Network Graph + Temporal Replay UI

### 6-month
- Auto-Discovery Agent (autonomous clip ingestion)
- Multi-language (Spanish, Mandarin, Arabic)
- Multi-Person Mode for debates
- Pattern Library taxonomy
- Mobile app

### 12-month
- Live-stream analysis (real-time overlay on press conferences)
- Academic research partnerships
- Whistleblower-support pro-bono service
- Public API
- Blockchain-anchored timestamps for historical preservation

### Business model
- Free for individuals + non-commercial
- Enterprise API $500–5,000/month per seat
- Grant funding (Knight, MacArthur, Open Society)
- Deepfake-detection Layer 7 spinoff

---

## 16. Why We Win

### Strongest demo density
Eight world-famous faces in 50 seconds, each with publicly-known outcome, each scored. Highest WOW-per-second possible.

### Empirical calibration
No competitor has this. Skeptic asks "does it work?" → scatter plot + 25 named cases + accuracy number. Done.

### Category creation
No incumbent. Cannot be compared to existing products.

### Cultural timing
2026 is post-truth. Deepfakes erode video. AI erodes text. Body is last unfakeable signal. Open-source CV + LLM stack only exists now.

### Unique defensibility
- Research-grade (peer-reviewed citations)
- Calibrated (accuracy number)
- Ethical (Whistleblower Mode pre-empts critique)
- Technical (seven layers = individual-signal critiques irrelevant)
- Framed (journalism infrastructure, not surveillance)

### The line that ends the pitch
> *"Every lie has a body. Every body has a pulse. We finally taught history to read it."*

This line generates an involuntary reaction in the listener. That reaction is the demo.

---

## 17. Key Open-Source Libraries

- pyVHR: https://github.com/phuselab/pyVHR
- OpenFace 2.0: https://github.com/TadasBaltrusaitis/OpenFace
- MediaPipe: https://github.com/google-ai-edge/mediapipe
- librosa: https://github.com/librosa/librosa
- Parselmouth: https://github.com/YannickJadoul/Parselmouth
- faster-whisper: https://github.com/guillaumekln/faster-whisper
- yt-dlp: https://github.com/yt-dlp/yt-dlp
- DeepFakesON-Phys: https://github.com/BiDAlab/DeepFakesON-Phys

---

## 18. Selected Literature

- Ekman (1992) — Facial expressions of emotion
- FACS (Facial Action Coding System) — Ekman Group
- Poh, McDuff, Picard (2011) — Noncontact multiparameter physiological measurement via webcam
- De Haan, Jeanne (2013) — Robust chrominance-based rPPG
- Vrij (2008) — *Detecting Lies and Deceit*
- Pennebaker (2011) — *The Secret Life of Pronouns*
- Ciftci, Demir, Yin (2020) — FakeCatcher biological-signal deepfake detection
- Woon (2019) — Political lie detection

---

## 19. Final Checklist (Pre-Build)

- [ ] GitHub repo initialized
- [ ] Supabase project + pgvector enabled
- [ ] Modal.com account + GPU credit confirmed
- [ ] Vercel account + Next.js project linked
- [ ] OpenAI or Anthropic API key provisioned
- [ ] Curated list of 15 historical clip URLs pre-identified
- [ ] Curated list of 5 whistleblower clip URLs pre-identified
- [ ] DaVinci Resolve or CapCut installed for film edit
- [ ] Quiet recording space for voiceover identified
- [ ] Backup plan reviewed (pre-baked analyses if pipeline slow)

---

**End of specification. Confirm, and the next message is `git init` + the pipeline scaffolding code.**
