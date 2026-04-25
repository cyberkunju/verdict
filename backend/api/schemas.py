"""HTTP request/response schemas for the product backend."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, HttpUrl

from verdict_pipeline.schema import ClipReport, ClipScores, ClipSignals, SignalQuality


class HealthResponse(BaseModel):
    status: Literal["ok"]
    archive_clip_count: int
    processed_ready: bool
    job_count: int


class CalibrationPoint(BaseModel):
    clip_id: str
    subject: str
    ground_truth: str
    predicted_label: str
    deception: int
    sincerity: int
    stress: int
    confidence: int


class CalibrationSummary(BaseModel):
    total_clips: int
    accuracy_percent: int
    confusion_matrix: dict[str, dict[str, int]]
    scatter_points: list[CalibrationPoint]
    signal_quality_counts: dict[str, dict[str, int]]


class AnalyzeUrlRequest(BaseModel):
    url: HttpUrl
    start_seconds: float | None = Field(default=None, ge=0)
    end_seconds: float | None = Field(default=None, ge=0)
    subject: str | None = None
    statement: str | None = None
    context: str | None = None
    year: int | None = None


class AnalyzeAcceptedResponse(BaseModel):
    job_id: str
    status: str
    status_url: str
    result_url: str


class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    input_type: str
    request: dict[str, Any]
    created_at: str
    updated_at: str
    result_id: str | None = None
    error: str | None = None


class SimilarArchiveMatch(BaseModel):
    clip_id: str
    subject: str
    statement: str
    ground_truth: str
    similarity: float
    scores: ClipScores


class TextPriorInference(BaseModel):
    model_name: str
    statement_used: str
    statement_source: str
    probability_resolved_false: float | None = None
    label: Literal["likely_false", "uncertain", "likely_true", "unavailable"]
    confidence: int | None = None


class LiveAnalysisPayload(BaseModel):
    subject: str
    statement: str
    year: int | None = None
    context: str
    video_url: str = ""
    video_start_seconds: float = Field(default=0, ge=0)
    video_end_seconds: float = Field(default=0, ge=0)
    thumbnail_url: str = ""
    signals: ClipSignals
    scores: ClipScores
    llm_report: ClipReport
    signal_quality: SignalQuality
    similar_archive_matches: list[SimilarArchiveMatch] = Field(default_factory=list)
    text_prior: TextPriorInference | None = None


class AnalysisResultResponse(BaseModel):
    result_id: str
    job_id: str
    status: Literal["completed"]
    payload: LiveAnalysisPayload
