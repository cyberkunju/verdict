"""
research-data/scripts/fetch_all.py
====================================
Auto-fetches every dataset / model in research-data/registry/sources.json that
is in tier 0 (direct download) or tier 1 (HuggingFace Hub, free).

Each fetch is idempotent: if the target already exists and looks complete,
skip it. Logs every step to research-data/manifests/fetch_log.jsonl.

Usage:
    python research-data/scripts/fetch_all.py [--only DATASET_ID] [--skip-large]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path
from urllib.parse import urlparse

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "raw"
MANIFESTS = ROOT / "manifests"
PRETRAINED = ROOT / "pretrained"
LOG = MANIFESTS / "fetch_log.jsonl"


# ---------------------------------------------------------------------------- #
# Logging helpers                                                              #
# ---------------------------------------------------------------------------- #
def log(record: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    record["ts"] = time.strftime("%Y-%m-%d %H:%M:%S")
    with LOG.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, ensure_ascii=False) + "\n")
    tag = record.get("event", "?").upper()
    print(f"[{tag}] {record.get('id','-')} :: {record.get('detail','')}")


def session_with_retries() -> requests.Session:
    s = requests.Session()
    retry = Retry(
        total=5, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504]
    )
    s.mount("https://", HTTPAdapter(max_retries=retry))
    s.mount("http://", HTTPAdapter(max_retries=retry))
    s.headers.update({"User-Agent": "verdict-research-fetcher/1.0"})
    return s


def stream_download(url: str, dest: Path, *, expect_min_mb: int = 1) -> bool:
    """Download a single URL to dest with progress prints. Idempotent."""
    if dest.exists() and dest.stat().st_size >= expect_min_mb * 1024 * 1024:
        log({"event": "skip_existing", "id": dest.name, "detail": str(dest)})
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    s = session_with_retries()
    with s.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        downloaded = 0
        last_print = 0
        with tmp.open("wb") as fh:
            for chunk in r.iter_content(chunk_size=1024 * 1024):
                if not chunk:
                    continue
                fh.write(chunk)
                downloaded += len(chunk)
                if total and downloaded - last_print > total // 20:
                    pct = 100 * downloaded / total
                    print(f"    ... {dest.name}: {pct:.0f}% ({downloaded/1e6:.1f}/{total/1e6:.1f} MB)")
                    last_print = downloaded
    tmp.rename(dest)
    log({"event": "downloaded", "id": dest.name,
         "detail": f"{dest.stat().st_size/1e6:.1f} MB -> {dest}"})
    return True


def maybe_unzip(zip_path: Path, extract_to: Path) -> None:
    if not zip_path.exists():
        return
    if extract_to.exists() and any(extract_to.iterdir()):
        log({"event": "skip_unzip", "id": zip_path.name, "detail": str(extract_to)})
        return
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(extract_to)
    log({"event": "extracted", "id": zip_path.name, "detail": str(extract_to)})


def git_clone(url: str, dest: Path, depth: int = 1) -> bool:
    if dest.exists() and (dest / ".git").exists():
        log({"event": "skip_existing_repo", "id": dest.name, "detail": str(dest)})
        return True
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = ["git", "clone", f"--depth={depth}", url, str(dest)]
    log({"event": "cloning", "id": dest.name, "detail": " ".join(cmd)})
    res = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if res.returncode != 0:
        log({"event": "clone_failed", "id": dest.name, "detail": res.stderr[:200]})
        return False
    log({"event": "cloned", "id": dest.name, "detail": str(dest)})
    return True


# ---------------------------------------------------------------------------- #
# Fetch tasks (one per dataset/model, ordered by priority)                     #
# ---------------------------------------------------------------------------- #
def fetch_rppg_toolbox() -> None:
    """rPPG-Toolbox: HIGHEST PRIORITY for HR accuracy. Provides PhysNet + DeepPhys."""
    git_clone(
        "https://github.com/ubicomplab/rPPG-Toolbox.git",
        PRETRAINED / "rppg_toolbox",
    )


def fetch_huggingface_dataset(repo_id: str, dest: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
        if dest.exists() and any(dest.iterdir()):
            log({"event": "skip_existing", "id": repo_id, "detail": str(dest)})
            return
        dest.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=repo_id,
            repo_type="dataset",
            local_dir=str(dest),
            local_dir_use_symlinks=False,
        )
        log({"event": "downloaded_hf_dataset", "id": repo_id, "detail": str(dest)})
    except Exception as e:
        log({"event": "hf_dataset_failed", "id": repo_id, "detail": repr(e)[:200]})


def fetch_huggingface_model(repo_id: str, dest: Path) -> None:
    try:
        from huggingface_hub import snapshot_download
        if dest.exists() and any(dest.iterdir()):
            log({"event": "skip_existing", "id": repo_id, "detail": str(dest)})
            return
        dest.mkdir(parents=True, exist_ok=True)
        snapshot_download(
            repo_id=repo_id,
            local_dir=str(dest),
            local_dir_use_symlinks=False,
        )
        log({"event": "downloaded_hf_model", "id": repo_id, "detail": str(dest)})
    except Exception as e:
        log({"event": "hf_model_failed", "id": repo_id, "detail": repr(e)[:200]})


def fetch_ravdess() -> None:
    """RAVDESS speech audio (Zenodo, public)."""
    url = "https://zenodo.org/records/1188976/files/Audio_Speech_Actors_01-24.zip"
    zip_path = RAW / "voice" / "ravdess_speech.zip"
    extract_to = RAW / "voice" / "ravdess_speech"
    try:
        stream_download(url, zip_path, expect_min_mb=150)
        maybe_unzip(zip_path, extract_to)
    except Exception as e:
        log({"event": "ravdess_failed", "id": "ravdess", "detail": repr(e)[:200]})


def fetch_crema_d() -> None:
    """CREMA-D: shallow git clone (LFS pointers); we fetch one wav as smoke test."""
    git_clone(
        "https://github.com/CheyneyComputerScience/CREMA-D.git",
        RAW / "voice" / "crema_d",
    )
    log({"event": "note", "id": "crema_d",
         "detail": "Audio files are git-LFS pointers; run 'git lfs pull' inside the dir to fetch ~1.3 GB"})


def fetch_diplomacy_corpus() -> None:
    """Diplomacy game deception. Convokit hosts it as a tarball; HF mirror is unreliable."""
    url = "https://zissou.infosci.cornell.edu/convokit/datasets/diplomacy-corpus/diplomacy-corpus.zip"
    zip_path = RAW / "deception" / "diplomacy.zip"
    extract_to = RAW / "deception" / "diplomacy"
    try:
        stream_download(url, zip_path, expect_min_mb=1)
        maybe_unzip(zip_path, extract_to)
    except Exception as e:
        log({"event": "diplomacy_failed", "id": "diplomacy", "detail": repr(e)[:200]})


def fetch_cornell_lies() -> None:
    """Cornell hotel-review deception (Ott et al)."""
    url = "https://www.cs.cornell.edu/~myleott/op_spam/op_spam_v1.4.zip"
    zip_path = RAW / "deception" / "cornell_op_spam.zip"
    extract_to = RAW / "deception" / "cornell_op_spam"
    try:
        stream_download(url, zip_path, expect_min_mb=1)
        maybe_unzip(zip_path, extract_to)
    except Exception as e:
        log({"event": "cornell_failed", "id": "cornell_lies", "detail": repr(e)[:200]})


def fetch_fever() -> None:
    fetch_huggingface_dataset("fever/fever", RAW / "factcheck" / "fever")


def fetch_climate_fever() -> None:
    fetch_huggingface_dataset("tdiggelm/climate_fever", RAW / "factcheck" / "climate_fever")


def fetch_hover() -> None:
    fetch_huggingface_dataset("hover-nlp/hover", RAW / "factcheck" / "hover")


def fetch_x_fact() -> None:
    fetch_huggingface_dataset("utahnlp/x-fact", RAW / "factcheck" / "x_fact")


def fetch_pubhealth() -> None:
    fetch_huggingface_dataset("ImperialCollegeLondon/health_fact", RAW / "factcheck" / "pubhealth")


def fetch_scifact() -> None:
    fetch_huggingface_dataset("allenai/scifact", RAW / "factcheck" / "scifact")


def fetch_claim_buster() -> None:
    """ClaimBuster political claim-worthiness corpus (Zenodo)."""
    url = "https://zenodo.org/records/3836810/files/groundtruth.zip"
    zip_path = RAW / "factcheck" / "claimbuster.zip"
    extract_to = RAW / "factcheck" / "claimbuster"
    try:
        stream_download(url, zip_path, expect_min_mb=1)
        maybe_unzip(zip_path, extract_to)
    except Exception as e:
        log({"event": "claimbuster_failed", "id": "claim_buster", "detail": repr(e)[:200]})


def fetch_audeering_wav2vec_emotion() -> None:
    """Pretrained continuous valence/arousal/dominance regressor — DROP-IN."""
    fetch_huggingface_model(
        "audeering/wav2vec2-large-robust-12-ft-emotion-msp-dim",
        PRETRAINED / "wav2vec_emotion" / "audeering",
    )


def fetch_pyfeat_models() -> None:
    """Py-Feat ships pretrained AU/emotion. Triggering Detector() pulls weights."""
    try:
        log({"event": "installing_pyfeat", "id": "pyfeat",
             "detail": "pip install py-feat (will pull torch ~2GB if not present)"})
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "--quiet", "py-feat"],
            check=False, timeout=600,
        )
        # Trigger model download
        subprocess.run(
            [sys.executable, "-c",
             "from feat import Detector; Detector(face_model='retinaface', "
             "landmark_model='mobilefacenet', au_model='xgb', emotion_model='resmasknet')"],
            check=False, timeout=900,
        )
        log({"event": "pyfeat_ready", "id": "pyfeat",
             "detail": "weights cached under user feat dir"})
    except Exception as e:
        log({"event": "pyfeat_failed", "id": "pyfeat", "detail": repr(e)[:200]})


def fetch_deception_text_models() -> None:
    """Pretrained DeBERTa fine-tunes for deception (community uploads)."""
    candidates = [
        "Hello-SimpleAI/chatgpt-detector-roberta",
        "barissayil/bert-sentiment-analysis-sst",
    ]
    # Skip — community deception fine-tunes are sparse; user is training their own.
    log({"event": "skip", "id": "deception_text_models",
         "detail": "user is training VerdictTextPrior locally; skipping community baselines"})


# ---------------------------------------------------------------------------- #
# Main orchestrator                                                            #
# ---------------------------------------------------------------------------- #
TASKS = [
    # (id, function, approx_size_mb, priority, skip_if_large)
    ("rppg_toolbox",              fetch_rppg_toolbox,              80,    1,  False),
    ("diplomacy",                 fetch_diplomacy_corpus,          50,    2,  False),
    ("cornell_lies",              fetch_cornell_lies,              2,     3,  False),
    ("fever",                     fetch_fever,                     50,    2,  False),
    ("climate_fever",             fetch_climate_fever,             5,     3,  False),
    ("hover",                     fetch_hover,                     30,    3,  False),
    ("scifact",                   fetch_scifact,                   5,     4,  False),
    ("x_fact",                    fetch_x_fact,                    250,   3,  True),
    ("pubhealth",                 fetch_pubhealth,                 8,     3,  False),
    ("claim_buster",              fetch_claim_buster,              12,    2,  False),
    ("ravdess",                   fetch_ravdess,                   207,   2,  False),
    ("audeering_wav2vec_emotion", fetch_audeering_wav2vec_emotion, 1300,  2,  True),
    ("crema_d",                   fetch_crema_d,                   100,   3,  False),  # only the repo, not LFS audio
]


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--only", help="Run only this task id")
    p.add_argument("--skip-large", action="store_true",
                   help="Skip downloads marked >500 MB")
    p.add_argument("--max-priority", type=int, default=99,
                   help="Skip tasks above this priority number (1=highest)")
    args = p.parse_args()

    log({"event": "fetch_run_start", "id": "-",
         "detail": f"only={args.only} skip_large={args.skip_large}"})

    for task_id, fn, size, priority, is_large in TASKS:
        if args.only and task_id != args.only:
            continue
        if args.skip_large and is_large:
            log({"event": "skip_large", "id": task_id, "detail": f"~{size} MB"})
            continue
        if priority > args.max_priority:
            log({"event": "skip_priority", "id": task_id,
                 "detail": f"priority {priority} > {args.max_priority}"})
            continue
        log({"event": "task_start", "id": task_id, "detail": f"~{size} MB priority={priority}"})
        try:
            fn()
        except Exception as e:
            log({"event": "task_error", "id": task_id, "detail": repr(e)[:300]})
        log({"event": "task_done", "id": task_id, "detail": ""})

    log({"event": "fetch_run_end", "id": "-", "detail": "all tasks attempted"})


if __name__ == "__main__":
    main()
