"""Background job runner for URL and upload analyses."""

from __future__ import annotations

from pathlib import Path

from services import analysis_service, ingest_service, result_store


def run_url_job(job_id: str) -> None:
    job = result_store.get_job(job_id)
    if job is None:
        raise FileNotFoundError(f"Unknown job: {job_id}")
    req = job["request"]
    try:
        start_seconds = req.get("start_seconds")
        end_seconds = req.get("end_seconds")
        if start_seconds is None and end_seconds is None:
            # Fast default window for live URL analysis.
            start_seconds = 0.0
            end_seconds = 45.0

        result_store.update_job(job_id, status="downloading")
        video_path = ingest_service.download_external_video(
            job_id=job_id,
            url=req["url"],
            start_seconds=start_seconds,
            end_seconds=end_seconds,
        )
        result_store.update_job(
            job_id,
            status="extracting",
            request={**req, "start_seconds": start_seconds, "end_seconds": end_seconds, "video_path": str(video_path)},
        )

        def _progress(phase: str) -> None:
            result_store.update_job(job_id, status=phase)

        payload = analysis_service.analyze_video(
            video_path=video_path,
            source_url=req["url"],
            start_seconds=start_seconds,
            end_seconds=end_seconds,
            subject=req.get("subject"),
            statement=req.get("statement"),
            context=req.get("context"),
            year=req.get("year"),
            progress=_progress,
        )
        result_store.update_job(job_id, status="synthesizing")
        result = result_store.save_result(job_id, payload)
        result_store.update_job(job_id, status="completed", result_id=result["result_id"])
    except Exception as exc:
        result_store.update_job(job_id, status="failed", error=str(exc))


def run_upload_job(job_id: str) -> None:
    job = result_store.get_job(job_id)
    if job is None:
        raise FileNotFoundError(f"Unknown job: {job_id}")
    req = job["request"]
    try:
        source_path = Path(req["stored_path"])
        video_path = source_path
        if req.get("start_seconds") is not None and req.get("end_seconds") is not None:
            result_store.update_job(job_id, status="trimming")
            trimmed = source_path.with_name(f"{source_path.stem}_trimmed.mp4")
            video_path = ingest_service.trim_video(
                source_path=source_path,
                target_path=trimmed,
                start_seconds=float(req["start_seconds"]),
                end_seconds=float(req["end_seconds"]),
            )
        result_store.update_job(job_id, status="extracting")

        def _progress(phase: str) -> None:
            result_store.update_job(job_id, status=phase)

        payload = analysis_service.analyze_video(
            video_path=video_path,
            source_url="",
            start_seconds=req.get("start_seconds"),
            end_seconds=req.get("end_seconds"),
            subject=req.get("subject"),
            statement=req.get("statement"),
            context=req.get("context"),
            year=req.get("year"),
            progress=_progress,
        )
        result_store.update_job(job_id, status="synthesizing")
        result = result_store.save_result(job_id, payload)
        result_store.update_job(job_id, status="completed", result_id=result["result_id"])
    except Exception as exc:
        result_store.update_job(job_id, status="failed", error=str(exc))
