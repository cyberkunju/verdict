"""Train M3 rPPG-10 model on Modal and persist artifacts to Modal Volume.

Run from repository root:

    modal run M3-data/scripts/train_rppg10_modal.py

The app scales to zero after the local entrypoint completes. Artifacts are saved
under ``verdict-m3-models:/runs/<run_name>/``.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import modal


APP_NAME = "verdict-m3-rppg-training"
DATA_VOLUME_NAME = "verdict-m3-data"
MODEL_VOLUME_NAME = "verdict-m3-models"
DATA_MOUNT = Path("/mnt/verdict-m3-data")
MODEL_MOUNT = Path("/mnt/verdict-m3-models")

app = modal.App(APP_NAME)
data_volume = modal.Volume.from_name(DATA_VOLUME_NAME)
model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME, create_if_missing=True)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install("ffmpeg", "libgl1", "libglib2.0-0")
    .pip_install(
        "joblib>=1.4,<2",
        "numpy>=1.26,<3",
        "opencv-python-headless>=4.10,<5",
        "openpyxl>=3.1,<4",
        "scikit-learn>=1.5,<2",
        "scipy>=1.13,<2",
        "torch>=2.5,<3",
    )
    .add_local_file(
        "M3-data/scripts/train_rppg10_ensemble.py",
        remote_path="/root/m3_scripts/train_rppg10_ensemble.py",
    )
)


def _run_name() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"m3-rppg10-quality-gated-ensemble-v1-{stamp}"


@app.function(
    image=image,
    gpu="T4",
    timeout=60 * 60 * 3,
    volumes={str(DATA_MOUNT): data_volume, str(MODEL_MOUNT): model_volume},
    min_containers=0,
    max_containers=1,
    scaledown_window=2,
)
def train_remote(run_name: str) -> dict:
    run_dir = MODEL_MOUNT / "runs" / run_name
    model_dir = run_dir / "model"
    manifest_dir = run_dir / "manifests"
    cache_dir = run_dir / "cache"
    model_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.update(
        {
            "M3_REPO_ROOT": "/root",
            "M3_ROOT": str(run_dir),
            "M3_RPPG10_DATA_ROOT": str(DATA_MOUNT / "rPPG-10" / "Dataset_rPPG-10"),
            "M3_RPPG_CACHE_DIR": str(cache_dir),
            "M3_RPPG_MODEL_DIR": str(model_dir),
            "M3_MANIFEST_DIR": str(manifest_dir),
        }
    )
    result = subprocess.run(
        ["python", "/root/m3_scripts/train_rppg10_ensemble.py"],
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    (run_dir / "stdout.log").write_text(result.stdout, encoding="utf-8")
    (run_dir / "stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        model_volume.commit()
        raise RuntimeError(f"training failed with code {result.returncode}\n{result.stderr[-4000:]}")

    metrics_path = model_dir / "metrics.json"
    metrics = json.loads(metrics_path.read_text(encoding="utf-8"))
    latest = MODEL_MOUNT / "latest-rppg10"
    if latest.exists():
        shutil.rmtree(latest)
    shutil.copytree(run_dir, latest)
    model_volume.commit()
    return {
        "run_name": run_name,
        "run_dir": str(run_dir),
        "latest_dir": str(latest),
        "metrics": metrics["metrics"],
        "deployment_model": metrics.get("deployment_model", {}),
    }


@app.local_entrypoint()
def main(run_name: str | None = None):
    name = run_name or _run_name()
    result = train_remote.remote(name)
    print(json.dumps(result, indent=2))
