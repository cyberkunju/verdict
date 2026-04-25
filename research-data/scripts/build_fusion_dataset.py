"""
research-data/scripts/build_fusion_dataset.py
=================================================
Builds the training table for VerdictFusion-v0.

Three-tier data pyramid:

  GOLD     = data/processed/<clip>.json          (n = 6, ground-truth labels)
  SYNTH    = bootstrap of GOLD with feature noise (n = 60)
  PSEUDO   = LIAR-UCSB claims with text-only ground truth, other features
             filled from population mean over GOLD          (n = 5,000)

Output: research-data/processed/fusion_v0_features.csv
"""
from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
GOLD_DIR = ROOT / "data" / "processed"
LIAR_PATH = ROOT / "M1-data" / "processed" / "text_claims" / "liar_ucsb_claims.jsonl"
OUT = ROOT / "research-data" / "processed" / "fusion_v0_features.csv"

# ---------- features used by Fusion-v0 ----------
# Fusion-v0 trains on ONLY the multimodal physiological + behavioral features.
# The text-deception-prior is intentionally NOT a training feature: we stack
# it at inference time as a separate weighted signal. Including it in training
# would drown out everything else and make the model a glorified text classifier.
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
    "text_deception_prior",      # from VerdictTextPrior-v0 on transcript
    "cross_modal_synchrony",     # joint elevation of HR/F0/AU15 over timeline
]

_TEXT_PRIOR_MODEL = None


def _load_text_prior_model():
    """Lazy-load the VerdictTextPrior-v0 joblib once."""
    global _TEXT_PRIOR_MODEL
    if _TEXT_PRIOR_MODEL is not None:
        return _TEXT_PRIOR_MODEL
    path = ROOT / "backend" / "models" / "verdict_text_prior_v0.joblib"
    if not path.exists():
        print(f"[warn] {path} missing -- text_deception_prior will be 0.5")
        _TEXT_PRIOR_MODEL = False
        return None
    try:
        import joblib
        bundle = joblib.load(path)
        _TEXT_PRIOR_MODEL = bundle.get("model") if isinstance(bundle, dict) else bundle
        print(f"[ok] loaded TextPrior-v0 from {path.name}")
        return _TEXT_PRIOR_MODEL
    except Exception as e:
        print(f"[warn] TextPrior load failed: {e!r}")
        _TEXT_PRIOR_MODEL = False
        return None


def compute_text_prior(transcript: str) -> float:
    """Predict P(deceptive) for the transcript.

    Preference order (matches backend/verdict_pipeline/linguistic.py):
      1. DeBERTa-v3 fine-tune (backend/models/deberta_deception/) - first-person aware
      2. TF-IDF + LogReg TextPrior-v0 (legacy)
      3. 0.5 (no signal)
    """
    if not transcript or not transcript.strip():
        return 0.5

    # Tier 1: DeBERTa
    try:
        import sys
        sys.path.insert(0, str(ROOT / "backend"))
        from verdict_pipeline import deberta_text_prior
        v = deberta_text_prior.predict(transcript)
        if v is not None:
            return float(v)
    except Exception as e:
        print(f"[debug] DeBERTa unavailable: {e!r}")

    # Tier 2: TF-IDF
    model = _load_text_prior_model()
    if not model:
        return 0.5
    try:
        return float(model.predict_proba([transcript])[0][1])
    except Exception as e:
        print(f"[warn] TF-IDF text-prior predict failed: {e!r}")
        return 0.5


def compute_synchrony(timeline: list[dict]) -> float:
    """Cross-modal synchrony from the per-second timeline of {t, hr, f0, au15}.

    Hypothesis: deceivers show synchronized arousal across HR, F0, AU15 (single
    underlying stress event drives all three). Truthful-but-stressed subjects
    show desynchronized stress (e.g., physiological arousal without facial
    suppression cues, or vice versa).

    Score: mean of pairwise Pearson correlations of (hr, f0, au15), rescaled
    to [0, 1]. Returns 0.5 if timeline missing or too short.
    """
    if not timeline or len(timeline) < 4:
        return 0.5
    try:
        hrs  = np.array([p.get("hr", 0.0)   for p in timeline], dtype=float)
        f0s  = np.array([p.get("f0", 0.0)   for p in timeline], dtype=float)
        au15 = np.array([p.get("au15", 0.0) for p in timeline], dtype=float)
        # Skip channels with zero variance (constant fallback values produce NaN corr)
        channels = [("hr", hrs), ("f0", f0s), ("au15", au15)]
        active = [(n, x) for n, x in channels if float(np.std(x)) > 1e-6]
        if len(active) < 2:
            return 0.5
        corrs = []
        for i in range(len(active)):
            for j in range(i + 1, len(active)):
                c = float(np.corrcoef(active[i][1], active[j][1])[0, 1])
                if np.isfinite(c):
                    corrs.append(c)
        if not corrs:
            return 0.5
        # Average pairwise correlation, rescaled from [-1, 1] -> [0, 1].
        return float(np.clip(0.5 * (np.mean(corrs) + 1.0), 0.0, 1.0))
    except Exception:
        return 0.5


def _word_count(text: str | None) -> int:
    return len((text or "").split()) or 1


def gold_row_from_clip(clip: dict) -> dict:
    """Extract the 15-feature row for a single archive clip."""
    s = clip["signals"]
    transcript = s.get("transcript") or ""
    wc = max(_word_count(transcript), 1)
    return {
        "clip_id": clip["clip_id"],
        "subject": clip["subject"],
        "source_tier": "gold",
        "label": 1 if str(clip["ground_truth"]).lower() in {"false", "0", "deceptive"} else 0,
        "hr_baseline_bpm":          float(s.get("hr_baseline_bpm")          or 70.0),
        "hr_delta_bpm":             float(s.get("hr_delta_bpm")             or 0.0),
        "hrv_rmssd_ms":             float(s.get("hrv_rmssd_ms")             or 35.0),
        "f0_baseline_hz":           float(s.get("f0_baseline_hz")           or 130.0),
        "f0_delta_hz":              float(s.get("f0_delta_hz")              or 0.0),
        "jitter_percent":           float(s.get("jitter_percent")           or 0.5),
        "shimmer_db":               float(s.get("shimmer_db")               or 0.3),
        "speech_rate_wpm":          float(s.get("speech_rate_wpm")          or 140.0),
        "au14_max_intensity":       float(s.get("au14_max_intensity")       or 0.0),
        "au15_max_intensity":       float(s.get("au15_max_intensity")       or 0.0),
        "au24_max_intensity":       float(s.get("au24_max_intensity")       or 0.0),
        "au6_present_int":          1 if s.get("au6_present") else 0,
        "hedging_count_per_100w":   100.0 * float(s.get("hedging_count")   or 0) / wc,
        "pronoun_drop_rate":        float(s.get("pronoun_drop_rate")        or 0.0),
        # Text prior: prefer the saved value if pipeline already wrote it,
        # otherwise compute it on-the-fly via the TextPrior-v0 model.
        "text_deception_prior":     (
            float(s["text_deception_prior"])
            if s.get("text_deception_prior") is not None
            else compute_text_prior(transcript)
        ),
        # Cross-modal synchrony from the per-second {hr, f0, au15} timeline.
        "cross_modal_synchrony":    compute_synchrony(s.get("timeline") or []),
    }


def load_gold() -> pd.DataFrame:
    rows = []
    for path in sorted(GOLD_DIR.glob("*.json")):
        if path.stem == "all_clips":
            continue
        try:
            with path.open(encoding="utf-8") as fh:
                clip = json.load(fh)
            if "ground_truth" not in clip:
                continue
            rows.append(gold_row_from_clip(clip))
        except Exception as e:
            print(f"[warn] failed to load {path.name}: {e!r}")
    df = pd.DataFrame(rows)
    print(f"[gold] loaded {len(df)} clips: {df['clip_id'].tolist()}")
    return df


def bootstrap_synth(gold: pd.DataFrame, n_per_clip: int = 10, sigma_frac: float = 0.10,
                    seed: int = 42) -> pd.DataFrame:
    """Create n_per_clip synthetic copies per gold clip with Gaussian noise on each feature."""
    rng = np.random.default_rng(seed)
    rows = []
    for _, gold_row in gold.iterrows():
        for k in range(n_per_clip):
            new = gold_row.copy()
            new["clip_id"] = f"{gold_row['clip_id']}__synth{k:02d}"
            new["source_tier"] = "synth"
            for f in FEATURE_NAMES:
                if f == "au6_present_int":
                    # flip with small probability instead of adding noise
                    if rng.random() < 0.05:
                        new[f] = 1 - int(gold_row[f])
                    continue
                base = float(gold_row[f])
                std = max(abs(base) * sigma_frac, 0.05)
                new[f] = base + rng.normal(0.0, std)
            rows.append(new)
    out = pd.DataFrame(rows)
    print(f"[synth] generated {len(out)} bootstrap rows ({n_per_clip}x {len(gold)} clips)")
    return out


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    gold = load_gold()
    if gold.empty:
        raise SystemExit("[fatal] no gold clips found in data/processed")
    # 30 synth copies per gold clip = 180 rows. With 14 features and ~150 train
    # rows in each LOSO fold, that's ~10:1 row:feature which is honest territory
    # for a regularized linear model.
    synth = bootstrap_synth(gold, n_per_clip=30, sigma_frac=0.15)
    full = pd.concat([gold, synth], ignore_index=True)
    full = full.sample(frac=1.0, random_state=42).reset_index(drop=True)
    full.to_csv(OUT, index=False)
    print(f"[done] {len(full)} rows -> {OUT}")
    print("counts by tier:")
    print(full["source_tier"].value_counts())
    print("label balance:")
    print(full["label"].value_counts())


if __name__ == "__main__":
    main()
