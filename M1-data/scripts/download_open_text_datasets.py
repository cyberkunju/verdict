"""Download immediately accessible open text/claim datasets.

These are not enough for the final multimodal fusion model, but they are useful
for claim-risk, claim-type, and linguistic pretraining. Each download is stored
under ``raw/external/text_claims`` with a small manifest.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]

DATASETS = [
    {
        "dataset_id": "liar_ucsb",
        "name": "LIAR",
        "url": "https://www.cs.ucsb.edu/~william/data/liar_dataset.zip",
        "license_status": "research_use_check_original_terms",
        "use_for": ["linguistic_pretraining", "claim_truthfulness_text_baseline"],
    },
    {
        "dataset_id": "fakenewsnet_minimal",
        "name": "FakeNewsNet minimal CSVs",
        "url": "https://github.com/KaiDMML/FakeNewsNet/archive/refs/heads/master.zip",
        "license_status": "repo_terms_required_social_fields_limited",
        "use_for": ["claim_truthfulness_text_baseline", "factcheck_metadata"],
    },
    {
        "dataset_id": "datacommons_factcheck",
        "name": "DataCommons Fact Check ClaimReview",
        "url": "https://storage.googleapis.com/datacommons-feeds/factcheck/latest/data.json",
        "license_status": "cc_by_structured_claimreview_metadata",
        "use_for": ["factcheck_metadata", "linguistic_pretraining", "ground_truth_mining"],
    },
    {
        "dataset_id": "global_claims_factcheck",
        "name": "Global Claims factcheck_claims",
        "url": "https://zenodo.org/api/records/16942245/files/factcheck_claims.json/content",
        "license_status": "cc_by_4_0",
        "use_for": ["factcheck_metadata", "multilingual_linguistic_pretraining"],
    },
    {
        "dataset_id": "global_claims_url_tweets",
        "name": "Global Claims URL tweet IDs",
        "url": "https://zenodo.org/api/records/16942245/files/url_tweets.json/content",
        "license_status": "cc_by_4_0_tweet_ids_only",
        "use_for": ["source_url_popularity_metadata"],
    },
    {
        "dataset_id": "averitec_train",
        "name": "AVeriTeC train",
        "url": "https://raw.githubusercontent.com/MichSchli/AVeriTeC/main/data/train.json",
        "license_status": "cc_by_nc_4_0",
        "use_for": ["claim_verification_pretraining", "evidence_retrieval"],
    },
    {
        "dataset_id": "averitec_dev",
        "name": "AVeriTeC dev",
        "url": "https://raw.githubusercontent.com/MichSchli/AVeriTeC/main/data/dev.json",
        "license_status": "cc_by_nc_4_0",
        "use_for": ["claim_verification_pretraining", "evidence_retrieval"],
    },
]


def download(url: str, out: Path) -> None:
    req = Request(url, headers={"User-Agent": "VERDICT-M1-open-text-downloader/0.1"})
    with urlopen(req, timeout=120) as response:
        out.write_bytes(response.read())


def main() -> int:
    parser = argparse.ArgumentParser(description="Download open text claim datasets.")
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--only", nargs="*", default=None)
    args = parser.parse_args()

    out_dir = args.root / "raw" / "external" / "text_claims"
    out_dir.mkdir(parents=True, exist_ok=True)
    selected = [
        d for d in DATASETS if args.only is None or d["dataset_id"] in set(args.only)
    ]
    manifest = []
    for dataset in selected:
        if "global_claims" in dataset["dataset_id"] or dataset["url"].endswith(".json"):
            suffix = ".json"
        elif dataset["url"].endswith(".gz"):
            suffix = ".gz"
        else:
            suffix = ".zip"
        out = out_dir / f"{dataset['dataset_id']}{suffix}"
        status = "downloaded"
        error = ""
        try:
            if not out.exists():
                download(dataset["url"], out)
        except Exception as exc:
            status = "failed"
            error = str(exc)
        row = {
            **dataset,
            "local_path": str(out),
            "status": status,
            "error": error,
            "bytes": out.stat().st_size if out.exists() else 0,
        }
        manifest.append(row)
        print(f"{dataset['dataset_id']}: {status} {row['bytes']} bytes")

    manifest_path = args.root / "manifests" / "open_text_datasets_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {manifest_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
