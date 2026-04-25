"""Discover candidate public TV claim clips through the GDELT TV API.

This collects metadata/search results only. It does not download video. Review
results manually, then convert useful entries into claim-window annotations.

Example:
    python M1-data/scripts/discover_gdelt_tv.py --query "\"I did not\"" --network CNN
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
API_URL = "https://api.gdeltproject.org/api/v2/tv/tv"


def run_query(query: str, network: str | None, max_records: int) -> dict:
    terms = query
    if network:
        terms = f"{terms} network:{network}"
    params = {
        "query": terms,
        "mode": "clipgallery",
        "format": "json",
        "maxrecords": str(max_records),
        "sort": "datedesc",
    }
    url = f"{API_URL}?{urlencode(params)}"
    req = Request(url, headers={"User-Agent": "VERDICT-M1-claim-discovery/0.1"})
    try:
        with urlopen(req, timeout=45) as response:
            payload = response.read()
        try:
            data = json.loads(payload.decode("utf-8"))
        except json.JSONDecodeError:
            data = {"raw": payload.decode("utf-8", errors="replace")}
    except Exception as exc:
        data = {"error": str(exc), "items": []}
    data["_query_url"] = url
    data["_query"] = terms
    return data


def safe_name(value: str) -> str:
    keep = [c.lower() if c.isalnum() else "_" for c in value]
    return "_".join("".join(keep).split("_"))[:80] or "query"


def main() -> int:
    parser = argparse.ArgumentParser(description="Discover GDELT TV candidate clips.")
    parser.add_argument("--query", required=True, help="GDELT TV query string.")
    parser.add_argument("--network", default=None, help="Optional network filter, e.g. CNN.")
    parser.add_argument("--max-records", type=int, default=50)
    parser.add_argument("--out-dir", type=Path, default=ROOT / "manifests" / "gdelt_tv")
    args = parser.parse_args()

    args.out_dir.mkdir(parents=True, exist_ok=True)
    data = run_query(args.query, args.network, args.max_records)
    name = safe_name(f"{args.network or 'all'}_{args.query}")
    out = args.out_dir / f"{name}.json"
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {out}")
    print(data.get("_query_url"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
