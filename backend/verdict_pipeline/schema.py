"""Pydantic v2 schema mirroring CONTRACT.md §2.

This module is the single canonical schema definition for the backend.
If CONTRACT.md changes, this file changes in the same commit.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

GroundTruth = Literal["true", "false", "sincere"]
SignalQualityFlag = Literal["real", "fallback", "manual"]


# ---------------------------------------------------------------------------
# Sub-models
# ---------------------------------------------------------------------------


class TimelinePoint(BaseModel):
    """One sample of the per-frame timeline (time aligned across signals)."""

    model_config = ConfigDict(extra="forbid")

    t: float = Field(ge=0, description="Seconds from clip start.")
    hr: float = Field(ge=0, le=240)
    f0: float = Field(ge=0, le=1000)
    au15: float = Field(ge=0, le=5)
    deception: float = Field(ge=0, le=100)


class ClipSignals(BaseModel):
    """All extracted physiological / facial / vocal / linguistic signals."""

    model_config = ConfigDict(extra="forbid")

    # rPPG
    hr_baseline_bpm: float = Field(ge=0, le=240)
    hr_peak_bpm: float = Field(ge=0, le=240)
    hr_delta_bpm: float
    hrv_rmssd_ms: float = Field(ge=0)

    # Facial Action Units (Py-Feat 0–5 intensity scale)
    au15_max_intensity: float = Field(ge=0, le=5)
    au14_max_intensity: float = Field(ge=0, le=5)
    au6_present: bool
    au24_max_intensity: float = Field(ge=0, le=5)

    # Voice
    f0_baseline_hz: float = Field(ge=0, le=1000)
    f0_peak_hz: float = Field(ge=0, le=1000)
    f0_delta_hz: float
    jitter_percent: float = Field(ge=0, le=100)
    shimmer_db: float = Field(ge=0)
    speech_rate_wpm: float = Field(ge=0, le=400)

    # Linguistic
    hedging_count: int = Field(ge=0)
    pronoun_drop_rate: float = Field(ge=0, le=1)
    transcript: str

    # Synchronized timeline (≥10 points required by contract)
    timeline: list[TimelinePoint] = Field(min_length=10)


class ClipScores(BaseModel):
    """Four composite scores, all integers in 0–100."""

    model_config = ConfigDict(extra="forbid")

    deception: int = Field(ge=0, le=100)
    sincerity: int = Field(ge=0, le=100)
    stress: int = Field(ge=0, le=100)
    confidence: int = Field(ge=0, le=100)


class ClipReport(BaseModel):
    """LLM analyst output, three required sections."""

    model_config = ConfigDict(extra="forbid")

    behavioral_summary: str = Field(min_length=10)
    comparative_profile: str = Field(min_length=10)
    qualifications: str = Field(min_length=10)


class SignalQuality(BaseModel):
    """Provenance flag per signal channel."""

    model_config = ConfigDict(extra="forbid")

    rppg: SignalQualityFlag
    facial_au: SignalQualityFlag
    voice: SignalQualityFlag
    transcript: SignalQualityFlag


# ---------------------------------------------------------------------------
# Top-level Clip object
# ---------------------------------------------------------------------------


class Clip(BaseModel):
    """The handoff artifact. One JSON file per clip + an array of all six."""

    model_config = ConfigDict(extra="forbid")

    schema_version: Literal["1.0"]
    clip_id: str = Field(pattern=r"^[a-z0-9]+(?:_[a-z0-9]+)+$")
    subject: str = Field(min_length=1)
    statement: str = Field(min_length=1)
    year: int = Field(ge=1900, le=2100)
    context: str = Field(min_length=1)
    ground_truth: GroundTruth
    ground_truth_source: str = Field(min_length=1)
    video_url: str = Field(min_length=1)
    video_start_seconds: float = Field(ge=0)
    video_end_seconds: float = Field(gt=0)
    thumbnail_url: str
    signals: ClipSignals
    scores: ClipScores
    llm_report: ClipReport
    similar_clips: list[str] = Field(default_factory=list)
    signal_quality: SignalQuality

    @field_validator("similar_clips")
    @classmethod
    def lowercase_clip_ids(cls, v: list[str]) -> list[str]:
        return [s.lower() for s in v]

    @model_validator(mode="after")
    def end_after_start(self) -> "Clip":
        if self.video_end_seconds <= self.video_start_seconds:
            raise ValueError(
                "video_end_seconds must be greater than video_start_seconds"
            )
        return self


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------


def validate_clip(payload: dict) -> Clip:
    """Validate a raw dict against the Clip schema. Raises on invalid."""
    return Clip.model_validate(payload)


def serialize_clip(clip: Clip) -> dict:
    """Serialize a Clip to a JSON-ready dict."""
    return clip.model_dump(mode="json")
