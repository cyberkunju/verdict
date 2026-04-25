"""
research-data/scripts/prepare_deberta_data.py
================================================
Combine first-person + claim-style deception corpora into a unified JSONL for
DeBERTa-v3 fine-tuning. The point is that the existing TextPrior-v0 was trained
only on news-style fact-check claims (LIAR), which mismatches the first-person
testimonial style of the VERDICT archive (Snowden, Wigand, etc.). This pre-prep
mixes domains so the resulting classifier handles both.

Source corpora:

    Diplomacy (Peskov et al. 2020) -- Cornell Convokit ``diplomacy-corpus``
        utterances.jsonl. Labels from ``meta.speaker_intention``:
            "Lie"   -> 1 (deceptive)
            "Truth" -> 0 (truthful)

    LIAR-UCSB (Wang 2017, augmented with verifiability)
        ``M1-data/processed/text_claims/liar_ucsb_claims.jsonl``.
        Labels: ``label_mapped`` in {"resolved_false", "resolved_true"}.

    AVeriTeC (Schlichtkrull et al. 2023)
        ``M1-data/processed/text_claims/averitec_claims.jsonl``.

Output: ``research-data/processed/deberta_training_data.jsonl``
        ``research-data/processed/deberta_eval_data.jsonl``      (10% held out)

Each row: {"text": "...", "label": 0|1, "source": "diplomacy"|"liar"|"averitec"}
"""
from __future__ import annotations

import json
import random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIPLOMACY = ROOT / "research-data" / "raw" / "deception" / "diplomacy" / "diplomacy-corpus" / "utterances.jsonl"
LIAR = ROOT / "M1-data" / "processed" / "text_claims" / "liar_ucsb_claims.jsonl"
AVERITEC = ROOT / "M1-data" / "processed" / "text_claims" / "averitec_claims.jsonl"

OUT_DIR = ROOT / "research-data" / "processed"
OUT_TRAIN = OUT_DIR / "deberta_training_data.jsonl"
OUT_EVAL = OUT_DIR / "deberta_eval_data.jsonl"

MIN_LEN = 15           # chars; reject one-word noise
MAX_LEN = 800          # chars; clip extremely long utterances
EVAL_FRACTION = 0.10
SEED = 42


def load_diplomacy() -> list[dict]:
    rows: list[dict] = []
    if not DIPLOMACY.exists():
        print(f"[diplomacy] missing {DIPLOMACY}")
        return rows
    n_truth = n_lie = n_skip = 0
    with DIPLOMACY.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = (obj.get("text") or "").strip()
            if len(text) < MIN_LEN:
                n_skip += 1
                continue
            text = text[:MAX_LEN]
            intent = (obj.get("meta") or {}).get("speaker_intention")
            if intent == "Lie":
                rows.append({"text": text, "label": 1, "source": "diplomacy"})
                n_lie += 1
            elif intent == "Truth":
                rows.append({"text": text, "label": 0, "source": "diplomacy"})
                n_truth += 1
            else:
                n_skip += 1
    print(f"[diplomacy] kept {len(rows)} (truth={n_truth}, lie={n_lie}, skip={n_skip})")
    return rows


def load_liar() -> list[dict]:
    rows: list[dict] = []
    if not LIAR.exists():
        print(f"[liar] missing {LIAR}")
        return rows
    n_true = n_false = n_skip = 0
    with LIAR.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = (obj.get("claim_text") or "").strip()
            if len(text) < MIN_LEN:
                n_skip += 1
                continue
            text = text[:MAX_LEN]
            label_mapped = obj.get("label_mapped")
            if label_mapped == "resolved_false":
                rows.append({"text": text, "label": 1, "source": "liar"})
                n_false += 1
            elif label_mapped == "resolved_true":
                rows.append({"text": text, "label": 0, "source": "liar"})
                n_true += 1
            else:
                n_skip += 1
    print(f"[liar] kept {len(rows)} (true={n_true}, false={n_false}, skip={n_skip})")
    return rows


def load_averitec() -> list[dict]:
    rows: list[dict] = []
    if not AVERITEC.exists():
        print(f"[averitec] missing {AVERITEC}")
        return rows
    n_true = n_false = n_skip = 0
    with AVERITEC.open(encoding="utf-8", errors="replace") as fh:
        for line in fh:
            try:
                obj = json.loads(line)
            except Exception:
                continue
            text = (obj.get("claim_text") or obj.get("claim") or "").strip()
            if len(text) < MIN_LEN:
                n_skip += 1
                continue
            text = text[:MAX_LEN]
            label = obj.get("label_mapped") or obj.get("label")
            label_lower = (label or "").lower() if isinstance(label, str) else ""
            if "false" in label_lower or label_lower == "refuted":
                rows.append({"text": text, "label": 1, "source": "averitec"})
                n_false += 1
            elif "true" in label_lower or label_lower == "supported":
                rows.append({"text": text, "label": 0, "source": "averitec"})
                n_true += 1
            else:
                n_skip += 1
    print(f"[averitec] kept {len(rows)} (true={n_true}, false={n_false}, skip={n_skip})")
    return rows


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    random.seed(SEED)

    pool: list[dict] = []
    pool.extend(load_diplomacy())
    pool.extend(load_liar())
    pool.extend(load_averitec())

    if not pool:
        raise SystemExit("[fatal] no training data found")

    # Class balance check
    n_pos = sum(1 for r in pool if r["label"] == 1)
    n_neg = sum(1 for r in pool if r["label"] == 0)
    print(f"\n[total] {len(pool)} rows  (deceptive={n_pos}, truthful={n_neg})")
    print(f"[sources] {dict((s, sum(1 for r in pool if r['source']==s)) for s in {r['source'] for r in pool})}")

    # Down-sample the majority class so DeBERTa sees roughly balanced batches.
    if n_pos > n_neg:
        pos = [r for r in pool if r["label"] == 1]
        neg = [r for r in pool if r["label"] == 0]
        random.shuffle(pos)
        pool = pos[:n_neg] + neg
    elif n_neg > n_pos:
        pos = [r for r in pool if r["label"] == 1]
        neg = [r for r in pool if r["label"] == 0]
        random.shuffle(neg)
        pool = neg[:n_pos] + pos
    print(f"[balanced] {len(pool)} rows after class balancing")

    random.shuffle(pool)
    n_eval = max(int(EVAL_FRACTION * len(pool)), 100)
    eval_rows = pool[:n_eval]
    train_rows = pool[n_eval:]

    with OUT_TRAIN.open("w", encoding="utf-8") as fh:
        for r in train_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    with OUT_EVAL.open("w", encoding="utf-8") as fh:
        for r in eval_rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    print(f"\n[saved] train -> {OUT_TRAIN} ({len(train_rows)} rows, "
          f"{OUT_TRAIN.stat().st_size / 1024 / 1024:.2f} MB)")
    print(f"[saved] eval  -> {OUT_EVAL} ({len(eval_rows)} rows, "
          f"{OUT_EVAL.stat().st_size / 1024 / 1024:.2f} MB)")


if __name__ == "__main__":
    main()
