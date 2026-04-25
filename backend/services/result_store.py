"""Filesystem-backed persistence for jobs and live analysis results."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from verdict_pipeline.config import JOBS_DIR, RESULTS_DIR, ensure_dirs
from verdict_pipeline.utils import read_json, write_json


def _ts() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _job_path(job_id: str) -> Path:
    return JOBS_DIR / f"{job_id}.json"


def _result_path(result_id: str) -> Path:
    return RESULTS_DIR / f"{result_id}.json"


def create_job(input_type: str, request: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    now = _ts()
    job = {
        "job_id": f"job_{uuid4().hex[:12]}",
        "status": "queued",
        "input_type": input_type,
        "request": request,
        "created_at": now,
        "updated_at": now,
        "result_id": None,
        "error": None,
    }
    write_json(_job_path(job["job_id"]), job)
    return job


def update_job(job_id: str, **fields: Any) -> dict[str, Any]:
    job = get_job(job_id)
    if job is None:
        raise FileNotFoundError(f"Unknown job: {job_id}")
    job.update(fields)
    job["updated_at"] = _ts()
    write_json(_job_path(job_id), job)
    return job


def get_job(job_id: str) -> dict[str, Any] | None:
    path = _job_path(job_id)
    if not path.exists():
        return None
    return read_json(path)


def list_jobs() -> list[dict[str, Any]]:
    ensure_dirs()
    jobs = [read_json(path) for path in sorted(JOBS_DIR.glob("*.json"))]
    return sorted(jobs, key=lambda item: item.get("created_at", ""), reverse=True)


def save_result(job_id: str, payload: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    result = {
        "result_id": f"res_{uuid4().hex[:12]}",
        "job_id": job_id,
        "status": "completed",
        "payload": payload,
    }
    write_json(_result_path(result["result_id"]), result)
    return result


def get_result(result_id: str) -> dict[str, Any] | None:
    path = _result_path(result_id)
    if not path.exists():
        return None
    return read_json(path)
