"""VerdictFusion-v0 inference adapter.

Loads the trained sklearn pipeline from ``backend/models/verdict_fusion_v0.joblib``
once at import time and exposes a single ``predict(features)`` function that
returns a calibrated deception probability in [0, 1].

If the joblib is missing or fails to load, ``predict`` returns ``None`` and
``score.compute_scores`` transparently falls back to the hand-coded formula.
This keeps the pipeline runnable on machines without the model.

The text-prior is intentionally NOT a training feature; it is stacked at
inference via ``predict(features, text_prior=...)`` using the alpha stored
inside the joblib bundle.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np

from .utils import get_logger

log = get_logger("fusion")

_MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "verdict_fusion_v0.joblib"

_BUNDLE: dict[str, Any] | None = None
_LOAD_ERROR: str | None = None


def _try_load() -> dict[str, Any] | None:
    global _BUNDLE, _LOAD_ERROR
    if _BUNDLE is not None or _LOAD_ERROR is not None:
        return _BUNDLE
    if not _MODEL_PATH.exists():
        _LOAD_ERROR = f"missing: {_MODEL_PATH}"
        log.info("[fusion] no trained model at %s -- falling back to hand-coded formula", _MODEL_PATH)
        return None
    try:
        import joblib
        bundle = joblib.load(_MODEL_PATH)
        _BUNDLE = bundle
        meta = bundle.get("training_meta", {})
        log.info("[fusion] loaded %s | LOSO acc=%.3f auc=%.3f n=%d",
                 bundle.get("model_version", "?"),
                 meta.get("loso_accuracy", float("nan")),
                 meta.get("loso_roc_auc", float("nan")),
                 meta.get("n_train", 0))
        return bundle
    except Exception as e:
        _LOAD_ERROR = repr(e)
        log.warning("[fusion] failed to load %s: %s", _MODEL_PATH, e)
        return None


def is_available() -> bool:
    return _try_load() is not None


def feature_names() -> list[str]:
    bundle = _try_load()
    return list(bundle["feature_names"]) if bundle else []


def predict(features: dict[str, float], text_prior: float | None = None) -> float | None:
    """Return calibrated deception probability in [0, 1] or None if model unavailable.

    Backwards-compatible wrapper around ``predict_full``. Returns just the prob.
    """
    full = predict_full(features, text_prior=text_prior)
    return None if full is None else full["prob"]


def predict_full(
    features: dict[str, float],
    text_prior: float | None = None,
    alpha: float = 0.20,
) -> dict | None:
    """Return calibrated deception probability + conformal p-values + abstention.

    Output keys:
        prob              — sigmoid output of trained logistic regression in [0, 1]
        predicted_label   — argmax (0=truthful, 1=deceptive)
        p_value_deceptive — split-conformal p-value for the prob being deceptive
        p_value_truthful  — split-conformal p-value for the prob being truthful
        abstain           — True if neither p-value crosses ``alpha``
        confidence        — max p-value (informational)
        coverage_alpha    — the alpha used (so caller knows the abstention rule)

    Returns ``None`` if the model is not available.
    """
    bundle = _try_load()
    if bundle is None:
        return None

    names = bundle["feature_names"]
    row = np.array([float(features.get(n, 0.0)) for n in names], dtype=float).reshape(1, -1)
    missing = [n for n in names if n not in features]
    if missing:
        log.debug("[fusion] missing features filled with 0: %s", missing[:5])

    try:
        prob = float(bundle["model"].predict_proba(row)[0, 1])
    except Exception as e:
        log.warning("[fusion] predict failed: %s -- falling back", e)
        return None

    # Optional text-prior stacking (typically alpha=0 in v0+; kept for compat)
    if text_prior is not None:
        stack_alpha = float(bundle.get("text_prior_stacking", {}).get("alpha", 0.0))
        if 0.0 < stack_alpha <= 1.0:
            prob = (1.0 - stack_alpha) * prob + stack_alpha * float(np.clip(text_prior, 0.0, 1.0))
    prob = float(np.clip(prob, 0.0, 1.0))

    # Split-conformal p-values: how surprising is this prediction under the
    # LOSO calibration distribution if the true label were 0 vs 1?
    conformal = bundle.get("conformal") or {}
    cal_residuals = np.array(conformal.get("calibration_residuals", []), dtype=float)
    n_cal = len(cal_residuals)

    def _p_value(label: int) -> float | None:
        if n_cal == 0:
            return None
        # Nonconformity score for hypothesizing this label.
        score = abs(prob - float(label))
        # Standard inductive-conformal p-value (Vovk et al.):
        #   p = (#{r >= score} + 1) / (n + 1)
        n_ge = int(np.sum(cal_residuals >= score))
        return float((n_ge + 1) / (n_cal + 1))

    p_dec = _p_value(1)
    p_tru = _p_value(0)

    # Abstain when neither label is plausible at the requested coverage level.
    # (Both p-values fall below alpha = both labels rejected as too surprising.)
    if p_dec is not None and p_tru is not None:
        abstain = (p_dec < alpha) and (p_tru < alpha)
        confidence = float(max(p_dec, p_tru))
    else:
        abstain = False
        confidence = None

    return {
        "prob": prob,
        "predicted_label": int(prob >= 0.5),
        "p_value_deceptive": p_dec,
        "p_value_truthful": p_tru,
        "abstain": abstain,
        "confidence": confidence,
        "coverage_alpha": alpha,
        "n_calibration": n_cal,
    }


def metadata() -> dict[str, Any]:
    """Return a small dict for inclusion in clip JSONs / API responses."""
    bundle = _try_load()
    if bundle is None:
        return {"available": False, "reason": _LOAD_ERROR or "not loaded"}
    meta = bundle.get("training_meta", {})
    return {
        "available": True,
        "version": bundle.get("model_version", "verdict_fusion_v0"),
        "loso_accuracy": meta.get("loso_accuracy"),
        "loso_roc_auc": meta.get("loso_roc_auc"),
        "loso_ece": meta.get("loso_ece"),
        "n_train": meta.get("n_train"),
        "top_features": sorted(
            bundle.get("feature_importances", {}).items(), key=lambda kv: -kv[1],
        )[:5],
    }
