"""Convenience entry: run the full pipeline on a single clip and print the JSON.

Examples
--------
::

    python -m scripts.run_one_clip nixon_1973
    python -m scripts.run_one_clip haugen_2021 --no-write
"""

from __future__ import annotations

import argparse
import json

from verdict_pipeline.batch import process_clip, write_outputs
from verdict_pipeline.utils import get_logger, setup_logging


log = get_logger("run_one_clip")


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(description="Run VERDICT pipeline on one clip.")
    p.add_argument("clip_id", help="Clip ID from the registry.")
    p.add_argument(
        "--no-write",
        action="store_true",
        help="Skip writing JSON to data/processed.",
    )
    args = p.parse_args(argv)

    payload = process_clip(args.clip_id)
    if not args.no_write:
        write_outputs([payload])
    print(json.dumps(payload, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
