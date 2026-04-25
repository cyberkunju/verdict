"""Download and trim a single clip via yt-dlp + bundled ffmpeg.

Examples
--------
Run by clip_id (uses metadata in ``verdict_pipeline.clips``)::

    python -m scripts.download_clip nixon_1973

Override URL / window from the CLI::

    python -m scripts.download_clip nixon_1973 \
        --url https://www.youtube.com/watch?v=XXXX \
        --start 14 --end 26
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from verdict_pipeline import clips as clip_registry
from verdict_pipeline.config import RAW_CLIPS_DIR, ensure_dirs
from verdict_pipeline.utils import ffmpeg_binary, get_logger, setup_logging


log = get_logger("download_clip")


def download(clip_id: str, url: str | None, start: float | None, end: float | None,
             out_dir: Path = RAW_CLIPS_DIR) -> Path:
    """Download a clip and trim it to ``[start, end]``.

    Returns the path to the trimmed mp4. Raises ``RuntimeError`` on failure.
    """
    meta = clip_registry.get_clip(clip_id)
    url = url or meta.video_url
    start = start if start is not None else meta.video_start_seconds
    end = end if end is not None else meta.video_end_seconds

    if not url:
        raise RuntimeError(
            f"No URL configured for {clip_id}. Edit verdict_pipeline/clips.py "
            "or pass --url."
        )
    if end <= start:
        raise RuntimeError("end must be greater than start")

    ensure_dirs()
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_path = out_dir / f"{clip_id}_full.mp4"
    trimmed_path = out_dir / f"{clip_id}.mp4"

    log.info("[bold]Downloading[/] %s -> %s", url, raw_path)
    _run([
        sys.executable, "-m", "yt_dlp",
        "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
        "-o", str(raw_path),
        "--merge-output-format", "mp4",
        "--no-playlist",
        url,
    ])

    log.info("[bold]Trimming[/] %.1fs..%.1fs -> %s", start, end, trimmed_path)
    _run([
        ffmpeg_binary(),
        "-y",
        "-i", str(raw_path),
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "18",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        str(trimmed_path),
    ])

    try:
        raw_path.unlink()
    except OSError:
        pass

    log.info("[green]done[/] %s (%.1fs)", trimmed_path, end - start)
    return trimmed_path


def _run(cmd: list[str]) -> None:
    log.debug("$ %s", " ".join(cmd))
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        log.error("command failed (%d):\n%s", proc.returncode, proc.stderr)
        raise RuntimeError(f"Command failed: {cmd[0]}")


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Download and trim a VERDICT clip.")
    p.add_argument("clip_id", help="Clip ID from verdict_pipeline.clips registry.")
    p.add_argument("--url", default=None, help="Override video URL.")
    p.add_argument("--start", type=float, default=None, help="Start seconds.")
    p.add_argument("--end", type=float, default=None, help="End seconds.")
    return p


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    args = _build_parser().parse_args(argv)
    try:
        download(args.clip_id, args.url, args.start, args.end)
    except Exception as exc:  # pragma: no cover - top-level error path
        log.exception("download failed: %s", exc)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
