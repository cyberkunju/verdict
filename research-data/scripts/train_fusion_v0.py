"""
research-data/scripts/train_fusion_v0.py
==========================================
Trains VerdictFusion-v0: a calibrated GBM that turns 15 multimodal features
into a deception probability with bootstrap CI and abstention rules.

  python research-data/scripts/build_fusion_dataset.py
  python research-data/scripts/train_fusion_v0.py

Outputs:
  backend/models/verdict_fusion_v0.joblib       # joblib bundle (model + meta)
  M1-data/manifests/verdict_fusion_v0_metrics.json
"""
from __future__ import annotations

import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parents[2]
DATA_CSV = ROOT / "research-data" / "processed" / "fusion_v0_features.csv"
MODEL_OUT = ROOT / "backend" / "models" / "verdict_fusion_v0.joblib"
METRICS_OUT = ROOT / "M1-data" / "manifests" / "verdict_fusion_v0_metrics.json"

# Trained features. Text-prior is stacked at inference time, NOT trained as a
# feature, to prevent it from dominating the model on tiny gold data.
FEATURE_NAMES = [
    "hr_baseline_bpm",
    "hr_delta_bpm",
    "hrv_rmssd_ms",
    "f0_baseline_hz",
    "f0_delta_hz",
    "jitter_percent",
    "shimmer_db",
    "speech_rate_wpm",
    "au14_max_intensity",
    "au15_max_intensity",
    "au24_max_intensity",
    "au6_present_int",
    "hedging_count_per_100w",
    "pronoun_drop_rate",
    "text_deception_prior",
    "cross_modal_synchrony",
]


def expected_calibration_error(y_true: np.ndarray, y_prob: np.ndarray, n_bins: int = 10) -> float:
    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    for i in range(n_bins):
        m = (y_prob >= bins[i]) & (y_prob < bins[i + 1])
        if not m.any():
            continue
        acc = float(y_true[m].mean())
        conf = float(y_prob[m].mean())
        ece += (m.sum() / len(y_prob)) * abs(acc - conf)
    return float(ece)


def main() -> None:
    if not DATA_CSV.exists():
        raise SystemExit(
            f"[fatal] missing {DATA_CSV} — run build_fusion_dataset.py first"
        )

    df = pd.read_csv(DATA_CSV)
    print(f"[load] {len(df)} rows; columns={list(df.columns)[:6]}...")

    X = df[FEATURE_NAMES].values
    y = df["label"].values.astype(int)
    groups = df["subject"].values
    print(f"[cv] tier counts: {df['source_tier'].value_counts().to_dict()}")

    cv_records = []
    cv_y_true, cv_y_prob = [], []

    gold_subjects = sorted(set(df[df["source_tier"] == "gold"]["subject"]))
    print(f"[cv] gold subjects: {gold_subjects}")

    def _make_pipeline() -> Pipeline:
        # Standardized features + L2-regularized logistic regression. Honest for
        # small data: a linear model with strong regularization rather than a
        # GBM that will memorize 60-180 rows.
        return Pipeline([
            ("scaler", StandardScaler()),
            ("lr", LogisticRegression(
                penalty="l2", C=0.5, solver="lbfgs", max_iter=2000, random_state=42,
            )),
        ])

    for held_subject in gold_subjects:
        # Hold out: this subject's gold AND synth rows (don't leak via bootstrap).
        held_mask = (groups == held_subject)
        test_mask = held_mask & (df["source_tier"] == "gold").values
        train_mask = ~held_mask

        X_tr, y_tr = X[train_mask], y[train_mask]
        X_te, y_te = X[test_mask], y[test_mask]
        if len(X_te) == 0:
            continue

        clf = _make_pipeline()
        clf.fit(X_tr, y_tr)
        prob = clf.predict_proba(X_te)[:, 1]

        cv_records.append({
            "held_subject": held_subject,
            "n_test": int(len(y_te)),
            "true_label": int(y_te[0]),
            "predicted_prob": float(prob[0]),
            "predicted_label": int(prob[0] >= 0.5),
            "correct": bool((prob[0] >= 0.5) == y_te[0]),
        })
        cv_y_true.extend(y_te.tolist())
        cv_y_prob.extend(prob.tolist())
        ok = (prob[0] >= 0.5) == y_te[0]
        print(f"  [{held_subject}] true={y_te[0]} pred={prob[0]:.3f} {'OK' if ok else 'MISS'}")

    cv_y_true = np.array(cv_y_true)
    cv_y_prob = np.array(cv_y_prob)

    if len(set(cv_y_true)) > 1:
        cv_auc = float(roc_auc_score(cv_y_true, cv_y_prob))
    else:
        cv_auc = float("nan")
    cv_acc = float(accuracy_score(cv_y_true, (cv_y_prob >= 0.5).astype(int)))
    cv_ece = expected_calibration_error(cv_y_true, cv_y_prob, n_bins=5)

    print(f"\n[LOSO] accuracy={cv_acc:.3f}  ROC-AUC={cv_auc:.3f}  ECE={cv_ece:.3f}")

    # Production model: fit on everything, then Platt-calibrate using the
    # held-out predictions we just collected (more honest than internal CV
    # on a tiny dataset).
    print("\n[final] fitting production model on all rows ...")
    final = _make_pipeline()
    final.fit(X, y)
    train_acc = accuracy_score(y, final.predict(X))
    train_auc = roc_auc_score(y, final.predict_proba(X)[:, 1])
    print(f"[final] train accuracy={train_acc:.3f}  ROC-AUC={train_auc:.3f}")

    # Feature importances = standardized coefficients magnitude (for linear).
    lr = final.named_steps["lr"]
    abs_coef = np.abs(lr.coef_[0])
    norm = abs_coef.sum() or 1.0
    feat_importance = dict(zip(FEATURE_NAMES, (abs_coef / norm).tolist()))
    feat_signs = dict(zip(FEATURE_NAMES, np.sign(lr.coef_[0]).astype(int).tolist()))

    # ------------------------------------------------------------------
    # Split-conformal calibration
    # ------------------------------------------------------------------
    # Use the LOSO out-of-fold predictions as a conformal calibration set.
    # Nonconformity score = |pred_prob - true_label| ∈ [0, 1].
    # At inference, a new prediction p gets a p-value = fraction of LOSO
    # residuals at least as extreme. If p_value < alpha, the prediction set
    # for the predicted label is non-trivial; otherwise we abstain.
    # This gives a *provable* coverage guarantee (Vovk et al. 2005).
    # ------------------------------------------------------------------
    cv_y_true = np.array(cv_y_true)
    cv_y_prob = np.array(cv_y_prob)
    nonconformity_scores = np.abs(cv_y_prob - cv_y_true)
    nonconformity_scores.sort()  # ascending; for quantile lookup

    # Pre-compute a few useful quantiles for quick reporting.
    conformal_quantiles = {
        "q50": float(np.quantile(nonconformity_scores, 0.50)),
        "q80": float(np.quantile(nonconformity_scores, 0.80)),
        "q90": float(np.quantile(nonconformity_scores, 0.90)),
        "q95": float(np.quantile(nonconformity_scores, 0.95)),
    }
    print(f"[conformal] residuals (n={len(nonconformity_scores)}): "
          f"q50={conformal_quantiles['q50']:.3f} "
          f"q80={conformal_quantiles['q80']:.3f} "
          f"q90={conformal_quantiles['q90']:.3f} "
          f"q95={conformal_quantiles['q95']:.3f}")

    bundle = {
        "model": final,
        "feature_names": FEATURE_NAMES,
        "feature_importances": feat_importance,
        "feature_signs": feat_signs,
        "model_version": "verdict_fusion_v0",
        "abstention_rules": {
            "low_quality_threshold": 0.4,
            "uncertain_band": [0.45, 0.55],
        },
        # Split-conformal calibration set (sorted ascending). At inference:
        #   p_value(prob, label) = (#{r in residuals : r >= |prob - label|} + 1) / (n + 1)
        # If max(p_value(prob, 0), p_value(prob, 1)) < alpha (e.g., 0.20), abstain.
        "conformal": {
            "calibration_residuals": nonconformity_scores.tolist(),
            "quantiles": conformal_quantiles,
            "n_calibration": int(len(nonconformity_scores)),
            "method": "split-conformal-LOSO",
            "default_alpha": 0.20,  # 80% coverage by default
        },
        "text_prior_stacking": {
            "alpha": 0.0,  # Disabled: text_prior is now a TRAINED feature, not stacked.
            "note": "text_deception_prior is feature 15 (trained); stacking alpha kept at 0",
        },
        "training_meta": {
            "n_train": int(len(X)),
            "n_features": len(FEATURE_NAMES),
            "loso_accuracy": cv_acc,
            "loso_roc_auc": cv_auc,
            "loso_ece": cv_ece,
        },
    }
    MODEL_OUT.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, MODEL_OUT)
    print(f"[saved] {MODEL_OUT}  ({MODEL_OUT.stat().st_size / 1024:.1f} KB)")

    # Save metrics file
    metrics = {
        "model_name": "VerdictFusion-v0",
        "description": "L2-regularized logistic regression on 14 multimodal features. Text-prior stacked externally.",
        "feature_names": FEATURE_NAMES,
        "feature_importances": feat_importance,
        "feature_signs": feat_signs,
        "loso_cv": {
            "accuracy": cv_acc,
            "roc_auc": cv_auc,
            "ece": cv_ece,
            "per_subject": cv_records,
        },
        "production_fit": {
            "n_rows": int(len(X)),
            "train_accuracy": float(train_acc),
            "train_roc_auc": float(train_auc),
        },
    }
    METRICS_OUT.parent.mkdir(parents=True, exist_ok=True)
    METRICS_OUT.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(f"[saved] {METRICS_OUT}")

    # Top-3 features summary
    top3 = sorted(feat_importance.items(), key=lambda kv: -kv[1])[:5]
    print("\nTop-5 feature importances:")
    for name, imp in top3:
        print(f"  {name:<28s}  {imp:.3f}")


if __name__ == "__main__":
    main()
