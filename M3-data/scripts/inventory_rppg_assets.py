"""Inventory available M3 rPPG assets.

This script records local source repositories, access forms, and pretrained
rPPG-Toolbox checkpoints without copying large binaries into git.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
M3 = ROOT / "M3-data"
RESEARCH = ROOT / "research-data"
TOOLBOX = RESEARCH / "pretrained" / "rppg_toolbox"


def sha256(path: Path, chunk_size: int = 1024 * 1024) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(chunk_size), b""):
            digest.update(chunk)
    return digest.hexdigest()


def checkpoint_manifest() -> list[dict]:
    release = TOOLBOX / "final_model_release"
    rows: list[dict] = []
    if not release.exists():
        return rows
    for path in sorted(release.glob("*.pth")):
        name = path.name
        dataset = name.split("_", 1)[0]
        model = name[len(dataset) + 1 :].replace(".pth", "") if "_" in name else name
        rows.append(
            {
                "name": name,
                "dataset_hint": dataset,
                "model_hint": model,
                "path": str(path.relative_to(ROOT)),
                "bytes": path.stat().st_size,
                "sha256": sha256(path),
            }
        )
    return rows


def mmpd_metadata_summary() -> dict:
    mmpd = M3 / "sources" / "MMPD_rPPG_dataset"
    summary: dict = {"present": mmpd.exists(), "path": str(mmpd.relative_to(ROOT))}
    meta = mmpd / "meta_label.csv"
    if meta.exists():
        with meta.open("r", encoding="utf-8-sig", newline="") as fh:
            reader = csv.DictReader(fh)
            rows = list(reader)
        summary["metadata_rows"] = len(rows)
        for key in ["light", "motion", "exercise", "skin_color", "gender"]:
            vals = sorted({str(row.get(key, "")).strip() for row in rows if row.get(key)})
            summary[f"{key}_values"] = vals
    for fname in ["MMPD_Release_Agreement.pdf", "Data Usage Protocol.pdf", "size_MMPD.csv", "size_mini_MMPD.csv"]:
        f = mmpd / fname
        summary[fname] = {"present": f.exists(), "bytes": f.stat().st_size if f.exists() else 0}
    return summary


def main() -> None:
    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "toolbox_present": TOOLBOX.exists(),
        "toolbox_path": str(TOOLBOX.relative_to(ROOT)) if TOOLBOX.exists() else None,
        "pretrained_checkpoints": checkpoint_manifest(),
        "mmpd_metadata": mmpd_metadata_summary(),
    }
    out = M3 / "manifests" / "rppg_asset_inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
