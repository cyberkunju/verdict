"""Job status and result retrieval endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from api.schemas import AnalysisResultResponse, JobStatusResponse
from services import result_store

router = APIRouter(tags=["jobs"])


@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
def get_job(job_id: str) -> JobStatusResponse:
    job = result_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}")
    return JobStatusResponse.model_validate(job)


@router.get("/jobs/{job_id}/result", response_model=AnalysisResultResponse)
def get_job_result(job_id: str) -> AnalysisResultResponse:
    job = result_store.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Unknown job: {job_id}")
    if job.get("status") != "completed" or not job.get("result_id"):
        raise HTTPException(status_code=409, detail=f"Job {job_id} is not completed yet")
    result = result_store.get_result(job["result_id"])
    if result is None:
        raise HTTPException(status_code=404, detail=f"Missing result for job: {job_id}")
    return AnalysisResultResponse.model_validate(result)


@router.get("/results/{result_id}", response_model=AnalysisResultResponse)
def get_result(result_id: str) -> AnalysisResultResponse:
    result = result_store.get_result(result_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Unknown result: {result_id}")
    return AnalysisResultResponse.model_validate(result)
