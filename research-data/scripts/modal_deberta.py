"""
research-data/scripts/modal_deberta.py
=========================================
Modal app: fine-tune ``microsoft/deberta-v3-base`` (184M params) for binary
deception classification on a balanced mix of first-person + claim-style
deception corpora (prepared by ``prepare_deberta_data.py``).

Architecture:
    - 1 Modal app (``verdict-deberta``)
    - 1 Modal volume (``verdict-models``) for artifact persistence
    - 1 GPU function (A10G) ``train`` -- accepts training + eval JSONL bytes,
      fine-tunes, evaluates, saves to /models/deberta_deception/
    - 1 CPU function ``download_artifacts`` -- yields trained artifacts back
      to the local caller for integration into the backend.

Usage (locally, after ``modal token set``):

    # Step 1: prepare data (already done if you ran prepare_deberta_data.py)
    python research-data/scripts/prepare_deberta_data.py

    # Step 2: launch GPU training (returns when done; auto-shutdown after 60s idle)
    modal run research-data/scripts/modal_deberta.py::run_training

    # Step 3: pull the trained artifacts back to backend/models/
    modal run research-data/scripts/modal_deberta.py::pull_artifacts

Cost / safety:
    - GPU function has timeout=3600 (hard 1h ceiling) -- prevents runaways.
    - container_idle_timeout=60 -- container shuts down 60s after last RPC.
    - Volume costs are ~$0.15/GB/month; deberta-v3-base ckpt is ~700 MB.
"""
from __future__ import annotations

import json
from pathlib import Path

import modal

def _repo_root() -> Path:
    """Resolve the local repo root only when called from a local entrypoint.
    Inside the Modal container the file path has fewer parents, so this
    function must NOT be called at module-import time."""
    return Path(__file__).resolve().parents[2]

# ---------------------------------------------------------------------------
# Modal infrastructure
# ---------------------------------------------------------------------------

app = modal.App("verdict-deberta")
volume = modal.Volume.from_name("verdict-models", create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        # Pinning known-good combo. transformers + accelerate + sentencepiece
        # for DeBERTa-v3 tokenizer; evaluate for metrics.
        "torch==2.5.1",
        "transformers==4.46.2",
        "accelerate==1.1.1",
        "datasets==3.1.0",
        "evaluate==0.4.3",
        "sentencepiece==0.2.0",
        "scikit-learn==1.5.2",
        "tiktoken",
        "tf-keras",  # transformers needs this on some image variants
    )
    .env({"HF_HUB_DISABLE_TELEMETRY": "1", "TRANSFORMERS_NO_ADVISORY_WARNINGS": "1"})
)

VOLUME_MOUNT = "/models"
ARTIFACT_DIR = f"{VOLUME_MOUNT}/deberta_deception"


# ---------------------------------------------------------------------------
# Training function (runs on A10G GPU)
# ---------------------------------------------------------------------------

@app.function(
    image=image,
    gpu="A10G",
    volumes={VOLUME_MOUNT: volume},
    timeout=3600,                  # 1 hour hard cap
    scaledown_window=60,           # idle shutdown after 60s
    memory=16 * 1024,              # 16 GB
)
def train(
    training_jsonl: bytes,
    eval_jsonl: bytes,
    *,
    base_model: str = "microsoft/deberta-v3-base",
    num_epochs: int = 3,
    batch_size: int = 16,
    learning_rate: float = 2e-5,
    max_length: int = 256,
    warmup_ratio: float = 0.06,
) -> dict:
    """Fine-tune DeBERTa-v3-base on the supplied JSONL data, save to volume."""
    import numpy as np
    import torch
    from datasets import Dataset
    from sklearn.metrics import (
        accuracy_score,
        f1_score,
        roc_auc_score,
    )
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
        set_seed,
    )

    set_seed(42)
    print(f"[modal] CUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"[modal] GPU: {torch.cuda.get_device_name(0)}")

    # ---- Load JSONL datasets from supplied bytes ----
    def _parse_jsonl(b: bytes) -> list[dict]:
        rows = []
        for line in b.decode("utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                rows.append(json.loads(line))
            except Exception:
                continue
        return rows

    train_rows = _parse_jsonl(training_jsonl)
    eval_rows = _parse_jsonl(eval_jsonl)
    print(f"[data] train={len(train_rows)} eval={len(eval_rows)}")

    train_ds = Dataset.from_list(
        [{"text": r["text"], "label": int(r["label"])} for r in train_rows]
    )
    eval_ds = Dataset.from_list(
        [{"text": r["text"], "label": int(r["label"])} for r in eval_rows]
    )

    # ---- Tokenize ----
    print(f"[model] loading tokenizer + base model: {base_model}")
    tok = AutoTokenizer.from_pretrained(base_model, use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(
        base_model, num_labels=2,
        id2label={0: "truthful", 1: "deceptive"},
        label2id={"truthful": 0, "deceptive": 1},
    )

    def _tokenize(batch):
        return tok(batch["text"], truncation=True, max_length=max_length, padding=False)

    train_ds = train_ds.map(_tokenize, batched=True, remove_columns=["text"])
    eval_ds = eval_ds.map(_tokenize, batched=True, remove_columns=["text"])

    # ---- Metrics ----
    def _compute_metrics(eval_pred):
        logits, labels = eval_pred
        probs = torch.softmax(torch.tensor(logits), dim=-1)[:, 1].numpy()
        preds = (probs >= 0.5).astype(int)
        acc = accuracy_score(labels, preds)
        f1 = f1_score(labels, preds, average="binary")
        try:
            auc = roc_auc_score(labels, probs)
        except Exception:
            auc = float("nan")
        return {"accuracy": float(acc), "f1": float(f1), "roc_auc": float(auc)}

    # ---- Training args ----
    output_dir = "/tmp/deberta_run"
    args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size * 2,
        learning_rate=learning_rate,
        warmup_ratio=warmup_ratio,
        weight_decay=0.01,
        logging_steps=50,
        eval_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=1,
        load_best_model_at_end=True,
        metric_for_best_model="roc_auc",
        greater_is_better=True,
        fp16=True,
        report_to="none",
        seed=42,
    )

    trainer = Trainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tok,
        data_collator=DataCollatorWithPadding(tok),
        compute_metrics=_compute_metrics,
    )

    print("[train] starting fine-tune ...")
    trainer.train()

    # ---- Final eval ----
    eval_metrics = trainer.evaluate()
    print(f"[eval] final metrics: {eval_metrics}")

    # ---- Save to volume ----
    Path(ARTIFACT_DIR).mkdir(parents=True, exist_ok=True)
    trainer.save_model(ARTIFACT_DIR)
    tok.save_pretrained(ARTIFACT_DIR)
    metadata = {
        "base_model": base_model,
        "num_train_rows": len(train_rows),
        "num_eval_rows": len(eval_rows),
        "training_args": {
            "epochs": num_epochs,
            "batch_size": batch_size,
            "lr": learning_rate,
            "max_length": max_length,
            "warmup_ratio": warmup_ratio,
        },
        "final_eval": {k: float(v) if isinstance(v, (int, float)) else str(v)
                        for k, v in eval_metrics.items()},
    }
    Path(f"{ARTIFACT_DIR}/training_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    volume.commit()
    print(f"[saved] artifacts -> {ARTIFACT_DIR}")
    return metadata


# ---------------------------------------------------------------------------
# Local entrypoints
# ---------------------------------------------------------------------------

@app.local_entrypoint()
def run_training():
    """Local entry: read JSONL, dispatch to GPU, print final metrics."""
    repo = _repo_root()
    data_train = repo / "research-data" / "processed" / "deberta_training_data.jsonl"
    data_eval = repo / "research-data" / "processed" / "deberta_eval_data.jsonl"
    if not data_train.exists():
        raise SystemExit(f"[fatal] missing {data_train} -- run prepare_deberta_data.py first")
    train_bytes = data_train.read_bytes()
    eval_bytes = data_eval.read_bytes()
    print(f"[local] sending {len(train_bytes)/1024/1024:.2f} MB train + "
          f"{len(eval_bytes)/1024/1024:.2f} MB eval to Modal GPU ...")
    metadata = train.remote(train_bytes, eval_bytes)
    print("\n=== Training complete ===")
    print(json.dumps(metadata, indent=2))


@app.function(image=image, volumes={VOLUME_MOUNT: volume}, timeout=600)
def list_artifacts() -> list[str]:
    """List files in the artifact directory on the volume."""
    p = Path(ARTIFACT_DIR)
    if not p.exists():
        return []
    return [str(f.relative_to(p)) for f in p.rglob("*") if f.is_file()]


@app.function(image=image, volumes={VOLUME_MOUNT: volume}, timeout=600)
def read_artifact(rel_path: str) -> bytes:
    full = Path(ARTIFACT_DIR) / rel_path
    return full.read_bytes()


@app.local_entrypoint()
def pull_artifacts():
    """Download every file in the volume's deberta_deception/ folder to local backend/models/."""
    local_out_dir = _repo_root() / "backend" / "models" / "deberta_deception"
    local_out_dir.mkdir(parents=True, exist_ok=True)
    files = list_artifacts.remote()
    print(f"[local] pulling {len(files)} files from volume ...")
    for rel in files:
        data = read_artifact.remote(rel)
        out = local_out_dir / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        print(f"  pulled {rel} ({len(data)/1024/1024:.2f} MB)")
    print(f"\n[done] artifacts -> {local_out_dir}")
