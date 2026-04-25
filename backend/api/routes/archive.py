"""Archive read endpoints backed by processed JSON."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from verdict_pipeline.schema import Clip

from services import archive_service

router = APIRouter(prefix="/archive", tags=["archive"])


@router.get("", response_model=list[Clip])
def list_archive() -> list[dict]:
    return archive_service.load_archive_clips()


@router.get("/{clip_id}", response_model=Clip)
def get_archive_clip(clip_id: str) -> dict:
    clip = archive_service.get_archive_clip(clip_id)
    if clip is None:
        raise HTTPException(status_code=404, detail=f"Unknown archive clip: {clip_id}")
    return clip
