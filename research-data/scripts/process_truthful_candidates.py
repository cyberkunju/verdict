"""
research-data/scripts/process_truthful_candidates.py
======================================================
Downloads + runs the full pipeline on the 6 newly-added truthful clips
defined in backend/verdict_pipeline/clips.py:

    dean_1973, cheung_2019, shultz_2019, wigand_1996, snowden_2013, ellsberg_1971

For each clip:
  1. python -m scripts.download_clip <clip_id>          (yt-dlp + ffmpeg trim)
  2. python -m verdict_pipeline.batch --clip-id <clip_id>  (full extractor pipeline)
  3. Verify data/processed/<clip_id>.json exists and has signals.

If a clip fails (404, geo-blocked, broken extractor), it is logged and skipped.
The script exits 0 if at least 4/6 succeed (enough to balance Fusion-v0 training).

  python research-data/scripts/process_truthful_candidates.py [--only clip_id]

Run from repo root with the backend on PYTHONPATH:
    set PYTHONPATH=backend
    python research-data/scripts/process_truthful_candidates.py
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
PROCESSED_DIR = ROOT / "data" / "processed"
LOG_PATH = ROOT / "research-data" / "manifests" / "truthful_processing_log.jsonl"

CANDIDATES = [
    "dean_1973",
    "cheung_2019",
    "shultz_2019",
    "wigand_1996",
    "snowden_2013",
    "ellsberg_1971",
]


def log(rec: dict) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    rec["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    tag = rec.get("event", "?").upper()
    detail = rec.get("detail", "")
    print(f"[{tag}] {rec.get('clip_id', '-')} :: {detail}")


def run_step(clip_id: str, cmd: list[str], step_name: str, *, timeout: int) -> bool:
    log({"event": f"{step_name}_start", "clip_id": clip_id, "detail": " ".join(cmd)})
    env = {**os.environ, "PYTHONPATH": str(BACKEND), "PYTHONIOENCODING": "utf-8"}
    try:
        proc = subprocess.run(
            cmd, cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired:
        log({"event": f"{step_name}_timeout", "clip_id": clip_id,
             "detail": f"after {timeout}s"})
        return False
    ok = proc.returncode == 0
    if not ok:
        tail_stderr = (proc.stderr or "").splitlines()[-15:]
        log({"event": f"{step_name}_failed", "clip_id": clip_id,
             "detail": f"rc={proc.returncode} | " + " | ".join(tail_stderr)})
    else:
        log({"event": f"{step_name}_ok", "clip_id": clip_id, "detail": ""})
    return ok


def process_one(clip_id: str) -> bool:
    """Download + run pipeline. Returns True on full success."""
    py = sys.executable

    # Step 1: download + trim. Generous 5-min timeout for slow networks.
    if not run_step(
        clip_id,
        [py, "-m", "scripts.download_clip", clip_id],
        step_name="download",
        timeout=300,
    ):
        return False

    # Step 2: run the full pipeline. 3-min timeout per clip is plenty for our
    # short windows (rPPG + facial + voice are the slowest steps).
    if not run_step(
        clip_id,
        [py, "-m", "verdict_pipeline.batch", "--only", clip_id],
        step_name="pipeline",
        timeout=180,
    ):
        return False

    # Step 3: verify output JSON
    out_path = PROCESSED_DIR / f"{clip_id}.json"
    if not out_path.exists():
        log({"event": "missing_output", "clip_id": clip_id, "detail": str(out_path)})
        return False

    try:
        clip = json.loads(out_path.read_text(encoding="utf-8"))
        sig_count = sum(1 for k in (
            "hr_baseline_bpm", "f0_baseline_hz", "au15_max_intensity"
        ) if clip.get("signals", {}).get(k) is not None)
        log({"event": "verified", "clip_id": clip_id,
             "detail": f"{sig_count}/3 critical features present, "
                       f"deception={clip.get('scores', {}).get('deception')}"})
    except Exception as e:
        log({"event": "verify_failed", "clip_id": clip_id, "detail": repr(e)[:200]})
        return False

    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", help="Run only this clip_id")
    ap.add_argument("--force", action="store_true",
                    help="Re-process even if data/processed/<id>.json already exists")
    args = ap.parse_args()

    targets = [args.only] if args.only else CANDIDATES
    results: dict[str, bool] = {}

    log({"event": "run_start", "clip_id": "-",
         "detail": f"processing {len(targets)} clips: {targets}"})

    for i, clip_id in enumerate(targets, start=1):
        out_path = PROCESSED_DIR / f"{clip_id}.json"
        if out_path.exists() and not args.force:
            log({"event": "clip_skip", "clip_id": clip_id,
                 "detail": f"({i}/{len(targets)}) already processed -- pass --force to redo"})
            results[clip_id] = True
            continue
        log({"event": "clip_start", "clip_id": clip_id,
             "detail": f"({i}/{len(targets)}) starting download+pipeline"})
        try:
            results[clip_id] = process_one(clip_id)
        except Exception as e:
            log({"event": "clip_exception", "clip_id": clip_id, "detail": repr(e)[:200]})
            results[clip_id] = False
        n_done = sum(1 for v in results.values())
        n_ok = sum(1 for v in results.values() if v)
        log({"event": "clip_done", "clip_id": clip_id,
             "detail": f"progress {n_done}/{len(targets)} ({n_ok} OK)"})

    n_ok = sum(results.values())
    n_total = len(results)
    log({"event": "run_end", "clip_id": "-",
         "detail": f"{n_ok}/{n_total} succeeded: " +
                   ", ".join(f"{k}={'OK' if v else 'FAIL'}" for k, v in results.items())})

    print("\n" + "=" * 60)
    print(f"SUMMARY: {n_ok}/{n_total} clips processed successfully")
    print("=" * 60)
    for cid, ok in results.items():
        print(f"  {cid:<18s} {'OK' if ok else 'FAIL'}")

    if n_ok < 4 and not args.only:
        print("\n[warn] fewer than 4 truthful clips ready -- Fusion-v0 may still")
        print("       lack class balance. Inspect the log and retry failed clips:")
        print(f"       {LOG_PATH}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
