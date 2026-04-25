"""Train VerdictTextPrior-v0 from collected text/fact-check rows.

This is a text-only prior for the current backend. It predicts whether a claim
text resembles resolved-false fact-check claims versus resolved-true claims.
It is not a multimodal deception model and should be blended conservatively.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = ROOT.parent
DEFAULT_OUT = PROJECT_ROOT / "backend" / "models" / "verdict_text_prior_v0.joblib"


def likely_english(text: str) -> bool:
    """Fast English-ish filter for this v0 model."""
    if len(text) < 20:
        return False
    letters = re.findall(r"[A-Za-z]", text)
    if len(letters) < 15:
        return False
    ascii_ratio = len(letters) / max(len(text), 1)
    common_hits = len(re.findall(r"\b(the|and|to|of|in|for|is|was|that|with|on)\b", text.lower()))
    return ascii_ratio >= 0.45 and common_hits >= 1


def iter_rows(processed_dir: Path):
    for path in sorted(processed_dir.glob("*.jsonl")):
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                if not line.strip():
                    continue
                row = json.loads(line)
                label = row.get("label_mapped")
                text = (row.get("claim_text") or "").strip()
                lang = (row.get("claim_language") or "en").lower()
                if label not in {"resolved_false", "resolved_true"}:
                    continue
                if lang not in {"en", "eng", ""}:
                    continue
                if not likely_english(text):
                    continue
                yield text, 1 if label == "resolved_false" else 0, row.get("dataset_id", "")


def load_examples(processed_dir: Path, max_per_label: int) -> tuple[list[str], list[int], dict]:
    false_items: list[tuple[str, int, str]] = []
    true_items: list[tuple[str, int, str]] = []
    dataset_counts: dict[str, int] = {}
    for text, label, dataset_id in iter_rows(processed_dir):
        dataset_counts[dataset_id] = dataset_counts.get(dataset_id, 0) + 1
        target = false_items if label == 1 else true_items
        if len(target) < max_per_label:
            target.append((text, label, dataset_id))
    examples = false_items + true_items
    texts = [x[0] for x in examples]
    labels = [x[1] for x in examples]
    stats = {
        "resolved_false": len(false_items),
        "resolved_true": len(true_items),
        "dataset_counts_after_filter": dataset_counts,
    }
    return texts, labels, stats


def train(texts: list[str], labels: list[int], seed: int) -> tuple[Pipeline, dict]:
    x_train, x_test, y_train, y_test = train_test_split(
        texts,
        labels,
        test_size=0.2,
        random_state=seed,
        stratify=labels,
    )
    model = Pipeline(
        steps=[
            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    strip_accents="unicode",
                    ngram_range=(1, 2),
                    min_df=3,
                    max_df=0.95,
                    max_features=250_000,
                    sublinear_tf=True,
                ),
            ),
            (
                "clf",
                LogisticRegression(
                    C=2.0,
                    class_weight="balanced",
                    max_iter=1000,
                    n_jobs=-1,
                    random_state=seed,
                ),
            ),
        ]
    )
    model.fit(x_train, y_train)
    probs = model.predict_proba(x_test)[:, 1]
    preds = (probs >= 0.5).astype(int)
    metrics = {
        "test_accuracy": accuracy_score(y_test, preds),
        "test_roc_auc": roc_auc_score(y_test, probs),
        "classification_report": classification_report(
            y_test,
            preds,
            target_names=["resolved_true", "resolved_false"],
            output_dict=True,
        ),
        "train_rows": len(x_train),
        "test_rows": len(x_test),
    }
    return model, metrics


def main() -> int:
    parser = argparse.ArgumentParser(description="Train VerdictTextPrior-v0.")
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=ROOT / "processed" / "text_claims",
    )
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--max-per-label", type=int, default=35_000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    texts, labels, stats = load_examples(args.processed_dir, args.max_per_label)
    if len(set(labels)) != 2:
        raise RuntimeError("Need both resolved_false and resolved_true examples.")
    model, metrics = train(texts, labels, args.seed)

    artifact = {
        "model_name": "VerdictTextPrior-v0",
        "description": (
            "Text-only resolved-false prior trained on fact-check corpora. "
            "Not a multimodal deception model."
        ),
        "positive_class": "resolved_false",
        "negative_class": "resolved_true",
        "stats": stats,
        "metrics": metrics,
        "model": model,
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(artifact, args.out, compress=3)

    metrics_path = ROOT / "manifests" / "verdict_text_prior_v0_metrics.json"
    metrics_payload = {k: v for k, v in artifact.items() if k != "model"}
    metrics_path.write_text(json.dumps(metrics_payload, indent=2), encoding="utf-8")
    print(json.dumps(metrics_payload, indent=2))
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
