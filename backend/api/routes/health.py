"""Health and service readiness endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import HealthResponse
from services import archive_service, result_store

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def healthcheck() -> HealthResponse:
    clips = archive_service.load_archive_clips()
    jobs = result_store.list_jobs()
    return HealthResponse(
        status="ok",
        archive_clip_count=len(clips),
        processed_ready=len(clips) > 0,
        job_count=len(jobs),
    )
