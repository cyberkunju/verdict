"""Train VerdictTextPrior-v1 on Modal GPU and persist artifacts to Modal Volume.

Run from the repository root after uploading processed text claims to the
``verdict-m1-data`` Modal Volume:

    modal run M1-data/scripts/train_text_prior_modal.py --model-name microsoft/deberta-v3-base

The remote function is intentionally ephemeral. It keeps no warm containers and
persists only dataset manifests, checkpoints, tokenizer files, and final model
artifacts under the ``verdict-m1-models`` Modal Volume.
"""

from __future__ import annotations

import hashlib
import inspect
import json
import math
import random
import re
import shutil
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal


APP_NAME = "verdict-text-prior-training"
DATA_VOLUME_NAME = "verdict-m1-data"
MODEL_VOLUME_NAME = "verdict-m1-models"
DATA_MOUNT = Path("/mnt/verdict-data")
MODEL_MOUNT = Path("/mnt/verdict-models")

app = modal.App(APP_NAME)
data_volume = modal.Volume.from_name(DATA_VOLUME_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "accelerate>=1.1,<2",
        "datasets>=3,<4",
        "evaluate>=0.4,<0.5",
        "hf_transfer>=0.1,<0.2",
        "numpy>=1.26,<3",
        "protobuf>=5,<6",
        "scikit-learn>=1.5,<2",
        "sentencepiece>=0.2,<0.3",
        "torch>=2.5,<3",
        "transformers>=4.46,<5",
    )
    .env(
        {
            "HF_HUB_ENABLE_HF_TRANSFER": "1",
            "TOKENIZERS_PARALLELISM": "false",
        }
    )
)


@dataclass(frozen=True)
class TrainConfig:
    model_name: str = "microsoft/deberta-v3-base"
    max_length: int = 256
    max_true: int = 50_000
    false_multiplier: float = 2.0
    seed: int = 42
    epochs: float = 3.0
    learning_rate: float = 2e-5
    weight_decay: float = 0.01
    train_batch_size: int = 16
    eval_batch_size: int = 32
    gradient_accumulation_steps: int = 2
    warmup_ratio: float = 0.06
    eval_steps: int = 250
    save_steps: int = 250
    early_stopping_patience: int = 3


def _utc_run_name(model_name: str) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    clean_model = re.sub(r"[^a-zA-Z0-9_.-]+", "-", model_name).strip("-")
    return f"verdict-text-prior-v1-{clean_model}-{stamp}"


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _likely_english(text: str) -> bool:
    if len(text) < 20:
        return False
    letters = re.findall(r"[A-Za-z]", text)
    if len(letters) < 15:
        return False
    ascii_ratio = len(letters) / max(len(text), 1)
    common_hits = len(
        re.findall(r"\b(the|and|to|of|in|for|is|was|that|with|on)\b", text.lower())
    )
    return ascii_ratio >= 0.45 and common_hits >= 1


def _read_claims(input_dir: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    stats: dict[str, Any] = {
        "input_dir": str(input_dir),
        "files": [],
        "raw_rows": 0,
        "kept_rows": 0,
        "dedupe_drops": 0,
        "label_drops": 0,
        "language_drops": 0,
        "english_filter_drops": 0,
        "dataset_counts": {},
        "label_counts": {},
    }

    for path in sorted(input_dir.rglob("*.jsonl")):
        file_rows = 0
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                stats["raw_rows"] += 1
                file_rows += 1
                row = json.loads(line)
                label = row.get("label_mapped")
                if label not in {"resolved_false", "resolved_true"}:
                    stats["label_drops"] += 1
                    continue
                lang = (row.get("claim_language") or "en").lower()
                if lang not in {"en", "eng", ""}:
                    stats["language_drops"] += 1
                    continue
                text = (row.get("claim_text") or "").strip()
                if not _likely_english(text):
                    stats["english_filter_drops"] += 1
                    continue
                norm = _normalize_text(text)
                key = hashlib.sha1(norm.encode("utf-8")).hexdigest()
                if key in seen:
                    stats["dedupe_drops"] += 1
                    continue
                seen.add(key)
                dataset_id = row.get("dataset_id") or path.stem
                rows.append(
                    {
                        "text": text,
                        "label": 1 if label == "resolved_false" else 0,
                        "label_name": label,
                        "dataset_id": dataset_id,
                        "source_path": path.name,
                    }
                )
        stats["files"].append({"name": path.name, "raw_rows": file_rows})

    stats["kept_rows"] = len(rows)
    stats["dataset_counts"] = dict(Counter(r["dataset_id"] for r in rows))
    stats["label_counts"] = dict(Counter(r["label_name"] for r in rows))
    return rows, stats


def _balanced_sample(rows: list[dict[str, Any]], cfg: TrainConfig) -> list[dict[str, Any]]:
    true_rows = [r for r in rows if r["label"] == 0]
    false_rows = [r for r in rows if r["label"] == 1]
    rng = random.Random(cfg.seed)
    rng.shuffle(true_rows)
    rng.shuffle(false_rows)

    true_limit = min(cfg.max_true, len(true_rows))
    false_limit = min(len(false_rows), max(1, int(true_limit * cfg.false_multiplier)))
    sampled = true_rows[:true_limit] + false_rows[:false_limit]
    rng.shuffle(sampled)
    return sampled


def _split_rows(rows: list[dict[str, Any]], seed: int) -> dict[str, list[dict[str, Any]]]:
    by_label: dict[int, list[dict[str, Any]]] = {0: [], 1: []}
    for row in rows:
        by_label[row["label"]].append(row)
    rng = random.Random(seed)
    splits = {"train": [], "validation": [], "test": []}
    for label_rows in by_label.values():
        rng.shuffle(label_rows)
        n = len(label_rows)
        n_test = max(1, math.floor(n * 0.10))
        n_val = max(1, math.floor(n * 0.10))
        splits["test"].extend(label_rows[:n_test])
        splits["validation"].extend(label_rows[n_test : n_test + n_val])
        splits["train"].extend(label_rows[n_test + n_val :])
    for split_rows in splits.values():
        rng.shuffle(split_rows)
    return splits


def _softmax_positive(logits: Any) -> Any:
    import numpy as np

    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp[:, 1] / exp.sum(axis=1)


def _expected_calibration_error(probs: Any, labels: Any, bins: int = 15) -> float:
    import numpy as np

    probs = np.asarray(probs)
    labels = np.asarray(labels)
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        if not np.any(mask):
            continue
        confidence = probs[mask].mean()
        accuracy = labels[mask].mean()
        ece += abs(confidence - accuracy) * (mask.mean())
    return float(ece)


def _best_threshold(probs: Any, labels: Any) -> dict[str, float]:
    import numpy as np
    from sklearn.metrics import f1_score

    best = {"threshold": 0.5, "macro_f1": -1.0}
    for threshold in np.linspace(0.05, 0.95, 181):
        preds = (probs >= threshold).astype(int)
        macro_f1 = float(f1_score(labels, preds, average="macro"))
        if macro_f1 > best["macro_f1"]:
            best = {"threshold": float(threshold), "macro_f1": macro_f1}
    return best


def _temperature_scale(validation_logits: Any, validation_labels: Any) -> float:
    import torch

    logits = torch.tensor(validation_logits, dtype=torch.float32)
    labels = torch.tensor(validation_labels, dtype=torch.long)
    log_temperature = torch.nn.Parameter(torch.zeros(()))
    optimizer = torch.optim.LBFGS([log_temperature], lr=0.05, max_iter=75)
    loss_fn = torch.nn.CrossEntropyLoss()

    def closure():
        optimizer.zero_grad()
        temperature = torch.exp(log_temperature).clamp(0.25, 8.0)
        loss = loss_fn(logits / temperature, labels)
        loss.backward()
        return loss

    optimizer.step(closure)
    return float(torch.exp(log_temperature).clamp(0.25, 8.0).detach().cpu().item())


@app.function(
    image=image,
    gpu="L40S",
    timeout=60 * 60 * 8,
    startup_timeout=60 * 30,
    min_containers=0,
    max_containers=1,
    scaledown_window=2,
    volumes={
        str(DATA_MOUNT): data_volume.read_only(),
        str(MODEL_MOUNT): model_volume,
    },
)
def train_text_prior_remote(config_payload: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    from datasets import Dataset
    from sklearn.metrics import (
        accuracy_score,
        brier_score_loss,
        classification_report,
        precision_recall_fscore_support,
        roc_auc_score,
    )
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        EarlyStoppingCallback,
        Trainer,
        TrainingArguments,
    )

    cfg = TrainConfig(**config_payload)
    torch.manual_seed(cfg.seed)
    random.seed(cfg.seed)
    np.random.seed(cfg.seed)

    rows, source_stats = _read_claims(DATA_MOUNT / "text_claims")
    sampled = _balanced_sample(rows, cfg)
    splits = _split_rows(sampled, cfg.seed)
    run_name = _utc_run_name(cfg.model_name)
    run_dir = MODEL_MOUNT / "runs" / run_name
    final_dir = run_dir / "final"
    run_dir.mkdir(parents=True, exist_ok=True)

    dataset_manifest = {
        "run_name": run_name,
        "config": asdict(cfg),
        "source_stats": source_stats,
        "sampled_rows": len(sampled),
        "split_counts": {
            name: dict(Counter(row["label_name"] for row in split_rows))
            for name, split_rows in splits.items()
        },
    }
    (run_dir / "dataset_manifest.json").write_text(
        json.dumps(dataset_manifest, indent=2), encoding="utf-8"
    )

    train_ds = Dataset.from_list(splits["train"])
    val_ds = Dataset.from_list(splits["validation"])
    test_ds = Dataset.from_list(splits["test"])

    tokenizer = AutoTokenizer.from_pretrained(cfg.model_name, use_fast=True)

    def tokenize(batch: dict[str, list[Any]]) -> dict[str, Any]:
        return tokenizer(batch["text"], truncation=True, max_length=cfg.max_length)

    train_ds = train_ds.map(tokenize, batched=True, remove_columns=["text", "label_name", "dataset_id", "source_path"])
    val_ds = val_ds.map(tokenize, batched=True, remove_columns=["text", "label_name", "dataset_id", "source_path"])
    test_ds = test_ds.map(tokenize, batched=True, remove_columns=["text", "label_name", "dataset_id", "source_path"])
    train_ds = train_ds.rename_column("label", "labels")
    val_ds = val_ds.rename_column("label", "labels")
    test_ds = test_ds.rename_column("label", "labels")

    label_counts = Counter(row["label"] for row in splits["train"])
    total = sum(label_counts.values())
    class_weights = torch.tensor(
        [total / (2 * label_counts[0]), total / (2 * label_counts[1])],
        dtype=torch.float32,
    )

    model = AutoModelForSequenceClassification.from_pretrained(
        cfg.model_name,
        num_labels=2,
        id2label={0: "resolved_true", 1: "resolved_false"},
        label2id={"resolved_true": 0, "resolved_false": 1},
    )

    def compute_metrics(eval_pred: Any) -> dict[str, float]:
        logits, labels = eval_pred
        probs = _softmax_positive(logits)
        preds = np.argmax(logits, axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(
            labels, preds, average="binary", zero_division=0
        )
        macro = precision_recall_fscore_support(
            labels, preds, average="macro", zero_division=0
        )
        return {
            "accuracy": float(accuracy_score(labels, preds)),
            "roc_auc": float(roc_auc_score(labels, probs)),
            "precision_false": float(precision),
            "recall_false": float(recall),
            "f1_false": float(f1),
            "macro_f1": float(macro[2]),
        }

    training_kwargs: dict[str, Any] = {
        "output_dir": str(run_dir / "checkpoints"),
        "learning_rate": cfg.learning_rate,
        "per_device_train_batch_size": cfg.train_batch_size,
        "per_device_eval_batch_size": cfg.eval_batch_size,
        "gradient_accumulation_steps": cfg.gradient_accumulation_steps,
        "num_train_epochs": cfg.epochs,
        "weight_decay": cfg.weight_decay,
        "warmup_ratio": cfg.warmup_ratio,
        "logging_steps": 50,
        "eval_steps": cfg.eval_steps,
        "save_steps": cfg.save_steps,
        "save_total_limit": 2,
        "load_best_model_at_end": True,
        "metric_for_best_model": "eval_macro_f1",
        "greater_is_better": True,
        "report_to": [],
        "seed": cfg.seed,
        "data_seed": cfg.seed,
        "bf16": bool(torch.cuda.is_available() and torch.cuda.is_bf16_supported()),
        "fp16": bool(torch.cuda.is_available() and not torch.cuda.is_bf16_supported()),
        "gradient_checkpointing": False,
    }
    signature = inspect.signature(TrainingArguments.__init__).parameters
    if "eval_strategy" in signature:
        training_kwargs["eval_strategy"] = "steps"
    else:
        training_kwargs["evaluation_strategy"] = "steps"
    training_kwargs["save_strategy"] = "steps"

    args = TrainingArguments(**training_kwargs)

    class WeightedTrainer(Trainer):
        def __init__(self, *args: Any, class_weights: torch.Tensor, **kwargs: Any):
            super().__init__(*args, **kwargs)
            self.class_weights = class_weights

        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.get("logits")
            weights = self.class_weights.to(logits.device)
            loss = torch.nn.CrossEntropyLoss(weight=weights)(logits, labels)
            return (loss, outputs) if return_outputs else loss

    trainer = WeightedTrainer(
        model=model,
        args=args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=cfg.early_stopping_patience)],
        class_weights=class_weights,
    )

    trainer.train()

    validation_pred = trainer.predict(val_ds, metric_key_prefix="validation")
    test_pred = trainer.predict(test_ds, metric_key_prefix="test")
    temperature = _temperature_scale(validation_pred.predictions, validation_pred.label_ids)
    validation_probs = _softmax_positive(validation_pred.predictions / temperature)
    validation_threshold = _best_threshold(validation_probs, validation_pred.label_ids)
    calibrated_test_logits = test_pred.predictions / temperature
    test_probs = _softmax_positive(calibrated_test_logits)
    test_preds = (test_probs >= 0.5).astype(int)
    test_preds_at_validation_threshold = (
        test_probs >= validation_threshold["threshold"]
    ).astype(int)

    test_metrics = {
        "accuracy_at_0_5": float(accuracy_score(test_pred.label_ids, test_preds)),
        "roc_auc": float(roc_auc_score(test_pred.label_ids, test_probs)),
        "brier_score": float(brier_score_loss(test_pred.label_ids, test_probs)),
        "ece_15_bin": _expected_calibration_error(test_probs, test_pred.label_ids, bins=15),
        "temperature": temperature,
        "best_threshold_on_validation": validation_threshold,
        "classification_report_at_0_5": classification_report(
            test_pred.label_ids,
            test_preds,
            target_names=["resolved_true", "resolved_false"],
            output_dict=True,
            zero_division=0,
        ),
        "classification_report_at_validation_threshold": classification_report(
            test_pred.label_ids,
            test_preds_at_validation_threshold,
            target_names=["resolved_true", "resolved_false"],
            output_dict=True,
            zero_division=0,
        ),
    }

    final_dir.mkdir(parents=True, exist_ok=True)
    trainer.save_model(str(final_dir))
    tokenizer.save_pretrained(str(final_dir))
    (final_dir / "verdict_calibration.json").write_text(
        json.dumps(
            {
                "positive_class": "resolved_false",
                "negative_class": "resolved_true",
                "temperature": temperature,
                "default_threshold": 0.5,
                "best_threshold_on_validation": validation_threshold,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    summary = {
        "model_name": "VerdictTextPrior-v1",
        "description": (
            "Transformer text-only resolved-false prior trained on M1 fact-check "
            "claims. Not a multimodal deception model."
        ),
        "run_name": run_name,
        "modal_app": APP_NAME,
        "modal_model_volume": MODEL_VOLUME_NAME,
        "modal_model_path": f"/runs/{run_name}/final",
        "config": asdict(cfg),
        "dataset_manifest": dataset_manifest,
        "validation_metrics": validation_pred.metrics,
        "test_metrics": test_metrics,
    }
    shutil.rmtree(run_dir / "checkpoints", ignore_errors=True)
    (run_dir / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    shutil.copyfile(run_dir / "metrics.json", final_dir / "metrics.json")
    model_volume.commit()
    return summary


@app.local_entrypoint()
def main(
    model_name: str = "microsoft/deberta-v3-base",
    max_length: int = 256,
    max_true: int = 50_000,
    false_multiplier: float = 2.0,
    epochs: float = 3.0,
    learning_rate: float = 2e-5,
    seed: int = 42,
):
    cfg = TrainConfig(
        model_name=model_name,
        max_length=max_length,
        max_true=max_true,
        false_multiplier=false_multiplier,
        epochs=epochs,
        learning_rate=learning_rate,
        seed=seed,
    )
    result = train_text_prior_remote.remote(asdict(cfg))
    print(json.dumps(result, indent=2))
