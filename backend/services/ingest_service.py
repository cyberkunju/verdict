"""Input acquisition helpers for analyzer jobs."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from verdict_pipeline.config import RAW_CLIPS_DIR, UPLOADS_DIR, ensure_dirs
from verdict_pipeline.utils import ffmpeg_binary


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-400:] or f"Command failed: {cmd[0]}")


def download_external_video(
    *,
    job_id: str,
    url: str,
    start_seconds: float | None,
    end_seconds: float | None,
) -> Path:
    ensure_dirs()
    raw_path = RAW_CLIPS_DIR / f"{job_id}_full.mp4"
    _run(
        [
            sys.executable,
            "-m",
            "yt_dlp",
            "-f",
            "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
            "-o",
            str(raw_path),
            "--merge-output-format",
            "mp4",
            "--no-playlist",
            "--ffmpeg-location",
            ffmpeg_binary(),
            url,
        ]
    )

    if start_seconds is None or end_seconds is None:
        return raw_path

    trimmed_path = RAW_CLIPS_DIR / f"{job_id}.mp4"
    trim_video(source_path=raw_path, target_path=trimmed_path, start_seconds=start_seconds, end_seconds=end_seconds)
    try:
        raw_path.unlink()
    except OSError:
        pass
    return trimmed_path


def trim_video(
    *,
    source_path: Path,
    target_path: Path,
    start_seconds: float,
    end_seconds: float,
) -> Path:
    ensure_dirs()
    _run(
        [
            ffmpeg_binary(),
            "-y",
            "-i",
            str(source_path),
            "-ss",
            f"{start_seconds:.3f}",
            "-to",
            f"{end_seconds:.3f}",
            "-c:v",
            "libx264",
            "-preset",
            "veryfast",
            "-crf",
            "18",
            "-c:a",
            "aac",
            "-b:a",
            "192k",
            "-movflags",
            "+faststart",
            str(target_path),
        ]
    )
    return target_path


def uploaded_target(job_id: str, filename: str) -> Path:
    ensure_dirs()
    return UPLOADS_DIR / f"{job_id}_{Path(filename).name}"
