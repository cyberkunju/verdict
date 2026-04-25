"""Train a quality-gated rPPG-10 heart-rate ensemble.

The model is intentionally hybrid rather than a large neural net. With only
rPPG-10 available locally, a deep model would overfit. This script builds a
strong, reproducible baseline by:

1. extracting mean RGB traces from the three provided ROI videos,
2. deriving ground-truth HR from synchronized ECG,
3. generating classical rPPG candidates (GREEN, POS, CHROM, LGI, PBV, OMIT) per ROI,
4. training a fusion regressor to correct/combine candidates,
5. training an error regressor used as a quality/reject gate.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cv2
import joblib
import numpy as np
from scipy.signal import butter, filtfilt, find_peaks, welch
from scipy.ndimage import median_filter
from sklearn.ensemble import ExtraTreesRegressor, RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


ROOT = Path(os.getenv("M3_REPO_ROOT", Path(__file__).resolve().parents[2]))
M3 = Path(os.getenv("M3_ROOT", ROOT / "M3-data"))
DATA_ROOT = Path(
    os.getenv(
        "M3_RPPG10_DATA_ROOT",
        M3 / "raw" / "public" / "rPPG-10" / "dataset" / "Dataset_rPPG-10",
    )
)
CACHE_DIR = Path(os.getenv("M3_RPPG_CACHE_DIR", M3 / "processed" / "rppg10_traces"))
MODEL_DIR = Path(
    os.getenv("M3_RPPG_MODEL_DIR", M3 / "models" / "m3_rppg10_quality_gated_ensemble_v1")
)
MANIFEST_DIR = Path(os.getenv("M3_MANIFEST_DIR", M3 / "manifests"))

LOW_HZ = 0.7
HIGH_HZ = 3.0
WINDOW_SECONDS = 30.0
HOP_SECONDS = 10.0


@dataclass
class VideoInfo:
    fps: float
    frames: int
    width: int
    height: int
    duration_seconds: float


def bandpass(x: np.ndarray, fs: float, low: float = LOW_HZ, high: float = HIGH_HZ) -> np.ndarray:
    if len(x) < int(fs * 3):
        return x - np.mean(x)
    nyq = fs / 2.0
    lo = max(low / nyq, 1e-4)
    hi = min(high / nyq, 0.999)
    if hi <= lo:
        return x - np.mean(x)
    b, a = butter(3, [lo, hi], btype="band")
    return filtfilt(b, a, x)


def zscore(x: np.ndarray) -> np.ndarray:
    return (x - np.mean(x)) / (np.std(x) + 1e-9)


def video_rgb_trace(path: Path) -> tuple[np.ndarray, VideoInfo]:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        raise RuntimeError(f"cannot open video: {path}")
    fps = float(cap.get(cv2.CAP_PROP_FPS) or 30.0)
    frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH) or 0)
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0)
    means: list[np.ndarray] = []
    while True:
        ok, frame = cap.read()
        if not ok:
            break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        means.append(rgb.reshape(-1, 3).mean(axis=0))
    cap.release()
    trace = np.asarray(means, dtype=np.float64)
    info = VideoInfo(
        fps=fps,
        frames=len(means) if means else frames,
        width=width,
        height=height,
        duration_seconds=(len(means) if means else frames) / max(fps, 1e-9),
    )
    return trace, info


def load_subject(subject_dir: Path) -> dict:
    subject = subject_dir.name
    cache = CACHE_DIR / f"{subject}.npz"
    if cache.exists():
        data = np.load(cache, allow_pickle=True)
        return {
            "subject": subject,
            "fps": float(data["fps"]),
            "traces": {k.replace("trace_", ""): data[k] for k in data.files if k.startswith("trace_")},
            "ecg": data["ecg"],
            "video_info": json.loads(str(data["video_info"].item())),
        }

    roi_files = {
        "forehead": subject_dir / f"{subject}_Forehead_.avi",
        "cheek1": subject_dir / f"{subject}_Cheek1_.avi",
        "cheek2": subject_dir / f"{subject}_Cheek2_.avi",
    }
    traces: dict[str, np.ndarray] = {}
    infos: dict[str, dict] = {}
    for roi, path in roi_files.items():
        trace, info = video_rgb_trace(path)
        traces[roi] = trace
        infos[roi] = asdict(info)
    fps = float(np.median([info["fps"] for info in infos.values()]))
    ecg_path = subject_dir / f"{subject}_ECG.npy"
    ecg = np.load(ecg_path).astype(np.float64).squeeze()

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        cache,
        fps=fps,
        ecg=ecg,
        video_info=json.dumps(infos),
        **{f"trace_{roi}": trace for roi, trace in traces.items()},
    )
    return {"subject": subject, "fps": fps, "traces": traces, "ecg": ecg, "video_info": infos}


def pulse_green(rgb: np.ndarray) -> np.ndarray:
    return zscore(rgb[:, 1])


def pulse_pos(rgb: np.ndarray) -> np.ndarray:
    rgb_t = rgb.T
    norm = rgb_t / (rgb_t.mean(axis=1, keepdims=True) + 1e-9)
    s1 = norm[1] - norm[2]
    s2 = -2.0 * norm[0] + norm[1] + norm[2]
    alpha = (np.std(s1) + 1e-9) / (np.std(s2) + 1e-9)
    return zscore(s1 + alpha * s2)


def pulse_chrom(rgb: np.ndarray) -> np.ndarray:
    norm = rgb / (rgb.mean(axis=0, keepdims=True) + 1e-9)
    r, g, b = norm[:, 0], norm[:, 1], norm[:, 2]
    x = 3.0 * r - 2.0 * g
    y = 1.5 * r + g - 1.5 * b
    alpha = (np.std(x) + 1e-9) / (np.std(y) + 1e-9)
    return zscore(x - alpha * y)


def pulse_lgi(rgb: np.ndarray) -> np.ndarray:
    """LGI-style projection using the ROI mean RGB trace."""
    x = rgb.T.reshape(1, 3, -1)
    u, _, _ = np.linalg.svd(x)
    s = u[:, :, 0]
    s = np.expand_dims(s, 2)
    p = np.tile(np.identity(3), (s.shape[0], 1, 1)) - np.matmul(s, np.swapaxes(s, 1, 2))
    y = np.matmul(p, x)
    return zscore(y[:, 1, :].reshape(-1))


def pulse_pbv(rgb: np.ndarray) -> np.ndarray:
    """PBV-style blood-volume pulse signature projection."""
    x = rgb.T.reshape(1, 3, -1)
    sig_mean = np.mean(x, axis=2)
    rn = x[:, 0, :] / (np.expand_dims(sig_mean[:, 0], axis=1) + 1e-9)
    gn = x[:, 1, :] / (np.expand_dims(sig_mean[:, 1], axis=1) + 1e-9)
    bn = x[:, 2, :] / (np.expand_dims(sig_mean[:, 2], axis=1) + 1e-9)
    pbv_n = np.array([np.std(rn, axis=1), np.std(gn, axis=1), np.std(bn, axis=1)])
    pbv_d = np.sqrt(np.var(rn, axis=1) + np.var(gn, axis=1) + np.var(bn, axis=1)) + 1e-9
    pbv = pbv_n / pbv_d
    c = np.swapaxes(np.array([rn, gn, bn]), 0, 1)
    ct = np.swapaxes(np.swapaxes(np.transpose(c), 0, 2), 1, 2)
    q = np.matmul(c, ct)
    w = np.linalg.solve(q + np.eye(3)[None, :, :] * 1e-6, np.swapaxes(pbv, 0, 1))
    a = np.matmul(ct, np.expand_dims(w, axis=2))
    b = np.matmul(np.swapaxes(np.expand_dims(pbv.T, axis=2), 1, 2), np.expand_dims(w, axis=2))
    return zscore((a / (b + 1e-9)).squeeze(axis=2).reshape(-1))


def pulse_omit(rgb: np.ndarray) -> np.ndarray:
    """OMIT-style orthogonal matrix image transformation on mean RGB trace."""
    x = rgb.T
    q, _ = np.linalg.qr(x)
    s = q[:, 0].reshape(1, -1)
    p = np.identity(3) - np.matmul(s.T, s)
    y = np.dot(p, x)
    return zscore(y[1, :].reshape(-1))


def hr_from_ppg_like(signal: np.ndarray, fs: float) -> tuple[float, float, float]:
    if len(signal) < int(fs * 4):
        return math.nan, -120.0, math.nan
    sig = bandpass(zscore(signal), fs)
    freqs, power = welch(sig, fs=fs, nperseg=min(len(sig), int(fs * 16)))
    mask = (freqs >= LOW_HZ) & (freqs <= HIGH_HZ)
    if not np.any(mask):
        return math.nan, -120.0, math.nan
    band_f = freqs[mask]
    band_p = power[mask]
    idx = int(np.argmax(band_p))
    peak_freq = float(band_f[idx])
    peak_power = float(band_p[idx])
    local = (freqs >= max(LOW_HZ, peak_freq - 0.1)) & (freqs <= min(HIGH_HZ, peak_freq + 0.1))
    noise = float(np.sum(power[mask]) - np.sum(power[local]) + 1e-12)
    snr_db = 10.0 * math.log10((float(np.sum(power[local])) + 1e-12) / noise)
    return peak_freq * 60.0, snr_db, peak_power


def hr_from_ecg(ecg: np.ndarray, fs: float) -> tuple[float, int]:
    sig = bandpass(zscore(ecg), fs, low=0.5, high=35.0)

    def detect(x: np.ndarray) -> np.ndarray:
        peaks, _ = find_peaks(
            x,
            distance=max(1, int(0.3 * fs)),
            prominence=max(0.35, float(np.std(x) * 0.6)),
        )
        return peaks

    candidates = [detect(sig), detect(-sig)]
    best: tuple[float, int, np.ndarray] | None = None
    for peaks in candidates:
        if len(peaks) < 3:
            continue
        rr = np.diff(peaks) / fs
        rr = rr[(rr >= 0.3) & (rr <= 1.8)]
        if len(rr) < 2:
            continue
        hr = 60.0 / float(np.median(rr))
        score = len(rr) if 35 <= hr <= 210 else -len(rr)
        if best is None or score > best[1]:
            best = (hr, score, peaks)
    if best is None:
        return math.nan, 0
    return best[0], len(best[2])


def subject_number(name: str) -> int:
    return int(name.split("_")[-1])


def split_subjects(subjects: list[str]) -> dict[str, list[str]]:
    ordered = sorted(subjects, key=subject_number)
    # Fixed subject-level split: no leakage across train/validation/test.
    return {
        "train": [s for s in ordered if subject_number(s) % 5 not in (0, 1)],
        "validation": [s for s in ordered if subject_number(s) % 5 == 0],
        "test": [s for s in ordered if subject_number(s) % 5 == 1],
    }


def build_examples() -> tuple[list[dict], dict]:
    subjects = sorted([p for p in DATA_ROOT.glob("Subject_*") if p.is_dir()], key=lambda p: subject_number(p.name))
    rows: list[dict] = []
    inventory: dict = {"subjects": [], "skipped_subjects": []}
    hr_feature_keys: set[str] = set()
    for subject_dir in subjects:
        try:
            item = load_subject(subject_dir)
        except Exception as exc:
            inventory["skipped_subjects"].append({"subject": subject_dir.name, "reason": str(exc)})
            continue
        subject = item["subject"]
        fps = float(item["fps"])
        traces: dict[str, np.ndarray] = item["traces"]
        ecg = item["ecg"]
        duration = min([len(t) / fps for t in traces.values()])
        ecg_fs = len(ecg) / duration
        inventory["subjects"].append(
            {
                "subject": subject,
                "fps": fps,
                "duration_seconds": duration,
                "ecg_samples": int(len(ecg)),
                "ecg_fs": ecg_fs,
                "video_info": item["video_info"],
            }
        )
        start = 0.0
        subject_rows: list[dict] = []
        while start + WINDOW_SECONDS <= duration + 1e-6:
            end = start + WINDOW_SECONDS
            v0, v1 = int(round(start * fps)), int(round(end * fps))
            e0, e1 = int(round(start * ecg_fs)), int(round(end * ecg_fs))
            y_hr, n_ecg_peaks = hr_from_ecg(ecg[e0:e1], ecg_fs)
            if not np.isfinite(y_hr) or y_hr < 35 or y_hr > 210:
                start += HOP_SECONDS
                continue

            features: dict[str, float | str] = {"subject": subject, "t0": start, "t1": end, "label_hr": y_hr}
            candidate_hrs: list[float] = []
            candidate_snrs: list[float] = []
            for roi, trace in traces.items():
                rgb = trace[v0:v1]
                for method, fn in (
                    ("green", pulse_green),
                    ("pos", pulse_pos),
                    ("chrom", pulse_chrom),
                    ("lgi", pulse_lgi),
                    ("pbv", pulse_pbv),
                    ("omit", pulse_omit),
                ):
                    try:
                        pulse = fn(rgb)
                        pred_hr, snr, peak = hr_from_ppg_like(pulse, fps)
                    except Exception:
                        pred_hr, snr, peak = math.nan, -120.0, math.nan
                    key = f"{roi}_{method}"
                    features[f"{key}_hr"] = pred_hr
                    features[f"{key}_snr"] = snr
                    features[f"{key}_peak"] = peak
                    hr_feature_keys.add(f"{key}_hr")
                    if np.isfinite(pred_hr):
                        candidate_hrs.append(pred_hr)
                        candidate_snrs.append(snr)
                features[f"{roi}_rgb_std"] = float(np.mean(np.std(rgb, axis=0)))
                features[f"{roi}_rgb_mean"] = float(np.mean(rgb))

            if candidate_hrs:
                weights = np.exp(np.clip(np.asarray(candidate_snrs, dtype=np.float64), -8, 8))
                weights = weights / (weights.sum() + 1e-12)
                features["candidate_weighted_hr"] = float(np.sum(weights * np.asarray(candidate_hrs)))
                features["candidate_median_hr"] = float(np.median(candidate_hrs))
                features["candidate_spread_hr"] = float(np.nanpercentile(candidate_hrs, 90) - np.nanpercentile(candidate_hrs, 10))
                features["candidate_best_snr"] = float(np.nanmax(candidate_snrs))
                features["candidate_mean_snr"] = float(np.nanmean(candidate_snrs))
            else:
                features["candidate_weighted_hr"] = math.nan
                features["candidate_median_hr"] = math.nan
                features["candidate_spread_hr"] = math.nan
                features["candidate_best_snr"] = -120.0
                features["candidate_mean_snr"] = -120.0
            features["n_ecg_peaks"] = n_ecg_peaks
            subject_rows.append(features)
            start += HOP_SECONDS
        add_temporal_features(subject_rows, sorted(hr_feature_keys))
        rows.extend(subject_rows)
    return rows, inventory


def add_temporal_features(subject_rows: list[dict], hr_keys: list[str]) -> None:
    """Add physiologically useful temporal continuity features in-place."""
    if not subject_rows:
        return
    subject_rows.sort(key=lambda r: float(r["t0"]))
    smooth_keys: list[str] = []
    for key in hr_keys:
        vals = np.asarray([float(r.get(key, math.nan)) for r in subject_rows], dtype=np.float64)
        finite = np.isfinite(vals)
        if not finite.any():
            continue
        fill = vals.copy()
        fill[~finite] = np.nanmedian(vals[finite])
        # A five-window median spans roughly 70 seconds with 30s windows / 10s hop.
        smooth = median_filter(fill, size=min(5, len(fill)), mode="nearest")
        smooth_key = f"{key}_smooth"
        smooth_keys.append(smooth_key)
        for row, val, raw in zip(subject_rows, smooth, vals):
            row[smooth_key] = float(val)
            row[f"{key}_jump_from_smooth"] = float(abs(raw - val)) if np.isfinite(raw) else 999.0

    for row in subject_rows:
        vals, snrs = [], []
        for key in smooth_keys:
            val = float(row.get(key, math.nan))
            snr = float(row.get(key.replace("_hr_smooth", "_snr"), -120.0))
            if np.isfinite(val):
                vals.append(val)
                snrs.append(snr)
        if vals:
            weights = np.exp(np.clip(np.asarray(snrs, dtype=np.float64), -8, 8))
            weights = weights / (weights.sum() + 1e-12)
            row["candidate_smooth_weighted_hr"] = float(np.sum(weights * np.asarray(vals)))
            row["candidate_smooth_median_hr"] = float(np.median(vals))
            row["candidate_smooth_spread_hr"] = float(np.percentile(vals, 90) - np.percentile(vals, 10))
        else:
            row["candidate_smooth_weighted_hr"] = math.nan
            row["candidate_smooth_median_hr"] = math.nan
            row["candidate_smooth_spread_hr"] = math.nan


def numeric_feature_names(rows: list[dict]) -> list[str]:
    ignore = {"subject", "t0", "t1", "label_hr"}
    names = sorted(k for k in rows[0] if k not in ignore)
    return names


def matrix(rows: list[dict], names: list[str]) -> tuple[np.ndarray, np.ndarray]:
    X = np.asarray([[float(r.get(n, math.nan)) for n in names] for r in rows], dtype=np.float64)
    y = np.asarray([float(r["label_hr"]) for r in rows], dtype=np.float64)
    col_medians = np.nanmedian(np.where(np.isfinite(X), X, np.nan), axis=0)
    col_medians = np.where(np.isfinite(col_medians), col_medians, 0.0)
    inds = ~np.isfinite(X)
    X[inds] = np.take(col_medians, np.where(inds)[1])
    return X, y


def metrics(y: np.ndarray, pred: np.ndarray) -> dict:
    err = np.abs(y - pred)
    return {
        "rows": int(len(y)),
        "mae_bpm": float(mean_absolute_error(y, pred)),
        "rmse_bpm": float(math.sqrt(mean_squared_error(y, pred))),
        "r2": float(r2_score(y, pred)) if len(y) > 1 else math.nan,
        "within_3_bpm": float(np.mean(err <= 3.0)),
        "within_5_bpm": float(np.mean(err <= 5.0)),
        "within_10_bpm": float(np.mean(err <= 10.0)),
        "median_abs_error_bpm": float(np.median(err)),
        "p90_abs_error_bpm": float(np.percentile(err, 90)),
    }


def accepted_metrics(y: np.ndarray, pred: np.ndarray, expected_err: np.ndarray, threshold: float) -> dict:
    mask = expected_err <= threshold
    out = {"threshold": float(threshold), "coverage": float(np.mean(mask)), "accepted_rows": int(mask.sum())}
    if mask.sum() >= 2:
        out.update(metrics(y[mask], pred[mask]))
    return out


def choose_quality_threshold(y_val: np.ndarray, pred_val: np.ndarray, expected_val: np.ndarray) -> float:
    candidates = np.percentile(expected_val, [30, 40, 50, 60, 70, 80, 90, 100])
    best = float(np.max(expected_val))
    best_score = (999.0, -1.0)
    for th in candidates:
        m = accepted_metrics(y_val, pred_val, expected_val, float(th))
        if m["accepted_rows"] < 20:
            continue
        mae = float(m.get("mae_bpm", 999.0))
        coverage = float(m["coverage"])
        score = (mae, -coverage)
        if score < best_score:
            best_score = score
            best = float(th)
    return best


def main() -> None:
    if not DATA_ROOT.exists():
        raise SystemExit(f"missing rPPG-10 dataset: {DATA_ROOT}")
    rows, inventory = build_examples()
    subjects = sorted({str(r["subject"]) for r in rows}, key=subject_number)
    splits = split_subjects(subjects)
    for split, names in splits.items():
        for name in names:
            if name not in subjects:
                raise RuntimeError(f"split subject missing: {name}")

    feature_names = numeric_feature_names(rows)
    split_rows = {k: [r for r in rows if r["subject"] in v] for k, v in splits.items()}
    X_train, y_train = matrix(split_rows["train"], feature_names)
    X_val, y_val = matrix(split_rows["validation"], feature_names)
    X_test, y_test = matrix(split_rows["test"], feature_names)
    X_all, y_all = matrix(rows, feature_names)

    fusion = ExtraTreesRegressor(
        n_estimators=500,
        random_state=42,
        min_samples_leaf=3,
        max_features=0.7,
        n_jobs=-1,
    )
    fusion.fit(X_train, y_train)

    train_pred = fusion.predict(X_train)
    val_pred = fusion.predict(X_val)
    test_pred = fusion.predict(X_test)

    err_model = RandomForestRegressor(
        n_estimators=400,
        random_state=43,
        min_samples_leaf=4,
        max_features=0.8,
        n_jobs=-1,
    )
    err_model.fit(X_train, np.abs(y_train - train_pred))
    train_expected = err_model.predict(X_train)
    val_expected = err_model.predict(X_val)
    test_expected = err_model.predict(X_test)
    q_threshold = choose_quality_threshold(y_val, val_pred, val_expected)

    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "model_name": "m3_rppg10_quality_gated_ensemble_v1",
        "data_root": str(DATA_ROOT),
        "method": "GREEN/POS/CHROM/LGI/PBV/OMIT per ROI + ExtraTrees HR fusion + RandomForest expected-error quality gate",
        "window_seconds": WINDOW_SECONDS,
        "hop_seconds": HOP_SECONDS,
        "subjects": subjects,
        "splits": splits,
        "row_counts": {k: len(v) for k, v in split_rows.items()},
        "feature_count": len(feature_names),
        "quality_threshold_expected_abs_error_bpm": q_threshold,
        "metrics": {
            "train": metrics(y_train, train_pred),
            "validation": metrics(y_val, val_pred),
            "test": metrics(y_test, test_pred),
            "validation_accepted": accepted_metrics(y_val, val_pred, val_expected, q_threshold),
            "test_accepted": accepted_metrics(y_test, test_pred, test_expected, q_threshold),
        },
        "baselines": {
            "test_candidate_weighted": metrics(
                y_test,
                np.asarray([float(r["candidate_weighted_hr"]) for r in split_rows["test"]], dtype=np.float64),
            ),
            "test_candidate_median": metrics(
                y_test,
                np.asarray([float(r["candidate_median_hr"]) for r in split_rows["test"]], dtype=np.float64),
            ),
        },
        "inventory": inventory,
    }

    fusion_all = ExtraTreesRegressor(
        n_estimators=700,
        random_state=52,
        min_samples_leaf=3,
        max_features=0.7,
        n_jobs=-1,
    )
    fusion_all.fit(X_all, y_all)
    all_pred = fusion_all.predict(X_all)
    err_all = RandomForestRegressor(
        n_estimators=500,
        random_state=53,
        min_samples_leaf=4,
        max_features=0.8,
        n_jobs=-1,
    )
    err_all.fit(X_all, np.abs(y_all - all_pred))
    report["deployment_model"] = {
        "trained_on": "all usable rPPG-10 windows",
        "rows": int(len(y_all)),
        "subjects": int(len(subjects)),
        "training_metrics_not_holdout": metrics(y_all, all_pred),
    }

    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(
        {
            "fusion_model": fusion,
            "error_model": err_model,
            "feature_names": feature_names,
            "quality_threshold_expected_abs_error_bpm": q_threshold,
            "config": {
                "low_hz": LOW_HZ,
                "high_hz": HIGH_HZ,
                "window_seconds": WINDOW_SECONDS,
                "hop_seconds": HOP_SECONDS,
            },
        },
        MODEL_DIR / "model.joblib",
    )
    joblib.dump(
        {
            "fusion_model": fusion_all,
            "error_model": err_all,
            "feature_names": feature_names,
            "quality_threshold_expected_abs_error_bpm": q_threshold,
            "config": {
                "low_hz": LOW_HZ,
                "high_hz": HIGH_HZ,
                "window_seconds": WINDOW_SECONDS,
                "hop_seconds": HOP_SECONDS,
            },
            "note": "Deployment artifact trained on all usable rPPG-10 windows. Use metrics.json for subject-held-out evaluation.",
        },
        MODEL_DIR / "deployment_all_data_model.joblib",
    )
    (MODEL_DIR / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (MANIFEST_DIR / "m3_rppg10_quality_gated_ensemble_v1_metrics.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    print(json.dumps({k: report[k] for k in ["model_name", "row_counts", "metrics"]}, indent=2))


if __name__ == "__main__":
    main()
