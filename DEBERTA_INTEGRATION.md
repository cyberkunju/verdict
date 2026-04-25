# DeBERTa-v3 Deception Classifier — Integration Reference

> Fine-tuned `microsoft/deberta-v3-base` for binary deception classification on
> a balanced mix of first-person + claim-style deception corpora. Replaces the
> legacy TF-IDF `VerdictTextPrior-v0` as the preferred text-prior signal in the
> verdict pipeline, with transparent fallback if the model directory is absent.

Trained **2026-04-25 on Modal A10G** (single ephemeral run, ~5 min wall-clock).

---

## 1. Model Card

| Field | Value |
|---|---|
| Base model | `microsoft/deberta-v3-base` (184 M params) |
| Task | Binary sequence classification (`truthful` vs `deceptive`) |
| Tokenizer | DeBERTa-v3 SentencePiece, max sequence length 256 |
| Output | `softmax(logits)` → `[P(truthful), P(deceptive)]` |
| Total params | ~184 M |
| Disk size on local | **~714 MB** (model.safetensors 703.5 MB + tokenizer 10.6 MB + configs) |
| Inference (CPU) | ~50–80 ms per transcript; ~19 s cold-start (one-shot model load) |
| Inference (GPU) | ~5–10 ms per transcript |
| License | MIT (DeBERTa) — fine-tune inherits |

### Final eval (held-out 10 % of training mix, n=1,288):

| Metric | Value |
|---|---|
| Accuracy | **0.849** |
| F1 (binary, deceptive class) | **0.846** |
| ROC-AUC | **0.904** |
| Eval loss | 0.412 |

These numbers are honest in-distribution metrics on the training corpora.
Zero-shot transfer to the VERDICT first-person archive is materially weaker
(see §6).

---

## 2. Training Data

Combined balanced corpus produced by
`research-data/scripts/prepare_deberta_data.py`.

| Source | Style | Raw rows | Kept rows | Notes |
|---|---|---|---|---|
| **Diplomacy** (Peskov et al. 2020, Cornell ConvoKit) | First-person game messages | 17,289 | 15,899 | label = `meta.speaker_intention` ∈ `{Truth, Lie}` |
| **LIAR-UCSB** (Wang 2017, augmented) | Third-person fact-check claims | 12,789 | 5,600 | label = `label_mapped` ∈ `{resolved_true, resolved_false}` |
| **AVeriTeC** (Schlichtkrull et al. 2023) | Claim/evidence pairs | ~3,500 | 3,017 | label heuristic: `*false*`/`refuted` → 1, `*true*`/`supported` → 0 |
| **Total (raw)** | | **24,516** | deceptive=6,444, truthful=18,072 |
| **Total (after class-balance down-sample)** | | **12,888** | 6,444 / 6,444 |
| Train split | | **11,600** | 90 % |
| Eval split  | | **1,288** | 10 % held out |

Output JSONL: `research-data/processed/deberta_training_data.jsonl` (1.73 MB),
`research-data/processed/deberta_eval_data.jsonl` (0.19 MB).

Each row: `{"text": str, "label": 0|1, "source": "diplomacy|liar|averitec"}`.

### Why this mix?

The legacy `VerdictTextPrior-v0` (TF-IDF + LogReg, 0.94 MB joblib) was trained
purely on LIAR — **news fact-check claim style**. The VERDICT archive consists
of **first-person testimonial deceptive denials and whistleblower disclosures**,
where TF-IDF on third-person claim wording does not transfer. Diplomacy is the
nearest publicly-licensed analog (first-person game messages with verified
deceptive intent). Mixing all three corpora gives the classifier exposure to
both styles.

---

## 3. Training Hyper-parameters

Configured in `research-data/scripts/modal_deberta.py::train`.

| Hyper-parameter | Value | Notes |
|---|---|---|
| Epochs | 3 | best-by-`roc_auc` checkpoint reloaded at end |
| Batch size (train) | 16 |
| Batch size (eval)  | 32 |
| Learning rate | 2e-5 | linear decay with warmup |
| Warmup ratio | 0.06 |
| Weight decay | 0.01 |
| Max sequence length | 256 |
| Mixed precision | `fp16` |
| Total optimizer steps | 2,175 |
| Optimizer | AdamW (HF default) |
| Random seed | 42 |
| Eval/save strategy | per epoch, `save_total_limit=1`, `load_best_model_at_end=True` |

Training wall-clock: **~3.5 min on Modal A10G** (excluding ~5 min image build
on first run; subsequent runs reuse the cached image).

---

## 4. File Layout

### Local artifacts (after `pull_artifacts`)

```
backend/models/deberta_deception/
├── model.safetensors          703.54 MB   (the fine-tuned weights)
├── config.json                  ~1 KB     (architecture + label maps)
├── tokenizer.json                8.26 MB
├── tokenizer_config.json         ~1 KB
├── special_tokens_map.json       ~1 KB
├── added_tokens.json             ~1 KB
├── spm.model                     2.35 MB  (SentencePiece vocabulary)
├── training_args.bin              ~5 KB    (HF TrainingArguments pickle)
└── training_metadata.json         ~1 KB    (corpora counts, final metrics)
```

`backend/models/deberta_deception/training_metadata.json` is the source of
truth for reproducing the run (corpora row counts + final eval metrics).

### Modal volume (cloud)

`verdict-models` volume (`modal volume list` → `verdict-models`):
```
/models/deberta_deception/                  ← same files as above
```

Region: nearest to user's Modal workspace (auto-selected). Cost ≈ **$0.11/mo**
for the 714 MB checkpoint at $0.15/GB-month.

---

## 5. Code Surface

### 5.1 Inference adapter — `backend/verdict_pipeline/deberta_text_prior.py`

```python
from verdict_pipeline import deberta_text_prior

deberta_text_prior.is_available()              # bool — model dir present + loadable
p = deberta_text_prior.predict(transcript)     # float in [0, 1] or None
```

Behaviour:

- Lazy-loads on first call (single global pipeline, thread-safe via `Lock`).
- Returns `None` and logs a warning if the model directory is missing, if
  `torch`/`transformers` are unavailable, or if a forward pass throws.
- Truncates inputs to 256 tokens (matches training).
- Auto-detects CUDA; falls back to CPU.

### 5.2 Wired through `linguistic.py`

`backend/verdict_pipeline/linguistic.py::_text_deception_prior` now uses a
two-tier preference:

```
Tier 1: DeBERTa-v3 (this model)         ← preferred
Tier 2: TF-IDF VerdictTextPrior-v0      ← legacy fallback
Tier 3: None                            ← no signal
```

The output flows into `LinguisticFeatures.text_deception_prior` and is
serialized to every clip JSON at `signals.text_deception_prior` (see
`batch.py::_dump`).

### 5.3 Used as a *trained* Fusion feature, not stacked

`research-data/scripts/build_fusion_dataset.py` and
`research-data/scripts/train_fusion_v0.py` both list
`text_deception_prior` as feature 15 in `FEATURE_NAMES`. The trained
logistic regression sees it directly. Stacking alpha is set to 0 in the
joblib (`text_prior_stacking.alpha = 0.0`).

`backend/verdict_pipeline/score.py::compute_scores` populates the value into
the feature dict it passes to `fusion.predict(...)`:

```python
fusion_features["text_deception_prior"] = float(text_deception_prior)
fusion_features["cross_modal_synchrony"] = _runtime_synchrony(...)
fusion_prob = fusion.predict(fusion_features, text_prior=text_deception_prior)
```

### 5.4 Conformal-prediction wrapping

`backend/verdict_pipeline/fusion.py::predict_full` now returns split-conformal
p-values + an explicit `abstain` flag using LOSO residuals saved in the joblib:

```python
{
  "prob": 0.74,
  "predicted_label": 1,
  "p_value_deceptive": 0.231,
  "p_value_truthful":  0.077,
  "abstain": False,
  "coverage_alpha": 0.20,
  "n_calibration": 12
}
```

Backwards-compatible: `fusion.predict(...)` still returns just the float prob.

---

## 6. Capability — Honest Performance Assessment

### 6.1 In-distribution (held-out 10 % of training mix)

**Strong**: 0.849 acc / 0.904 ROC-AUC. The model genuinely separates Diplomacy
lies from Diplomacy truths and resolved-false claims from resolved-true ones.

### 6.2 Zero-shot transfer to the VERDICT 12-clip archive

Per-clip P(deceptive) measured on the truncated transcript (first 1000 chars):

| Clip | Ground truth | DeBERTa P(deceptive) | Interpretation |
|---|---|---|---|
| nixon_1973         | deceptive | **0.959** | ✓ correct |
| holmes_2018        | deceptive | **0.964** | ✓ correct |
| clinton_1998       | deceptive | 0.382 | ✗ false-negative (short denial) |
| sbf_2022           | deceptive | 0.196 | ✗ false-negative (rambling, hedged) |
| armstrong_2005     | deceptive | 0.271 | ✗ false-negative (calm denial) |
| dean_1973          | truthful  | **0.162** | ✓ correct |
| shultz_2019        | truthful  | **0.410** | ✓ correct |
| wigand_1996        | truthful  | 0.506 | ~ borderline |
| snowden_2013       | truthful  | 0.575 | ✗ false-positive |
| haugen_2021        | truthful  | 0.881 | ✗ false-positive |
| cheung_2019        | truthful  | 0.793 | ✗ false-positive |
| ellsberg_1971      | truthful  | (no transcript) | — |

**Archive accuracy: 4 / 11 confidently correct, 7 ambiguous/wrong.**

This is the honest signal. The training corpora do not contain whistleblower-
style first-person disclosures of *another* party's wrongdoing, so the model
treats descriptions of fraud/wiretapping/etc. as deceptive-style language.
This same domain mismatch is why we measured the multimodal Fusion-v0 LOSO at
**0.417** when using *real* AUs (versus the previously inflated 0.909 driven
by hand-coded fallback AU profiles). Physiological + linguistic features alone
cannot reliably separate stressed truthful whistleblowers from calm practiced
deceivers on this 12-clip archive.

### 6.3 What this model is good for

1. **Producing a calibrated text-prior for downstream probabilistic fusion.**
   The 0.904 ROC-AUC on Diplomacy + LIAR + AVeriTeC means the rank-ordering of
   claims by P(deceptive) is meaningful in those domains.
2. **First-person game / chat / negotiation deception** (its training
   distribution).
3. **Fact-checkable third-person claims** (LIAR / AVeriTeC distribution).

### 6.4 What it is NOT good for

1. **First-person whistleblower disclosures.** No corpus of this style exists
   in the training mix; the model has no basis to distinguish it from
   accusatory false claims.
2. **Short denials** ("I am not a crook", "I did not have sexual relations
   with that woman"). The 256-token context is fine, but the *style* of
   short, controlled denial is rare in training data.
3. **Stand-alone deception detection on novel video subjects.** Use it as
   one input to the multimodal Fusion model + conformal abstention, never
   alone.

---

## 7. Reproducing the Run

```powershell
# 1. Prepare data (local; ~5 s, 12.9k balanced rows)
python research-data/scripts/prepare_deberta_data.py

# 2. Fine-tune on Modal A10G (~3.5 min training + ~5 min image build first time)
$env:PYTHONIOENCODING = "utf-8"
modal run --detach research-data/scripts/modal_deberta.py::run_training

# 3. Pull artifacts back to backend/models/deberta_deception/  (~715 MB)
modal run --detach research-data/scripts/modal_deberta.py::pull_artifacts

# 4. Sanity check
$env:PYTHONPATH = "backend"
python -c "from verdict_pipeline import deberta_text_prior as d; print(d.predict('I did not have sexual relations with that woman.'))"

# 5. Re-extract features for all archive clips (uses DeBERTa via linguistic.py)
python -m verdict_pipeline.batch

# 6. Re-train Fusion-v1 on the new feature distribution
python research-data/scripts/build_fusion_dataset.py
python research-data/scripts/train_fusion_v0.py
```

---

## 8. Modal Deployment Details

| Field | Value |
|---|---|
| App name | `verdict-deberta` |
| Region | Auto (Modal default) |
| Image | `debian_slim` (Python 3.11) + torch 2.5.1 + transformers 4.46.2 + accelerate 1.1.1 + datasets 3.1.0 + sentencepiece 0.2.0 + scikit-learn + tf-keras |
| GPU | A10G (24 GB) |
| Memory | 16 GB host RAM |
| Timeout | 3,600 s (1 h hard cap) |
| Idle window | 60 s (`scaledown_window`) |
| Volume | `verdict-models` (`modal.Volume.from_name(..., create_if_missing=True)`) |
| Image build cost | ~$0 (Modal image build is free; downloads ~2 GB of CUDA wheels) |
| Training cost | A10G ≈ $1.10/hour × ~0.06 h ≈ **$0.07** per run |

The volume persists across runs; subsequent training jobs only need to
re-upload the small JSONL data, not the model weights.

### 8.1 Modal app definition skeleton

```python
import modal

app = modal.App("verdict-deberta")
volume = modal.Volume.from_name("verdict-models", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch==2.5.1", "transformers==4.46.2", "accelerate==1.1.1",
        "datasets==3.1.0", "evaluate==0.4.3", "sentencepiece==0.2.0",
        "scikit-learn==1.5.2", "tiktoken", "tf-keras",
    )
)

@app.function(
    image=image, gpu="A10G", volumes={"/models": volume},
    timeout=3600, scaledown_window=60, memory=16*1024,
)
def train(training_jsonl: bytes, eval_jsonl: bytes) -> dict:
    ...  # see research-data/scripts/modal_deberta.py for full body
```

---

## 9. Known Issues / Caveats

1. **Domain gap to whistleblower style** (§6.2). The model gives plausible but
   miscalibrated priors on transcripts that describe a third party's
   wrongdoing. Plan: gate the DeBERTa output behind a "domain detector" if a
   future release targets whistleblower triage.
2. **`fp16` training on A10G** can produce slightly different metrics across
   runs even with `set_seed(42)` because some CUDA kernels are non-deterministic.
   Observed run-to-run F1 variance ≈ ±0.005 in informal repeats.
3. **Module-level path resolution**: `Path(__file__).resolve().parents[2]`
   must NOT run at import time because Modal containers see a different file
   path; this is encapsulated in `_repo_root()` for safety.
4. **Multiple `verdict-deberta` ephemeral apps** can accumulate if `modal run`
   is invoked in parallel from different shells. Stop them with
   `modal app stop <APP_ID>` to avoid duplicate GPU billing.
5. **AVeriTeC label heuristic**: we map any label containing the substring
   `false` or equal to `refuted` → 1, and `true`/`supported` → 0. Other labels
   (e.g., `Conflicting Evidence/Cherrypicking`) are dropped. Approximately
   550 rows skipped this way.

---

## 10. Quick Reference — Where Is Everything?

| Concern | Path |
|---|---|
| Local model directory | `backend/models/deberta_deception/` |
| Inference adapter | `backend/verdict_pipeline/deberta_text_prior.py` |
| Wired into linguistic features | `backend/verdict_pipeline/linguistic.py::_text_deception_prior` |
| Used as Fusion feature 15 | `research-data/scripts/build_fusion_dataset.py::compute_text_prior` |
| Modal app definition | `research-data/scripts/modal_deberta.py` |
| Data prep | `research-data/scripts/prepare_deberta_data.py` |
| Training data (local) | `research-data/processed/deberta_{training,eval}_data.jsonl` |
| Modal cloud volume | `verdict-models` → `/models/deberta_deception/` |
| Final eval metrics | `backend/models/deberta_deception/training_metadata.json` |
| Conformal wrapper | `backend/verdict_pipeline/fusion.py::predict_full` |

---

*Document generated 2026-04-25. For contract-level invariants see `CONTRACT.md`.
For the broader pipeline architecture see `ML_TRAINING.md` and `TASKS.md`.*
