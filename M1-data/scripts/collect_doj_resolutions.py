"""Collect DOJ press release metadata for resolution candidates.

DOJ releases are useful as public-record resolution sources, especially for
convicted, sentenced, pleaded guilty, settled, and charged events. Charges alone
must not be treated as truth labels.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://www.justice.gov/api/v1/press_releases.json"

DEFAULT_TERMS = [
    "convicted fraud",
    "sentenced fraud",
    "pleaded guilty fraud",
    "false statements convicted",
    "securities fraud sentenced",
    "wire fraud convicted",
    "obstruction convicted",
    "settlement fraud",
]


def fetch(term: str, page: int, pagesize: int) -> dict:
    params = {
        "parameters[title]": term,
        "fields": "title,url,uuid,date,body,component,topic",
        "sort": "date",
        "direction": "DESC",
        "pagesize": str(pagesize),
        "page": str(page),
    }
    url = f"{API_URL}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "VERDICT-M1-doj-resolution-harvester/0.1"})
    with urlopen(req, timeout=60) as response:
        data = json.loads(response.read().decode("utf-8"))
    data["_query_url"] = url
    return data


def normalize_item(term: str, item: dict) -> dict:
    title = item.get("title", "")
    body = item.get("body", "")
    title_lower = title.lower()
    label_strength = "candidate_resolution"
    if any(word in title_lower for word in ["convicted", "sentenced", "pleaded guilty", "guilty plea"]):
        label_strength = "strong_resolution"
    elif "charged" in title_lower or "indicted" in title_lower:
        label_strength = "allegation_only_not_training_label"
    return {
        "source": "doj_press_releases",
        "query_term": term,
        "title": title,
        "url": item.get("url", ""),
        "uuid": item.get("uuid", ""),
        "date": item.get("date", ""),
        "component": item.get("component", ""),
        "topic": item.get("topic", ""),
        "label_strength": label_strength,
        "body_excerpt": body[:1000] if isinstance(body, str) else "",
        "audit_status": "candidate",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect DOJ resolution metadata.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--terms", nargs="*", default=DEFAULT_TERMS)
    parser.add_argument("--pages", type=int, default=2)
    parser.add_argument("--pagesize", type=int, default=50)
    args = parser.parse_args()

    out_dir = args.root / "manifests" / "doj"
    out_dir.mkdir(parents=True, exist_ok=True)
    rows: list[dict] = []
    errors: list[dict] = []

    for term in args.terms:
        for page in range(args.pages):
            try:
                data = fetch(term, page, args.pagesize)
                for item in data.get("results", []):
                    rows.append(normalize_item(term, item))
                print(f"{term!r} page={page}: {len(data.get('results', []))}")
            except Exception as exc:
                errors.append({"term": term, "page": page, "error": str(exc)})
                print(f"{term!r} page={page}: failed {exc}")

    out = out_dir / "doj_resolution_candidates.jsonl"
    with out.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    summary = {
        "rows": len(rows),
        "errors": errors,
        "terms": args.terms,
        "pages": args.pages,
        "pagesize": args.pagesize,
    }
    summary_path = out_dir / "doj_resolution_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"wrote {out} rows={len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
