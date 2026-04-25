"""Calibration summary endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.schemas import CalibrationSummary
from services.calibration_service import build_calibration_summary

router = APIRouter(prefix="/calibration", tags=["calibration"])


@router.get("/summary", response_model=CalibrationSummary)
def get_calibration_summary() -> CalibrationSummary:
    return CalibrationSummary.model_validate(build_calibration_summary())
