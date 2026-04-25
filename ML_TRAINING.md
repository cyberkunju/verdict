# VERDICT — ML_TRAINING.md
## Background Training Brief — Run on Cloud GPU While Pipeline Builds

This document specifies optional ML training tasks that **upgrade signal
quality** without blocking the foreground hackathon build. Each task is
self-contained: dataset, recipe, expected output format, and the exact
integration point in the pipeline.

> **Hard rule:** `AGENT.md` §12 forbids foreground training. These tasks
> run on dedicated cloud GPU (Colab Pro / Kaggle / Lambda / RunPod). The
> foreground build proceeds with the classical pipeline regardless of
> whether any of these models complete in time. Drop-in upgrades only.

---

## Priority Order

| # | Model | Lift on demo | Time on A100 | Difficulty | Dataset license |
|---|---|---|---|---|---|
| **T1** | Linguistic deception classifier (DeBERTa-v3) | High | 30-60 min | Medium | Public |
| **T2** | Voice arousal classifier (wav2vec2) | Medium | 60-90 min | Medium | Public |
| **T3** | Deep rPPG (PhysNet) | Medium-High | 2-4 hrs | Hard | Research |
| **T4** | Micro-expression detector | Low | 1-2 hrs | Hard | Research |

**Run T1 first.** Largest demo lift, smallest training effort, slots cleanly
into `verdict_pipeline/linguistic.py` via a single optional call.

---

## Universal Output Convention

Every trained model drops weights into `backend/models/<model_name>/`:

```
backend/models/
├── deception_lm/                # T1
│   ├── config.json
│   ├── model.safetensors
│   └── tokenizer/
├── voice_arousal/               # T2
│   ├── config.json
│   ├── preprocessor_config.json
│   └── model.safetensors
├── rppg_physnet/                # T3
│   └── physnet.pt
└── microexpr/                   # T4
    └── microexpr.pt
```

Each model exports a single Python function the pipeline knows how to call
(the integration sections below). If weights are missing, the pipeline
silently falls back to the classical estimator.

`backend/models/` is **gitignored** in the root `.gitignore` (covers
`*.bin`, `*.pt`, `*.safetensors`, `*.onnx`, `models/`). Push to a separate
HuggingFace repo and reference by ID, or attach as GitHub Release asset.

---

## T1 — Linguistic Deception Classifier (DeBERTa-v3-base)

### Why

The hand-crafted hedging / pronoun heuristics in `linguistic.py` capture
only surface cues. A fine-tuned transformer on labeled deception transcripts
learns subtle markers: distancing constructions, presupposition shifts,
verbal-immediacy collapse, negation patterns, hedged certainty. Outputs a
single calibrated probability we can fold into the `deception` score with
a 0.05-0.10 weight bump.

### Dataset

Use any one (or a union):

- **Real-Life Trial Lies** (Pérez-Rosas et al. 2015) — 121 video clips
  with court-verified labels and clean transcripts. Cite:
  `Deception Detection using Real-life Trial Data, ICMI 2015`.
- **Diplomacy** (Peskov et al. 2020) — chat-game deception with
  `~189k` messages and self-reported lie/truth labels. Permissive license.
  Best for high data volume.
- **Cornell Movie-Deception Detection** (Ott et al. 2011) — 800 truthful
  and 800 deceptive hotel-review sentences. Synthetic but useful for
  augmentation.

Combine: train on Diplomacy (volume) → fine-tune on Real-Life Trials
(domain match).

### Recipe

```python
# train_t1.py — run on Colab Pro / Kaggle T4
from transformers import (
    AutoTokenizer, AutoModelForSequenceClassification,
    Trainer, TrainingArguments,
)
from datasets import load_dataset, concatenate_datasets

MODEL = "microsoft/deberta-v3-base"
tokenizer = AutoTokenizer.from_pretrained(MODEL)
model = AutoModelForSequenceClassification.from_pretrained(MODEL, num_labels=2)

# Load + harmonize datasets to {text, label} where label: 0=truth, 1=deception.
diplomacy = load_dataset("convokit/diplomacy")  # adjust loader
trials = load_dataset("path/to/realtrial")  # local prep required

def tok(b): return tokenizer(b["text"], truncation=True, padding="max_length", max_length=256)
diplomacy = diplomacy.map(tok, batched=True)
trials = trials.map(tok, batched=True)
ds = concatenate_datasets([diplomacy["train"], trials["train"]]).shuffle(seed=42)

args = TrainingArguments(
    output_dir="./ckpt",
    num_train_epochs=3,
    per_device_train_batch_size=16,
    learning_rate=2e-5,
    warmup_ratio=0.06,
    weight_decay=0.01,
    fp16=True,
    eval_strategy="epoch",
    save_strategy="epoch",
    load_best_model_at_end=True,
    metric_for_best_model="f1",
)

trainer = Trainer(model=model, args=args, train_dataset=ds,
                  eval_dataset=trials["test"], tokenizer=tokenizer)
trainer.train()
trainer.save_model("backend/models/deception_lm")
tokenizer.save_pretrained("backend/models/deception_lm")
```

### Calibration

After training, run Platt scaling on the dev set so the output probability
is well-calibrated:

```python
from sklearn.linear_model import LogisticRegression
import numpy as np
logits = np.load("dev_logits.npy")
y = np.load("dev_y.npy")
lr = LogisticRegression().fit(logits, y)
np.save("backend/models/deception_lm/calibration.npy",
        np.array([lr.coef_[0,0], lr.intercept_[0]]))
```

### Output schema

```json
{
  "deception_probability": 0.83,
  "model": "deberta-v3-base-deception",
  "calibrated": true,
  "model_version": "t1.v1"
}
```

### Pipeline integration

`verdict_pipeline/linguistic.py::extract` already returns a
`LinguisticFeatures` dataclass. Add the optional probability field:

```python
# in linguistic.py, add after _extract_spacy or _extract_regex_fallback:
def _maybe_lm_probability(text: str) -> float | None:
    try:
        from transformers import pipeline
        from .config import BACKEND_DIR
        p = (BACKEND_DIR / "models" / "deception_lm")
        if not p.exists():
            return None
        clf = pipeline("text-classification", model=str(p), tokenizer=str(p))
        out = clf(text, truncation=True)[0]
        return float(out["score"]) if out["label"].lower().startswith("decep") \
               else 1.0 - float(out["score"])
    except Exception:
        return None
```

Then in `verdict_pipeline/score.py::compute_scores`, accept an optional
`lm_deception_prob: float | None = None` parameter. When provided, blend:

```python
if lm_deception_prob is not None:
    deception = 0.85 * deception + 0.15 * lm_deception_prob  # weighted blend
```

---

## T2 — Voice Arousal / Stress Classifier (wav2vec2-base)

### Why

Praat jitter/shimmer captures local periodicity but misses prosodic stress
patterns. wav2vec2 fine-tuned on emotional-arousal datasets gives a
continuous arousal score (0-1) that improves the `stress` composite.

### Dataset

- **RAVDESS** (24 actors × 8 emotions) — primary, public. Map emotions to
  arousal scale: neutral=0.1, calm=0.2, happy=0.7, sad=0.4, angry=0.9,
  fearful=0.85, disgust=0.75, surprised=0.8.
- **IEMOCAP** (if access) — adds dimensional valence/arousal labels.
- **CREMA-D** — additional speaker variety.

### Recipe

```python
from transformers import (
    AutoFeatureExtractor, AutoModelForAudioClassification,
    Trainer, TrainingArguments,
)

MODEL = "facebook/wav2vec2-base"
feat = AutoFeatureExtractor.from_pretrained(MODEL)
model = AutoModelForAudioClassification.from_pretrained(MODEL, num_labels=1,
                                                        problem_type="regression")

# Resample audio to 16kHz, label = arousal in [0, 1].
# Train with MSE loss, 5 epochs, lr=5e-5, batch=8, fp16.
args = TrainingArguments(
    output_dir="./ckpt",
    num_train_epochs=5,
    per_device_train_batch_size=8,
    learning_rate=5e-5,
    warmup_ratio=0.1,
    fp16=True,
    save_strategy="epoch",
)
trainer = Trainer(model=model, args=args, train_dataset=ds_train,
                  eval_dataset=ds_val, tokenizer=feat)
trainer.train()
trainer.save_model("backend/models/voice_arousal")
feat.save_pretrained("backend/models/voice_arousal")
```

### Output schema

```json
{
  "arousal": 0.78,
  "model": "wav2vec2-arousal",
  "model_version": "t2.v1"
}
```

### Pipeline integration

In `verdict_pipeline/extract_voice.py`, add optional path that loads the
model and adds an `arousal` field to `VoiceFeatures` (via a new optional
attribute). Then in `score.py` blend:

```python
if voice_arousal is not None:
    stress = 0.80 * stress + 0.20 * voice_arousal
```

The contract schema does not need to change — `arousal` is internal-only.

---

## T3 — Deep rPPG (PhysNet)

### Why

Multi-ROI POS in `extract_rppg.py` works well on modern HD footage but
struggles on archival low-light interlaced video. PhysNet (3D-CNN over
spatiotemporal face crops) is robust to compression and lighting.

### Dataset

- **UBFC-rPPG** — 42 subjects, ground-truth contact PPG. Standard benchmark.
  Request access from the Université Bourgogne Franche-Comté page.
- **PURE** — 10 subjects, six controlled head-motion conditions.
- **MMPD** (mobile) — useful augmentation.

### Recipe

Use the **rPPG-Toolbox** (https://github.com/ubicomplab/rPPG-Toolbox).
It has a ready-made PhysNet trainer. Steps:

```bash
git clone https://github.com/ubicomplab/rPPG-Toolbox
cd rPPG-Toolbox
conda env create -f environment.yml
conda activate rppg-toolbox

# Edit configs/train_configs/UBFC-rPPG_UBFC-rPPG_PHYSNET_BASIC.yaml
# Set DATA_PATH to your UBFC dataset.
python main.py --config_file ./configs/train_configs/UBFC-rPPG_UBFC-rPPG_PHYSNET_BASIC.yaml
```

The trained checkpoint is `final_model_PhysNet.pth`. Copy to
`backend/models/rppg_physnet/physnet.pt`.

### Output schema

The model produces a per-window pulse waveform; HR is extracted by FFT just
like the classical path. The integration only requires swapping the
upstream pulse signal source.

### Pipeline integration

In `verdict_pipeline/extract_rppg.py`, add a deep-path branch:

```python
def _physnet_pulse(video_path: Path) -> np.ndarray | None:
    try:
        import torch
        from .config import BACKEND_DIR
        ckpt = BACKEND_DIR / "models" / "rppg_physnet" / "physnet.pt"
        if not ckpt.exists():
            return None
        # Load model, preprocess (face crops 128x128, T frames), forward,
        # return 1D pulse signal at fps.
        ...
    except Exception:
        return None
```

If `_physnet_pulse` returns a signal, skip POS entirely and use the
deep pulse as the fused signal. Mark `quality = "real"` (still real, just
deeper). All downstream HR / HRV / SNR code already works on a 1D pulse.

---

## T4 — Micro-Expression Detector (Optional)

### Why

Adds the ability to detect sub-500 ms AU activations that classical Py-Feat
sampling at 10 fps misses. Lifts AU15/AU14 sensitivity for terse denials.

### Dataset

- **CASME II** — 247 micro-expression samples, 200 fps. Apply via SMIC.
- **SAMM** — 159 samples, multiple ethnicities. Apply via Manchester.

### Recipe

Train a 3D-ResNet on cropped face video clips at native 200 fps,
classifying onset / apex / offset frames per AU. Output AU activation
intensity 0-5 sampled at the source fps.

### Pipeline integration

Add to `verdict_pipeline/extract_facial.py` a `_microexpr_aus()` function
that, when weights exist, augments the per-frame AU intensities before the
max-aggregation step. No schema change required.

---

## Evaluation Gate (When to Integrate vs Skip)

A trained model is **only** integrated into the demo if it meets all of:

| Gate | T1 | T2 | T3 | T4 |
|---|---|---|---|---|
| Held-out F1 / MAE | F1 ≥ 0.72 | MAE ≤ 0.18 | MAE ≤ 5 bpm | F1 ≥ 0.65 |
| Inference time on CPU | ≤ 1 s/clip | ≤ 2 s/clip | ≤ 8 s/clip | ≤ 6 s/clip |
| Adds a `signal_quality` flag | yes | yes | yes | yes |
| Demo improvement on Nixon + SBF | yes | yes | yes | n/a |

If the gate is missed, drop the model, keep the classical pipeline. No
"it kinda works" integrations.

---

## Quick Cloud Recipes

### Colab Pro

```python
!pip install -U transformers datasets accelerate evaluate
!pip install -q torchaudio librosa
# Mount Google Drive, save weights there.
```

### Kaggle T4 / P100

Free 30 GPU-hours/week. Good for T1.

### RunPod / Lambda Labs

Best for T3 — A100 40GB, hourly billing, attaches to your HuggingFace.

---

## Reporting Back

When a model finishes training, drop a message in `TASKS.md`
`### Open Issues` with:

- Model name and version
- Held-out metric
- Path to weights (HF Hub ID or release asset URL)
- Whether the gate above passed

Person 1 then wires it into the relevant `extract_*` module on a
`pipeline/lm-deception` (or similar) branch. **Never** integrate a fresh
model less than 2 hours before submission.
