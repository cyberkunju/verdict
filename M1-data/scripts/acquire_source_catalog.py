"""Prepare compliant acquisition commands for M1 source catalog entries.

The script does not bypass access controls or dataset terms. It creates a
local acquisition checklist and, with ``--metadata-only``, saves source metadata
that can be reviewed before any downloads.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]


def load_catalog(root: Path) -> dict:
    return json.loads((root / "registry" / "source_catalog.json").read_text(encoding="utf-8"))


def write_checklist(root: Path, sources: list[dict]) -> Path:
    out = root / "manifests" / "acquisition_checklist.md"
    lines = [
        "# M1 Acquisition Checklist",
        "",
        "Review license/terms before downloading raw data.",
        "",
    ]
    for source in sources:
        lines.extend(
            [
                f"## {source['source_id']}",
                "",
                f"- Name: {source['name']}",
                f"- Category: {source['category']}",
                f"- Priority: {source['priority']}",
                f"- URL: {source['url']}",
                f"- License status: {source['license_status']}",
                f"- Use for: {', '.join(source['use_for'])}",
                "- Action: review terms, record approval, then acquire.",
                "",
            ]
        )
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def fetch_metadata(root: Path, sources: list[dict]) -> Path:
    out_dir = root / "manifests" / "source_metadata"
    out_dir.mkdir(parents=True, exist_ok=True)
    for source in sources:
        url = source["url"]
        out = out_dir / f"{source['source_id']}.txt"
        try:
            req = Request(url, headers={"User-Agent": "VERDICT-research-metadata/0.1"})
            with urlopen(req, timeout=20) as response:
                body = response.read(8192)
            out.write_bytes(body)
        except Exception as exc:
            out.write_text(f"metadata fetch failed: {exc}\nurl: {url}\n", encoding="utf-8")
    return out_dir


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare M1 source acquisition artifacts.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--metadata-only", action="store_true")
    args = parser.parse_args()

    catalog = load_catalog(args.root)
    sources = catalog["sources"]
    checklist = write_checklist(args.root, sources)
    print(f"wrote {checklist}")
    if args.metadata_only:
        out_dir = fetch_metadata(args.root, sources)
        print(f"wrote metadata snippets to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
