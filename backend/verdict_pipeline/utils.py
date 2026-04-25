"""Shared utilities: logging, JSON I/O, ffmpeg path, timing."""

from __future__ import annotations

import json
import logging
import shutil
import time
from pathlib import Path
from typing import Any

try:
    import imageio_ffmpeg
except ImportError:  # pragma: no cover - optional runtime fallback
    imageio_ffmpeg = None
from rich.logging import RichHandler


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------


def setup_logging(level: str = "INFO") -> None:
    """Install a Rich-based root handler. Idempotent."""
    root = logging.getLogger()
    if any(isinstance(h, RichHandler) for h in root.handlers):
        return
    root.handlers.clear()
    handler = RichHandler(
        rich_tracebacks=True,
        show_path=False,
        markup=True,
    )
    formatter = logging.Formatter("%(message)s", datefmt="[%X]")
    handler.setFormatter(formatter)
    root.addHandler(handler)
    root.setLevel(level)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


# ---------------------------------------------------------------------------
# JSON I/O
# ---------------------------------------------------------------------------


def write_json(path: Path | str, data: Any, *, indent: int = 2) -> Path:
    """Write a JSON-serializable object to ``path``. Returns the path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(
        json.dumps(data, indent=indent, ensure_ascii=False),
        encoding="utf-8",
    )
    return p


def read_json(path: Path | str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# ffmpeg
# ---------------------------------------------------------------------------


def ffmpeg_binary() -> str:
    """Absolute path to the bundled ffmpeg executable.

    Avoids any system-wide ffmpeg install requirement.
    """
    if imageio_ffmpeg is not None:
        return imageio_ffmpeg.get_ffmpeg_exe()
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg
    raise RuntimeError("ffmpeg not available: install imageio-ffmpeg or system ffmpeg")


# ---------------------------------------------------------------------------
# Timing
# ---------------------------------------------------------------------------


class Timer:
    """Tiny context manager for wall-clock timing.

    Example:
        with Timer("rppg") as t:
            run_rppg()
        log.info("rppg took %.2fs", t.elapsed)
    """

    def __init__(self, label: str = "") -> None:
        self.label = label
        self.elapsed: float = 0.0
        self._t0: float = 0.0

    def __enter__(self) -> "Timer":
        self._t0 = time.perf_counter()
        return self

    def __exit__(self, *_exc: object) -> None:
        self.elapsed = time.perf_counter() - self._t0
