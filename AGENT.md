# VERDICT — AGENT.md
## Rules of Engagement for Humans + AI Assistants

**Status:** Locked at Phase 0. Changes require both Person 1 and Person 2 acknowledgment in `TASKS.md`.

This file is the **how we work** rulebook. `CONTRACT.md` is the **what we build** rulebook. `TASKS.md` is the **where we are** rulebook.

If any tool, AI, or human suggests breaking a rule here to "save time", **the rule wins**. The rules exist because they prevent the exact failures that lose hackathons.

---

## 1. Roles

| Role | Owner | Mission (one line) |
|---|---|---|
| **Person 1 — Pipeline** | Backend | Produce 6 valid clip JSON files conforming to `CONTRACT.md` schema. |
| **Person 2 — Frontend + Product** | Frontend, demo, submission | Ship a deployed, beautiful site and a 2-minute demo video. |

Each person reads their own playbook (`PERSON1_PIPELINE.md` / `PERSON2_FRONTEND_PRODUCT.md`), works against `CONTRACT.md`, and ticks `TASKS.md`.

---

## 2. Folder Ownership (Hard Boundaries)

| Path | Write | Read |
|---|---|---|
| `/backend/**` | Person 1 only | Both |
| `/data/**` | Person 1 only | Both |
| `/frontend/**` | Person 2 only | Both |
| `VERDICT.md` | Nobody (locked spec) | Both |
| `PERSON1_PIPELINE.md` | Person 1 only | Both |
| `PERSON2_FRONTEND_PRODUCT.md` | Person 2 only | Both |
| `CONTRACT.md` | Both, only with co-sign | Both |
| `TASKS.md` | Both | Both |
| `AGENT.md` | Both, only with co-sign | Both |
| `README.md` | Both | Both |

**Cross-folder writes are forbidden.** If Person 2 needs a backend change, they file an entry in `### Open Issues` of `TASKS.md`. They do not edit `/backend`.

---

## 3. The Contract Is Law

- `CONTRACT.md` is the only source of truth for the JSON schema, file paths, clip IDs, score ranges, units, env vars, and tech stack.
- Field names in `CONTRACT.md` are **immutable** after Phase 0 sign-off.
- If a person discovers the contract is wrong, they **stop**, post in `### Open Issues`, and wait for co-sign before editing.
- Any AI assistant proposing a schema rename must be rejected.
- Any code that adds a field outside the contract must update `CONTRACT.md` in the **same commit** with both names listed in the commit message.

---

## 4. Branch & Commit Rules

### Branches

- `main` — always demo-ready. Never broken.
- `pipeline/*` — Person 1 work branches. Example: `pipeline/rppg-extract`.
- `frontend/*` — Person 2 work branches. Example: `frontend/detail-page`.
- `data/*` — Person 1 data updates only. Example: `data/batch-6-clips`.

### Commit Message Format

```
<type>(<scope>): <imperative summary>

<optional body>
```

Allowed types: `feat`, `fix`, `data`, `docs`, `chore`, `style`, `refactor`.
Allowed scopes: `pipe`, `fe`, `contract`, `tasks`, `docs`, `infra`.

Examples:

- `feat(pipe): add CHROM rPPG extraction`
- `feat(fe): build archive grid with mock data`
- `data(pipe): add nixon_1973 processed json`
- `docs(contract): lock schema v1.0`

### Hard Rules

- Never commit secrets. `.env*` is in `.gitignore`.
- Never commit raw video files. Only processed JSON.
- Never force-push `main`.
- Squash-merge feature branches into `main`.
- Each commit must leave the repo runnable.

---

## 5. Sync Points (Five Mandatory)

Each sync point has a checkbox in `TASKS.md`. Both persons must check before moving on.

| # | Name | When | What gets verified |
|---|---|---|---|
| **S0** | Kickoff | Phase 0 start | Repo cloned, both can run `npm run dev` and `python -V`. |
| **S1** | Schema Lock | End of Phase 0 | `CONTRACT.md` reviewed and signed by both. Schema version v1.0 set. |
| **S2** | First Clip Handoff | End of Phase 3 | `data/processed/nixon_1973.json` validates and renders on frontend detail page. |
| **S3** | Full Data Handoff | End of Phase 4 | All 6 clips render on archive grid with no UI errors. |
| **S4** | Demo Lock | End of Phase 6 | Vercel URL works on a phone, demo video exported under 2 min. |

**No skipping syncs.** If a sync fails, fix before proceeding.

---

## 6. Definition of Done

A task is **done** only when its specific criterion below is met. Self-marking without verification is forbidden.

| Task type | Done means |
|---|---|
| **Pipeline task** | Output JSON validates against `CONTRACT.md` schema and one human eyeballs it. |
| **Frontend task** | Page renders without console errors with both mock and real data. |
| **UI polish task** | Looks correct on 1440px desktop AND 390px mobile. |
| **Demo task** | Recorded, watched end-to-end, audio clean, under target duration. |
| **Deploy task** | Live URL opens on a different network/device. |
| **Doc task** | Committed and linked from `README.md`. |

---

## 7. Quality Bar (Non-Negotiable)

- **Lint clean.** Backend: `ruff` or `flake8` zero errors. Frontend: `next lint` zero errors.
- **No console errors** in browser dev tools on any page.
- **No `TODO` comments** in `main`. Use `### Open Issues` in `TASKS.md` instead.
- **Every public function** has at least a one-line docstring or JSDoc.
- **Every API/file path** referenced in code matches `CONTRACT.md` exactly.
- **No dead imports.** No commented-out code blocks.
- **No `any` in TypeScript** in shipped components. Use the schema type from `lib/types.ts`.

---

## 8. AI Assistant Rules

These rules apply to Cascade, Cursor, Claude, ChatGPT, Copilot, or any other coding AI invoked during this build.

### Always

- **Paste `CONTRACT.md`** into the AI's context for any structural change.
- **Show the AI which folder you own** before letting it write files.
- **Read the AI's diff** before accepting. No blind apply.
- **Ask the AI to cite the file and line** it is changing.

### Never

- Never let an AI rename a schema field.
- Never let an AI write into the other person's folder.
- Never let an AI install a new dependency that isn't in `CONTRACT.md` tech-stack lock without co-sign.
- Never let an AI add a new framework, ORM, or database.
- Never let an AI rewrite `VERDICT.md`, `CONTRACT.md`, or `AGENT.md` without explicit co-sign.

### Prompt Hygiene

- Start AI prompts with: `"You are working on the VERDICT hackathon project. Read CONTRACT.md before suggesting changes."`
- For frontend, end prompts with: `"Match the visual direction in PERSON2_FRONTEND_PRODUCT.md."`
- For backend, end prompts with: `"Match the schema in CONTRACT.md exactly. Use the fallback policy in PERSON1_PIPELINE.md if extraction fails."`

---

## 9. Escalation Triggers

These five conditions force a 60-second human-to-human chat (Slack, Discord, or in person). Do **not** debug silently past the 30-min mark.

1. **rPPG fails** on the test clip after 30 min → consider clip swap or fallback estimator.
2. **Py-Feat install breaks** after 20 min → switch to deterministic fallback AU values.
3. **Vercel deploy fails** after 15 min → fall back to local screen capture for the demo.
4. **Schema needs a change** → both must co-sign in `### Open Issues` before any code change.
5. **Demo timing slips** by more than 30 min vs phase plan → drop a non-critical task immediately.

---

## 10. Time Discipline

- Each phase has a hard end time written in `TASKS.md`.
- If a phase is **+30 min late**, automatically execute the fallback path documented in the relevant person file (e.g., manual JSON in PERSON1, mock-only demo in PERSON2).
- Phase 5 is the **scope freeze**. After Phase 5 starts, no new features. Bug fixes only.
- Phase 7 is **submit and stop**. No "one more tweak."

---

## 11. Communication Protocol

- **Default channel:** sit next to each other or open one shared call.
- **Async channel:** `### Open Issues` section at the bottom of `TASKS.md`. Add timestamp and owner.
- **Status format:** "Phase X. On task Y. ETA Z. Blocker: none/<short>."
- **Quiet hours:** none. Hackathon mode.

---

## 12. Forbidden Actions (Hackathon-Specific)

The following are never allowed during this 8-hour build, regardless of how clever the idea sounds:

- No model training or fine-tuning.
- No new ML model downloads over 1 GB.
- No swapping the tech stack locked in `CONTRACT.md`.
- No editing the other person's folder.
- No schema renames after Phase 0.
- No new pages or features after Phase 5.
- No "let me refactor real quick" after Phase 4.
- No live backend dependency on demo day. Static JSON only.
- No personal email/login flows. No auth.
- No animation library beyond Framer Motion if absolutely needed (and only if Person 2 has spare time post Phase 5).

---

## 13. Emergency Doctrine

If everything starts failing at once:

1. **Stop coding.** 60 second pause.
2. Open `TASKS.md`. Identify which phase you are actually in.
3. Drop to the **fallback path** documented in the role doc.
4. Prefer a polished prototype with simulated values over a broken real pipeline.
5. The demo video and the deployed URL are the only artifacts the judges see. Protect those at all costs.

---

## 14. Acknowledgment

Both persons must check the box below in `TASKS.md`:

- `[ ] BOTH: I have read AGENT.md and accept these rules.`

After that, this file is locked.
