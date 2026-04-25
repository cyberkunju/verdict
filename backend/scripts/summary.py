"""One-shot summary of all_clips.json — for human eyeballing the run output."""
from __future__ import annotations

import json
from pathlib import Path

from verdict_pipeline.config import PROCESSED_DIR


def main() -> int:
    path = PROCESSED_DIR / "all_clips.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    print(f"\n{len(data)} clips at {path}\n")
    for c in data:
        sq = c["signal_quality"]
        s = c["scores"]
        sig = c["signals"]
        print(
            f"  {c['clip_id']:18}  "
            f"hr={sig['hr_baseline_bpm']:>5.1f}->{sig['hr_peak_bpm']:>5.1f}  "
            f"d={sig['hr_delta_bpm']:>4.1f}  "
            f"f0={sig['f0_baseline_hz']:>5.0f}->{sig['f0_peak_hz']:>5.0f}  "
            f"rppg={sq['rppg']:>8} face={sq['facial_au']:>8} voice={sq['voice']:>4} tr={sq['transcript']:>4}"
        )
        print(
            f"  {'':18}  scores: dec={s['deception']:>3}  sin={s['sincerity']:>3}  "
            f"str={s['stress']:>3}  con={s['confidence']:>3}   "
            f"timeline={len(sig['timeline'])} pts"
        )
        tr = sig["transcript"][:110].replace("\n", " ")
        print(f"  {'':18}  transcript: {tr!r}")
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
