"""Validate M1-data JSON and JSONL registries.

This intentionally validates metadata only. Raw datasets may require separate
license agreements and should not be blindly downloaded.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_source_catalog(path: Path) -> None:
    data = load_json(path)
    if not isinstance(data, dict):
        raise ValueError(f"{path} must be a JSON object")
    sources = data.get("sources")
    if not isinstance(sources, list) or not sources:
        raise ValueError(f"{path} must contain non-empty sources[]")
    seen: set[str] = set()
    for idx, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"source[{idx}] must be an object")
        source_id = source.get("source_id")
        if not source_id:
            raise ValueError(f"source[{idx}] missing source_id")
        if source_id in seen:
            raise ValueError(f"duplicate source_id: {source_id}")
        seen.add(str(source_id))
        for key in ("name", "category", "url", "license_status", "priority", "use_for"):
            if key not in source:
                raise ValueError(f"{source_id} missing {key}")


def validate_seed_claims(path: Path) -> None:
    required = {
        "claim_id",
        "source_id",
        "subject",
        "claim_text",
        "claim_start_seconds",
        "claim_end_seconds",
        "ground_truth_label",
        "ground_truth_source_url",
        "label_confidence",
        "context_type",
        "claim_type",
        "train_eligible",
    }
    seen: set[str] = set()
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not line.strip():
            continue
        row = json.loads(line)
        missing = required - set(row)
        if missing:
            raise ValueError(f"{path}:{line_no} missing {sorted(missing)}")
        claim_id = row["claim_id"]
        if claim_id in seen:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        seen.add(claim_id)
        if row["claim_end_seconds"] <= row["claim_start_seconds"]:
            raise ValueError(f"{claim_id} has invalid time range")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate M1-data catalog files.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    root = args.root
    validate_source_catalog(root / "registry" / "source_catalog.json")
    load_json(root / "registry" / "claim_schema.json")
    load_json(root / "registry" / "feature_schema.json")
    load_json(root / "manifests" / "discovery_queries.json")
    validate_seed_claims(root / "manifests" / "seed_claims.jsonl")
    print("M1-data catalog validation ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
