"""Read helpers for the processed archive artifacts."""

from __future__ import annotations

from pathlib import Path

from verdict_pipeline.config import PROCESSED_DIR
from verdict_pipeline.schema import validate_clip
from verdict_pipeline.utils import read_json

HANDOFF_PATH = PROCESSED_DIR / "all_clips.json"


def load_archive_clips() -> list[dict]:
    if HANDOFF_PATH.exists():
        data = read_json(HANDOFF_PATH)
        if isinstance(data, list):
            return [validate_clip(item).model_dump(mode="json") for item in data]

    clips: list[dict] = []
    for path in sorted(PROCESSED_DIR.glob("*.json")):
        if path.name == "all_clips.json":
            continue
        payload = read_json(path)
        clips.append(validate_clip(payload).model_dump(mode="json"))
    return clips


def get_archive_clip(clip_id: str) -> dict | None:
    for clip in load_archive_clips():
        if clip.get("clip_id") == clip_id:
            return clip
    return None
