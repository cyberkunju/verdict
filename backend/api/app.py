"""VERDICT product backend.

Additive service layer around the existing offline pipeline. The static JSON
handoff remains intact; this app exposes archive reads plus async analysis jobs.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from verdict_pipeline.config import ensure_dirs

from .routes import analyze, archive, calibration, health, jobs


def create_app() -> FastAPI:
    ensure_dirs()
    app = FastAPI(
        title="VERDICT Backend",
        version="0.2.0",
        description="Archive, calibration, and async analyzer service for VERDICT.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router, prefix="/api")
    app.include_router(archive.router, prefix="/api")
    app.include_router(calibration.router, prefix="/api")
    app.include_router(analyze.router, prefix="/api")
    app.include_router(jobs.router, prefix="/api")
    return app


app = create_app()
