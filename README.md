# VERDICT
### *The Physiological History of Denial*

A public, journalism-grade AI system that extracts involuntary physiological, facial, vocal, and linguistic signals from public video and produces a multi-dimensional behavioral profile of the speaker — calibrated against historical denials with verifiable ground truth.

> *"Every lie has a body. Every body has a pulse. We ran one hundred years of historical denials through the machine. The pulse remembered what history forgot."*

---

## Where to Start

| You are | Open this first |
|---|---|
| **Anyone** | `AGENT.md` (the rules), then `CONTRACT.md` (the locked tech truth) |
| **Person 1 — Pipeline** | `PERSON1_PIPELINE.md` (your detailed playbook) |
| **Person 2 — Frontend + Product** | `PERSON2_FRONTEND_PRODUCT.md` (your detailed playbook) |
| **Both, every 30 min** | `TASKS.md` (tick boxes, check sync points) |

The full product spec lives in `VERDICT.md`. Read it once, then return only for narrative reference.

---

## Doc Map

| File | Purpose | Authority |
|---|---|---|
| `README.md` | Index and quick start | Informational |
| `AGENT.md` | Rules of engagement (humans + AI) | Locked at Phase 0 |
| `CONTRACT.md` | Locked technical contract — schema, paths, tech stack, env | **Supreme** |
| `TASKS.md` | Master phase-based task tracker, sync points, checkboxes | Live |
| `VERDICT.md` | Full product specification and narrative | Reference |
| `PERSON1_PIPELINE.md` | Backend playbook — extraction, scoring, LLM analyst | Person 1 |
| `PERSON2_FRONTEND_PRODUCT.md` | Frontend + demo + submission playbook | Person 2 |

If two docs disagree, **`CONTRACT.md` wins**. If `CONTRACT.md` and `AGENT.md` disagree on a process question, `AGENT.md` wins.

---

## Repo Layout

```
verdict/
├── *.md                          # all the docs above
├── data/                         # OWNER: Person 1
│   ├── raw_clips/                # gitignored video sources
│   └── processed/                # committed analysis JSON (the handoff)
├── backend/                      # OWNER: Person 1
│   └── verdict_pipeline/
└── frontend/                     # OWNER: Person 2
    ├── app/
    ├── components/
    └── lib/
```

Folder ownership is hard. See `AGENT.md` §2.

---

## Quick Commands

### Backend (Person 1)

```bash
# from /backend
python -m venv .venv
.\.venv\Scripts\activate            # PowerShell
pip install -r requirements.txt
python scripts/download_clip.py --url <yt> --start 14 --end 26 --out ../data/raw_clips/nixon_1973.mp4
python -m verdict_pipeline.batch    # processes all 6 clips
```

### Frontend (Person 2)

```bash
# from /frontend
npm install
npm run dev                         # http://localhost:3000
npm run sync-data                   # copies ../data/processed/all_clips.json to public/data/
npm run build && npm run start      # production preview
```

### Handoff (Person 1 → Person 2)

```bash
# Person 1
git add data/processed && git commit -m "data(pipe): batch v1" && git push

# Person 2
git pull
cd frontend && npm run sync-data
```

---

## Sync Status

Live progress lives in `TASKS.md`. The five hard sync gates:

- **S0** Kickoff
- **S1** Schema lock
- **S2** First clip handoff
- **S3** Full data handoff
- **S4** Demo lock

No phase advances until its predecessor sync is checked by both.

---

## Submission

Final outputs:

- **Live URL** — Vercel deployment of `/frontend`
- **GitHub** — this repo, public
- **Demo video** — ≤ 2 min, 1080p, YouTube unlisted

Submission text template lives at the bottom of `PERSON2_FRONTEND_PRODUCT.md`.
