"""Validate one or more clip JSON files against the locked Pydantic schema.

Usage::

    python -m scripts.validate_json data/processed/nixon_1973.json
    python -m scripts.validate_json data/processed/all_clips.json --array
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from verdict_pipeline.schema import Clip
from verdict_pipeline.utils import get_logger, setup_logging


log = get_logger("validate_json")


def validate_file(path: Path, *, is_array: bool) -> int:
    """Return number of valid clip objects; raises on invalid."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload if is_array else [payload]
    if not isinstance(items, list):
        raise ValueError(f"--array given but {path} is not a JSON array.")

    n_ok = 0
    for i, item in enumerate(items):
        try:
            Clip.model_validate(item)
            n_ok += 1
        except Exception as exc:
            log.error("invalid clip[%d] in %s: %s", i, path, exc)
            raise
    return n_ok


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(description="Validate VERDICT clip JSON files.")
    p.add_argument("paths", nargs="+", type=Path)
    p.add_argument("--array", action="store_true",
                   help="Treat each input file as a JSON array of clips.")
    args = p.parse_args(argv)

    total = 0
    for path in args.paths:
        n = validate_file(path, is_array=args.array)
        log.info("[green]ok[/] %s (%d clip%s)", path, n, "" if n == 1 else "s")
        total += n
    log.info("validated [bold]%d[/] clip object%s total.", total, "" if total == 1 else "s")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
