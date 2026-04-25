"""Evaluate a saved VerdictTextPrior-v1 Modal model artifact.

This is a post-training test harness. It reloads the final model from the
``verdict-m1-models`` Volume, rebuilds the deterministic validation/test splits
from ``verdict-m1-data``, runs calibrated inference, and writes a standalone
test report back to the model Volume.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import modal


APP_NAME = "verdict-text-prior-testing"
DATA_VOLUME_NAME = "verdict-m1-data"
MODEL_VOLUME_NAME = "verdict-m1-models"
DATA_MOUNT = Path("/mnt/verdict-data")
MODEL_MOUNT = Path("/mnt/verdict-models")
DEFAULT_RUN_NAME = "verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z"

app = modal.App(APP_NAME)
data_volume = modal.Volume.from_name(DATA_VOLUME_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "accelerate>=1.1,<2",
        "datasets>=3,<4",
        "numpy>=1.26,<3",
        "protobuf>=5,<6",
        "scikit-learn>=1.5,<2",
        "sentencepiece>=0.2,<0.3",
        "torch>=2.5,<3",
        "transformers>=4.46,<5",
    )
    .env({"TOKENIZERS_PARALLELISM": "false"})
)


@dataclass(frozen=True)
class EvalConfig:
    run_name: str = DEFAULT_RUN_NAME
    max_length: int = 256
    max_true: int = 50_000
    false_multiplier: float = 2.0
    seed: int = 42
    batch_size: int = 64


SMOKE_PROBES = [
    {
        "id": "flat_earth_false",
        "text": "The earth is flat and NASA invented all evidence of a round planet.",
        "expected": "resolved_false",
    },
    {
        "id": "moon_cheese_false",
        "text": "The moon is made entirely of green cheese.",
        "expected": "resolved_false",
    },
    {
        "id": "microchip_vaccine_false",
        "text": "Vaccines contain hidden tracking microchips used to monitor every person.",
        "expected": "resolved_false",
    },
    {
        "id": "earth_orbits_true",
        "text": "The earth orbits the sun once roughly every year.",
        "expected": "resolved_true",
    },
    {
        "id": "water_boils_true",
        "text": "At sea level, pure water boils at about 100 degrees Celsius.",
        "expected": "resolved_true",
    },
    {
        "id": "company_audit_true",
        "text": "The audited annual report stated that revenue increased by 12 percent.",
        "expected": "resolved_true",
    },
    {
        "id": "nixon_denial_probe",
        "text": "I am not a crook.",
        "expected": "diagnostic_only",
    },
    {
        "id": "careful_uncertain_probe",
        "text": "The available evidence is incomplete, and the claim has not yet been independently verified.",
        "expected": "diagnostic_only",
    },
]


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
                key = hashlib.sha1(_normalize_text(text).encode("utf-8")).hexdigest()
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


def _balanced_sample(rows: list[dict[str, Any]], cfg: EvalConfig) -> list[dict[str, Any]]:
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


def _softmax_positive(logits):
    import numpy as np

    shifted = logits - logits.max(axis=1, keepdims=True)
    exp = np.exp(shifted)
    return exp[:, 1] / exp.sum(axis=1)


def _expected_calibration_error(probs, labels, bins: int = 15) -> float:
    import numpy as np

    probs = np.asarray(probs)
    labels = np.asarray(labels)
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (probs >= lo) & (probs < hi if hi < 1.0 else probs <= hi)
        if not np.any(mask):
            continue
        ece += abs(probs[mask].mean() - labels[mask].mean()) * mask.mean()
    return float(ece)


def _predict_texts(model, tokenizer, texts: list[str], cfg: EvalConfig, temperature: float):
    import numpy as np
    import torch

    probs: list[float] = []
    model.eval()
    device = next(model.parameters()).device
    with torch.no_grad():
        for start in range(0, len(texts), cfg.batch_size):
            batch_texts = texts[start : start + cfg.batch_size]
            encoded = tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                max_length=cfg.max_length,
                return_tensors="pt",
            ).to(device)
            logits = model(**encoded).logits.detach().cpu().numpy() / temperature
            probs.extend(_softmax_positive(logits).tolist())
    return np.asarray(probs)


def _metrics(labels, probs, threshold: float) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import (
        accuracy_score,
        brier_score_loss,
        classification_report,
        confusion_matrix,
        f1_score,
        precision_recall_curve,
        roc_auc_score,
    )

    labels = np.asarray(labels)
    preds = (probs >= threshold).astype(int)
    precision_curve, recall_curve, thresholds = precision_recall_curve(labels, probs)
    macro_f1_by_threshold = []
    for candidate in thresholds:
        candidate_preds = (probs >= candidate).astype(int)
        macro_f1_by_threshold.append(f1_score(labels, candidate_preds, average="macro"))
    best_index = int(np.argmax(macro_f1_by_threshold)) if len(macro_f1_by_threshold) else 0
    return {
        "threshold": threshold,
        "accuracy": float(accuracy_score(labels, preds)),
        "roc_auc": float(roc_auc_score(labels, probs)),
        "brier_score": float(brier_score_loss(labels, probs)),
        "ece_15_bin": _expected_calibration_error(probs, labels, bins=15),
        "confusion_matrix": confusion_matrix(labels, preds).tolist(),
        "classification_report": classification_report(
            labels,
            preds,
            target_names=["resolved_true", "resolved_false"],
            output_dict=True,
            zero_division=0,
        ),
        "best_macro_f1_threshold": {
            "threshold": float(thresholds[best_index]) if len(thresholds) else threshold,
            "macro_f1": float(macro_f1_by_threshold[best_index])
            if len(macro_f1_by_threshold)
            else 0.0,
        },
        "pr_curve_summary": {
            "points": int(len(thresholds)),
            "max_precision": float(max(precision_curve)),
            "max_recall": float(max(recall_curve)),
        },
    }


def _dataset_slices(rows: list[dict[str, Any]], probs, threshold: float) -> dict[str, Any]:
    import numpy as np
    from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

    grouped: dict[str, list[int]] = defaultdict(list)
    for idx, row in enumerate(rows):
        grouped[row["dataset_id"]].append(idx)
    out: dict[str, Any] = {}
    for dataset_id, idxs in sorted(grouped.items()):
        labels = np.asarray([rows[i]["label"] for i in idxs])
        slice_probs = np.asarray([probs[i] for i in idxs])
        preds = (slice_probs >= threshold).astype(int)
        out[dataset_id] = {
            "rows": len(idxs),
            "label_counts": dict(Counter(rows[i]["label_name"] for i in idxs)),
            "accuracy": float(accuracy_score(labels, preds)),
            "macro_f1": float(f1_score(labels, preds, average="macro")),
            "roc_auc": float(roc_auc_score(labels, slice_probs))
            if len(set(labels.tolist())) == 2
            else None,
        }
    return out


def _load_threshold(calibration_path: Path) -> tuple[float, float, dict[str, Any]]:
    payload = json.loads(calibration_path.read_text(encoding="utf-8"))
    temperature = float(payload.get("temperature", 1.0))
    threshold_payload = (
        payload.get("best_threshold_on_validation")
        or payload.get("best_threshold_on_test")
        or {"threshold": payload.get("default_threshold", 0.5)}
    )
    threshold = float(threshold_payload.get("threshold", 0.5))
    return temperature, threshold, payload


@app.function(
    image=image,
    gpu="T4",
    timeout=60 * 60,
    startup_timeout=60 * 20,
    min_containers=0,
    max_containers=1,
    scaledown_window=2,
    volumes={
        str(DATA_MOUNT): data_volume.read_only(),
        str(MODEL_MOUNT): model_volume,
    },
)
def test_model_remote(config_payload: dict[str, Any]) -> dict[str, Any]:
    import numpy as np
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    cfg = EvalConfig(**config_payload)
    model_dir = MODEL_MOUNT / "runs" / cfg.run_name / "final"
    if not model_dir.exists():
        raise RuntimeError(f"Missing model directory: {model_dir}")

    temperature, threshold, calibration_payload = _load_threshold(
        model_dir / "verdict_calibration.json"
    )
    rows, source_stats = _read_claims(DATA_MOUNT / "text_claims")
    sampled = _balanced_sample(rows, cfg)
    splits = _split_rows(sampled, cfg.seed)

    tokenizer = AutoTokenizer.from_pretrained(model_dir)
    model = AutoModelForSequenceClassification.from_pretrained(model_dir)
    if torch.cuda.is_available():
        model = model.to("cuda")

    split_reports: dict[str, Any] = {}
    split_probs: dict[str, Any] = {}
    for name in ["validation", "test"]:
        split_rows = splits[name]
        labels = np.asarray([r["label"] for r in split_rows])
        probs = _predict_texts(model, tokenizer, [r["text"] for r in split_rows], cfg, temperature)
        split_probs[name] = {
            "min": float(probs.min()),
            "max": float(probs.max()),
            "mean": float(probs.mean()),
            "p05": float(np.quantile(probs, 0.05)),
            "p50": float(np.quantile(probs, 0.50)),
            "p95": float(np.quantile(probs, 0.95)),
        }
        split_reports[name] = {
            "rows": len(split_rows),
            "label_counts": dict(Counter(r["label_name"] for r in split_rows)),
            "at_calibration_threshold": _metrics(labels, probs, threshold),
            "at_0_5": _metrics(labels, probs, 0.5),
            "dataset_slices": _dataset_slices(split_rows, probs, threshold),
        }

    probe_probs = _predict_texts(
        model, tokenizer, [probe["text"] for probe in SMOKE_PROBES], cfg, temperature
    )
    probe_results = []
    for probe, probability in zip(SMOKE_PROBES, probe_probs.tolist()):
        expected = probe["expected"]
        predicted = "resolved_false" if probability >= threshold else "resolved_true"
        passed = (
            expected == "diagnostic_only"
            or expected == predicted
        )
        probe_results.append(
            {
                **probe,
                "probability_resolved_false": probability,
                "threshold": threshold,
                "predicted": predicted,
                "passed": passed,
            }
        )

    gate_checks = {
        "test_roc_auc_ge_0_95": split_reports["test"]["at_0_5"]["roc_auc"] >= 0.95,
        "test_macro_f1_ge_0_88": (
            split_reports["test"]["at_0_5"]["classification_report"]["macro avg"]["f1-score"]
            >= 0.88
        ),
        "test_ece_le_0_05": split_reports["test"]["at_0_5"]["ece_15_bin"] <= 0.05,
        "all_labeled_smoke_probes_pass": all(
            p["passed"] for p in probe_results if p["expected"] != "diagnostic_only"
        ),
    }

    report = {
        "report_name": "VerdictTextPrior-v1 post-training test",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "config": asdict(cfg),
        "modal_app": APP_NAME,
        "model_dir": str(model_dir),
        "calibration": calibration_payload,
        "effective_temperature": temperature,
        "effective_threshold": threshold,
        "source_stats": source_stats,
        "split_counts": {
            name: dict(Counter(row["label_name"] for row in split_rows))
            for name, split_rows in splits.items()
        },
        "probability_summaries": split_probs,
        "split_reports": split_reports,
        "smoke_probes": probe_results,
        "gate_checks": gate_checks,
        "passed_quality_gate": all(gate_checks.values()),
    }

    report_dir = MODEL_MOUNT / "runs" / cfg.run_name / "tests"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"post_training_eval_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    (report_dir / "latest_post_training_eval.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    model_volume.commit()
    report["modal_report_path"] = str(report_path.relative_to(MODEL_MOUNT))
    return report


@app.local_entrypoint()
def main(
    run_name: str = DEFAULT_RUN_NAME,
    batch_size: int = 64,
    seed: int = 42,
):
    cfg = EvalConfig(run_name=run_name, batch_size=batch_size, seed=seed)
    result = test_model_remote.remote(asdict(cfg))
    print(json.dumps(result, indent=2))

