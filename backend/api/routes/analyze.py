"""Async analysis submission endpoints."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from verdict_pipeline.config import UPLOADS_DIR, ensure_dirs

from api.schemas import AnalyzeAcceptedResponse, AnalyzeUrlRequest
from services import job_service, result_store

router = APIRouter(prefix="/analyze", tags=["analyze"])


@router.post("/url", response_model=AnalyzeAcceptedResponse, status_code=202)
def analyze_url(req: AnalyzeUrlRequest, background_tasks: BackgroundTasks) -> AnalyzeAcceptedResponse:
    job = result_store.create_job("url", req.model_dump(mode="json"))
    background_tasks.add_task(job_service.run_url_job, job["job_id"])
    return AnalyzeAcceptedResponse(
        job_id=job["job_id"],
        status=job["status"],
        status_url=f"/api/jobs/{job['job_id']}",
        result_url=f"/api/jobs/{job['job_id']}/result",
    )


@router.post("/upload", response_model=AnalyzeAcceptedResponse, status_code=202)
async def analyze_upload(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    start_seconds: float | None = Form(default=None),
    end_seconds: float | None = Form(default=None),
    subject: str | None = Form(default=None),
    statement: str | None = Form(default=None),
    context: str | None = Form(default=None),
    year: int | None = Form(default=None),
) -> AnalyzeAcceptedResponse:
    ensure_dirs()
    payload = {
        "filename": file.filename or "upload.mp4",
        "start_seconds": start_seconds,
        "end_seconds": end_seconds,
        "subject": subject,
        "statement": statement,
        "context": context,
        "year": year,
    }
    job = result_store.create_job("upload", payload)
    target = UPLOADS_DIR / f"{job['job_id']}_{Path(payload['filename']).name}"
    target.write_bytes(await file.read())
    result_store.update_job(job["job_id"], request={**payload, "stored_path": str(target)})
    background_tasks.add_task(job_service.run_upload_job, job["job_id"])
    return AnalyzeAcceptedResponse(
        job_id=job["job_id"],
        status="queued",
        status_url=f"/api/jobs/{job['job_id']}",
        result_url=f"/api/jobs/{job['job_id']}/result",
    )
