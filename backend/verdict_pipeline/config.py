"""Centralized configuration: paths, env, runtime constants.

All paths are resolved relative to the repo root, derived from this file's
location. All env vars come from `backend/.env` (or process env if .env missing).
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

BACKEND_DIR: Path = Path(__file__).resolve().parent.parent
ROOT_DIR: Path = BACKEND_DIR.parent
DATA_DIR: Path = ROOT_DIR / "data"
RAW_CLIPS_DIR: Path = DATA_DIR / "raw_clips"
PROCESSED_DIR: Path = DATA_DIR / "processed"
REPORTS_DIR: Path = DATA_DIR / "reports"
JOBS_DIR: Path = DATA_DIR / "jobs"
RESULTS_DIR: Path = DATA_DIR / "results"
UPLOADS_DIR: Path = DATA_DIR / "uploads"
THUMBNAILS_DIR: Path = DATA_DIR / "thumbnails"

# ---------------------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------------------

load_dotenv(BACKEND_DIR / ".env", override=False)

# ---------------------------------------------------------------------------
# LLM
# ---------------------------------------------------------------------------

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.2"))

# ---------------------------------------------------------------------------
# Whisper (transcription)
# ---------------------------------------------------------------------------

WHISPER_MODEL: str = os.getenv("WHISPER_MODEL", "small")
WHISPER_DEVICE: str = os.getenv("WHISPER_DEVICE", "auto")
WHISPER_COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "auto")

# ---------------------------------------------------------------------------
# rPPG
# ---------------------------------------------------------------------------

RPPG_FPS: int = int(os.getenv("RPPG_FPS", "30"))
RPPG_LOW_HZ: float = float(os.getenv("RPPG_LOW_HZ", "0.7"))
RPPG_HIGH_HZ: float = float(os.getenv("RPPG_HIGH_HZ", "3.0"))
RPPG_WINDOW_SECONDS: int = int(os.getenv("RPPG_WINDOW_SECONDS", "10"))

# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------

LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
SCHEMA_VERSION: str = os.getenv("SCHEMA_VERSION", "1.0")


def ensure_dirs() -> None:
    """Create writable data directories on demand. Called by entry points."""
    for d in (RAW_CLIPS_DIR, PROCESSED_DIR, REPORTS_DIR, JOBS_DIR, RESULTS_DIR, UPLOADS_DIR, THUMBNAILS_DIR):
        d.mkdir(parents=True, exist_ok=True)
