"""Extract poster thumbnails at clip midpoint for the locked archive."""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path
from urllib.request import urlopen

from verdict_pipeline import clips as clip_registry
from verdict_pipeline.config import RAW_CLIPS_DIR, THUMBNAILS_DIR, ensure_dirs
from verdict_pipeline.utils import ffmpeg_binary, get_logger, setup_logging

log = get_logger("extract_thumbnails")


def _youtube_thumbnail_url(video_url: str) -> str | None:
    if "v=" in video_url:
        video_id = video_url.split("v=")[-1].split("&")[0]
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    if "youtu.be/" in video_url:
        video_id = video_url.split("youtu.be/")[-1].split("?")[0]
        return f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg"
    return None


def _download_remote_thumbnail(clip_id: str, video_url: str) -> Path:
    remote_url = _youtube_thumbnail_url(video_url)
    if not remote_url:
        raise FileNotFoundError(f"No thumbnail source available for {clip_id}")
    out = THUMBNAILS_DIR / f"{clip_id}.jpg"
    with urlopen(remote_url, timeout=20) as response:  # noqa: S310
        out.write_bytes(response.read())
    log.info("thumbnail fallback %s -> %s", remote_url, out)
    return out


def extract_thumbnail(clip_id: str, *, source_path: Path | None = None) -> Path:
    meta = clip_registry.get_clip(clip_id)
    ensure_dirs()
    source = source_path or (RAW_CLIPS_DIR / f"{clip_id}.mp4")
    if not source.exists():
        return _download_remote_thumbnail(clip_id, meta.video_url)
    midpoint = max((meta.video_end_seconds - meta.video_start_seconds) / 2.0, 0.1)
    out = THUMBNAILS_DIR / f"{clip_id}.jpg"
    cmd = [
        ffmpeg_binary(),
        "-y",
        "-ss",
        f"{midpoint:.3f}",
        "-i",
        str(source),
        "-frames:v",
        "1",
        "-q:v",
        "2",
        str(out),
    ]
    proc = subprocess.run(cmd, check=False, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr[-400:] or f"ffmpeg failed for {clip_id}")
    log.info("thumbnail %s -> %s", clip_id, out)
    return out


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract archive thumbnails.")
    parser.add_argument("--only", nargs="*", default=None, help="Optional subset of clip_ids")
    args = parser.parse_args(argv)

    targets = args.only or clip_registry.all_clip_ids()
    failures = 0
    for clip_id in targets:
        try:
            extract_thumbnail(clip_id)
        except Exception as exc:
            failures += 1
            log.warning("thumbnail failed for %s: %s", clip_id, exc)
    return 1 if failures else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
