"""Validate local rPPG dataset layout before training.

The script does not download restricted datasets. It checks whether acquired
datasets are arranged in the structure expected by the M3/rPPG-Toolbox plan.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
M3 = ROOT / "M3-data"


EXPECTED = {
    "UBFC-rPPG": ["subject*/vid.avi", "subject*/ground_truth.txt"],
    "PURE": ["*/*/*.png", "*/*.json"],
    "MMPD": ["subject*/p*_*.mat"],
    "VitalVideo": ["**/*.mp4", "**/*.json"],
    "UBFC-Phys": ["**/*.avi", "**/*.csv"],
    "VIPL-HR-V2": ["**/*.avi"],
    "rPPG-10": ["dataset/Dataset_rPPG-10/Subject_*/*_ECG.npy", "dataset/Dataset_rPPG-10/Subject_*/*.avi"],
}


def count_matches(base: Path, patterns: list[str]) -> dict[str, int]:
    return {pattern: len(list(base.glob(pattern))) for pattern in patterns}


def main() -> None:
    roots = [M3 / "raw" / "public", M3 / "raw" / "restricted", M3 / "raw" / "own-capture"]
    report = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "datasets": {},
    }
    for dataset, patterns in EXPECTED.items():
        dataset_report = []
        for root in roots:
            base = root / dataset
            dataset_report.append(
                {
                    "path": str(base.relative_to(ROOT)),
                    "present": base.exists(),
                    "matches": count_matches(base, patterns) if base.exists() else {},
                }
            )
        report["datasets"][dataset] = dataset_report
    out = M3 / "manifests" / "rppg_dataset_layout_report.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
