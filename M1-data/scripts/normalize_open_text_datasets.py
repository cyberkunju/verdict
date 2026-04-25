"""Normalize downloaded open text datasets into JSONL feature-pretraining rows.

Outputs are local data artifacts under ``processed/text_claims`` and are
gitignored. A tracked count summary is written to ``manifests``.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

csv.field_size_limit(min(sys.maxsize, 2_147_483_647))


def normalize_liar(zip_path: Path, out_dir: Path) -> dict:
    label_map = {
        "pants-fire": "resolved_false",
        "false": "resolved_false",
        "barely-true": "contested_or_partial",
        "half-true": "contested_or_partial",
        "mostly-true": "contested_or_partial",
        "true": "resolved_true",
    }
    counts: dict[str, int] = {}
    out_path = out_dir / "liar_ucsb_claims.jsonl"
    with zipfile.ZipFile(zip_path) as zf, out_path.open("w", encoding="utf-8") as out:
        for split in ("train", "valid", "test"):
            with zf.open(f"{split}.tsv") as fh:
                reader = csv.reader((line.decode("utf-8", errors="replace") for line in fh), delimiter="\t")
                for row in reader:
                    if len(row) < 14:
                        continue
                    label = row[1]
                    mapped = label_map.get(label, "unclear")
                    record = {
                        "dataset_id": "liar_ucsb",
                        "split": split,
                        "source_row_id": row[0],
                        "label_original": label,
                        "label_mapped": mapped,
                        "claim_text": row[2],
                        "subject": row[4],
                        "speaker": row[5],
                        "speaker_job": row[6],
                        "state": row[7],
                        "party": row[8],
                        "context": row[13],
                        "train_eligible_for_fusion": False,
                        "use_for": ["linguistic_pretraining"],
                    }
                    counts[mapped] = counts.get(mapped, 0) + 1
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"dataset_id": "liar_ucsb", "output": str(out_path), "counts": counts, "rows": sum(counts.values())}


def normalize_fakenewsnet(zip_path: Path, out_dir: Path) -> dict:
    files = {
        "FakeNewsNet-master/dataset/politifact_fake.csv": "resolved_false",
        "FakeNewsNet-master/dataset/politifact_real.csv": "resolved_true",
        "FakeNewsNet-master/dataset/gossipcop_fake.csv": "resolved_false",
        "FakeNewsNet-master/dataset/gossipcop_real.csv": "resolved_true",
    }
    counts: dict[str, int] = {}
    out_path = out_dir / "fakenewsnet_minimal_claims.jsonl"
    with zipfile.ZipFile(zip_path) as zf, out_path.open("w", encoding="utf-8") as out:
        for name, mapped in files.items():
            with zf.open(name) as fh:
                reader = csv.DictReader((line.decode("utf-8", errors="replace") for line in fh))
                for row in reader:
                    record = {
                        "dataset_id": "fakenewsnet_minimal",
                        "source_file": name,
                        "source_row_id": row.get("id", ""),
                        "label_mapped": mapped,
                        "claim_text": row.get("title", ""),
                        "source_url": row.get("news_url") or row.get("url", ""),
                        "tweet_ids_present": bool(row.get("tweet_ids")),
                        "train_eligible_for_fusion": False,
                        "use_for": ["linguistic_pretraining", "factcheck_metadata"],
                    }
                    counts[mapped] = counts.get(mapped, 0) + 1
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {
        "dataset_id": "fakenewsnet_minimal",
        "output": str(out_path),
        "counts": counts,
        "rows": sum(counts.values()),
    }


def map_rating(value: str) -> str:
    normalized = (value or "").strip().lower()
    false_terms = {
        "false",
        "pants on fire",
        "pants-fire",
        "incorrect",
        "fake",
        "misleading",
        "mostly false",
        "partly false",
        "no evidence",
        "not true",
        "fabricated",
        "hoax",
    }
    true_terms = {"true", "correct", "mostly true", "accurate", "verified"}
    if normalized in false_terms or "false" in normalized or "fake" in normalized:
        return "resolved_false"
    if normalized in true_terms or normalized == "yes":
        return "resolved_true"
    return "contested_or_partial"


def normalize_datacommons(json_path: Path, out_dir: Path) -> dict:
    out_path = out_dir / "datacommons_factcheck_claims.jsonl"
    data = json.loads(json_path.read_text(encoding="utf-8"))
    counts: dict[str, int] = {}
    rows = 0
    with out_path.open("w", encoding="utf-8") as out:
        for feed_item in data.get("dataFeedElement", []):
            items = feed_item.get("item", [])
            if items is None:
                items = []
            if isinstance(items, dict):
                items = [items]
            for item in items:
                if not isinstance(item, dict):
                    continue
                rating = item.get("reviewRating", {})
                if isinstance(rating, dict):
                    rating_value = rating.get("alternateName") or rating.get("ratingValue") or ""
                else:
                    rating_value = ""
                mapped = map_rating(str(rating_value))
                author = item.get("author", {})
                reviewed = item.get("itemReviewed", {})
                reviewed_author = reviewed.get("author", {}) if isinstance(reviewed, dict) else {}
                record = {
                    "dataset_id": "datacommons_factcheck",
                    "source_url": item.get("url") or feed_item.get("url", ""),
                    "publisher": author.get("name", "") if isinstance(author, dict) else "",
                    "date_published": item.get("datePublished", ""),
                    "label_original": rating_value,
                    "label_mapped": mapped,
                    "claim_text": item.get("claimReviewed", ""),
                    "speaker": reviewed_author.get("name", "") if isinstance(reviewed_author, dict) else "",
                    "train_eligible_for_fusion": False,
                    "use_for": ["linguistic_pretraining", "factcheck_metadata"],
                }
                if record["claim_text"]:
                    counts[mapped] = counts.get(mapped, 0) + 1
                    rows += 1
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"dataset_id": "datacommons_factcheck", "output": str(out_path), "counts": counts, "rows": rows}


def normalize_global_claims(jsonl_path: Path, out_dir: Path) -> dict:
    out_path = out_dir / "global_claims_factcheck_claims.jsonl"
    counts: dict[str, int] = {}
    rows = 0
    with jsonl_path.open(encoding="utf-8", errors="replace") as fh, out_path.open("w", encoding="utf-8") as out:
        for line in fh:
            if not line.strip():
                continue
            row = json.loads(line)
            mapped = map_rating(str(row.get("review_standardized", "")))
            record = {
                "dataset_id": "global_claims_factcheck",
                "source_url": row.get("factcheck_url", ""),
                "factcheck_date": row.get("factcheck_date", ""),
                "label_original": row.get("review_standardized", ""),
                "label_mapped": mapped,
                "claim_text": (row.get("claim_reviewed") or "").strip(),
                "claim_language": row.get("claim_language", ""),
                "items_reviewed": row.get("items_reviewed", ""),
                "topics": row.get("topics", {}),
                "twitter_presence": row.get("twitter_presence", ""),
                "train_eligible_for_fusion": False,
                "use_for": ["linguistic_pretraining", "multilingual_factcheck_metadata"],
            }
            if record["claim_text"]:
                counts[mapped] = counts.get(mapped, 0) + 1
                rows += 1
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {
        "dataset_id": "global_claims_factcheck",
        "output": str(out_path),
        "counts": counts,
        "rows": rows,
    }


def normalize_averitec(raw_dir: Path, out_dir: Path) -> dict | None:
    paths = [raw_dir / "averitec_train.json", raw_dir / "averitec_dev.json"]
    existing = [p for p in paths if p.exists()]
    if not existing:
        return None
    label_map = {
        "Supported": "resolved_true",
        "Refuted": "resolved_false",
        "Not Enough Evidence": "unclear",
        "Conflicting Evidence/Cherrypicking": "contested_or_partial",
    }
    out_path = out_dir / "averitec_claims.jsonl"
    counts: dict[str, int] = {}
    rows = 0
    with out_path.open("w", encoding="utf-8") as out:
        for path in existing:
            split = path.stem.replace("averitec_", "")
            data = json.loads(path.read_text(encoding="utf-8"))
            for idx, row in enumerate(data):
                original = row.get("label", "")
                mapped = label_map.get(original, "unclear")
                record = {
                    "dataset_id": "averitec",
                    "split": split,
                    "source_row_id": str(idx),
                    "label_original": original,
                    "label_mapped": mapped,
                    "claim_text": row.get("claim", ""),
                    "speaker": row.get("speaker") or "",
                    "claim_date": row.get("claim_date") or "",
                    "fact_checking_article": row.get("fact_checking_article") or "",
                    "reporting_source": row.get("reporting_source") or "",
                    "location_ISO_code": row.get("location_ISO_code") or "",
                    "claim_types": row.get("claim_types", []),
                    "question_count": len(row.get("questions", [])),
                    "train_eligible_for_fusion": False,
                    "use_for": ["claim_verification_pretraining", "evidence_retrieval"],
                }
                if record["claim_text"]:
                    counts[mapped] = counts.get(mapped, 0) + 1
                    rows += 1
                    out.write(json.dumps(record, ensure_ascii=False) + "\n")
    return {"dataset_id": "averitec", "output": str(out_path), "counts": counts, "rows": rows}


def main() -> int:
    parser = argparse.ArgumentParser(description="Normalize open text datasets.")
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()

    raw_dir = args.root / "raw" / "external" / "text_claims"
    out_dir = args.root / "processed" / "text_claims"
    out_dir.mkdir(parents=True, exist_ok=True)

    summaries = []
    liar_zip = raw_dir / "liar_ucsb.zip"
    if liar_zip.exists():
        summaries.append(normalize_liar(liar_zip, out_dir))
    fakenews_zip = raw_dir / "fakenewsnet_minimal.zip"
    if fakenews_zip.exists():
        summaries.append(normalize_fakenewsnet(fakenews_zip, out_dir))
    datacommons_json = raw_dir / "datacommons_factcheck.json"
    if datacommons_json.exists():
        summaries.append(normalize_datacommons(datacommons_json, out_dir))
    global_claims_jsonl = raw_dir / "global_claims_factcheck.json"
    if global_claims_jsonl.exists():
        summaries.append(normalize_global_claims(global_claims_jsonl, out_dir))
    averitec_summary = normalize_averitec(raw_dir, out_dir)
    if averitec_summary is not None:
        summaries.append(averitec_summary)

    summary_path = args.root / "manifests" / "open_text_datasets_counts.json"
    summary_path.write_text(json.dumps(summaries, indent=2), encoding="utf-8")
    print(json.dumps(summaries, indent=2))
    print(f"wrote {summary_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
