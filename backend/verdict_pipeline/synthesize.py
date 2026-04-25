"""LLM analyst synthesis using OpenAI structured outputs.

Produces the three-section report locked in CONTRACT.md §2:
``behavioral_summary``, ``comparative_profile``, ``qualifications``.

Hard rules baked into the prompt:
  - Never says "lying", "guilty", "dishonest", "proved".
  - Cites concrete numbers (HR delta, F0 delta, AU intensities, hedging).
  - Includes signal-quality caveat.
  - For ``ground_truth = "sincere"`` clips, frames the analysis as a
    sincerity counter-example (whistleblower mode).
"""

from __future__ import annotations

import json
from typing import Any, Optional

from pydantic import BaseModel

from .config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY
from .utils import get_logger

log = get_logger("synthesize")


class AnalystReport(BaseModel):
    behavioral_summary: str
    comparative_profile: str
    qualifications: str


SYSTEM_PROMPT = """\
You are VERDICT, a cautious physiological signal analyst for public-interest
journalism. You do not determine truth. You only summarize measured
physiological, facial, vocal, and linguistic signals against historical
reference cases.

Hard rules:
- NEVER say: "lying", "guilty", "dishonest", "proved", "proves they lied".
- PREFER: "signal consistent with", "pattern similar to", "elevated relative
  to baseline", "this is not a truth determination".
- ALWAYS cite concrete numbers (HR delta, F0 delta, AU intensities, hedging).
- ALWAYS include a signal-quality caveat in the qualifications section.
- For ``ground_truth = "sincere"`` cases, frame the analysis as a sincerity
  counter-example: high stress can co-exist with high sincerity in
  whistleblower testimony.

Output exactly three sections as JSON keys:
1. behavioral_summary  -> 3-5 sentences with concrete numbers.
2. comparative_profile -> 2-3 sentences referencing similar archive entries.
3. qualifications      -> 2-3 sentences. Always include: physiological
   arousal can reflect stress, fear, anger, fatigue, or other causes. Always
   include the signal-quality flags.
"""


USER_TEMPLATE = """\
Clip: {clip_id} ({year}) — {subject}
Statement: "{statement}"
Context: {context}
Ground truth on public record: {ground_truth} ({ground_truth_source})

Signals (CONTRACT.md units):
- HR baseline: {hr_baseline_bpm} bpm | peak: {hr_peak_bpm} bpm | delta: {hr_delta_bpm} bpm
- HRV RMSSD: {hrv_rmssd_ms} ms
- AU15 max: {au15_max_intensity} | AU14 max: {au14_max_intensity} | AU24 max: {au24_max_intensity} | AU6 present: {au6_present}
- F0 baseline: {f0_baseline_hz} Hz | peak: {f0_peak_hz} Hz | delta: {f0_delta_hz} Hz
- Jitter: {jitter_percent}% | Shimmer: {shimmer_db} dB | Speech rate: {speech_rate_wpm} wpm
- Hedging count: {hedging_count} | Pronoun drop rate: {pronoun_drop_rate:.2f}

Composite scores: deception={deception} sincerity={sincerity} stress={stress} confidence={confidence}
Cross-signal synchrony: {synchrony:.2f}
Signal quality: rppg={rppg} facial_au={facial_au} voice={voice} transcript={transcript}

Similar historical entries in archive: {similar_clips}

Produce the three-section report now.
"""


def synthesize(
    *,
    clip_meta: dict[str, Any],
    signals: dict[str, Any],
    scores: dict[str, Any],
    signal_quality: dict[str, str],
    synchrony: float,
    similar_clips: list[str],
) -> AnalystReport:
    """Generate an analyst report. Falls back to a templated draft on failure."""
    user_msg = USER_TEMPLATE.format(
        clip_id=clip_meta["clip_id"],
        year=clip_meta["year"],
        subject=clip_meta["subject"],
        statement=clip_meta["statement"],
        context=clip_meta["context"],
        ground_truth=clip_meta["ground_truth"],
        ground_truth_source=clip_meta["ground_truth_source"],
        hr_baseline_bpm=signals.get("hr_baseline_bpm", 0),
        hr_peak_bpm=signals.get("hr_peak_bpm", 0),
        hr_delta_bpm=signals.get("hr_delta_bpm", 0),
        hrv_rmssd_ms=signals.get("hrv_rmssd_ms", 0),
        au15_max_intensity=signals.get("au15_max_intensity", 0),
        au14_max_intensity=signals.get("au14_max_intensity", 0),
        au24_max_intensity=signals.get("au24_max_intensity", 0),
        au6_present=signals.get("au6_present", False),
        f0_baseline_hz=signals.get("f0_baseline_hz", 0),
        f0_peak_hz=signals.get("f0_peak_hz", 0),
        f0_delta_hz=signals.get("f0_delta_hz", 0),
        jitter_percent=signals.get("jitter_percent", 0),
        shimmer_db=signals.get("shimmer_db", 0),
        speech_rate_wpm=signals.get("speech_rate_wpm", 0),
        hedging_count=signals.get("hedging_count", 0),
        pronoun_drop_rate=signals.get("pronoun_drop_rate", 0.0),
        deception=scores.get("deception", 0),
        sincerity=scores.get("sincerity", 0),
        stress=scores.get("stress", 0),
        confidence=scores.get("confidence", 0),
        synchrony=synchrony,
        rppg=signal_quality.get("rppg", "real"),
        facial_au=signal_quality.get("facial_au", "real"),
        voice=signal_quality.get("voice", "real"),
        transcript=signal_quality.get("transcript", "real"),
        similar_clips=", ".join(similar_clips) if similar_clips else "(none)",
    )

    if OPENAI_API_KEY:
        try:
            return _call_openai(user_msg)
        except Exception as exc:
            log.warning("OpenAI call failed: %s", exc)

    return _template_fallback(clip_meta, signals, scores)


def _call_openai(user_msg: str) -> AnalystReport:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        temperature=LLM_TEMPERATURE,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    return AnalystReport.model_validate(data)


def _template_fallback(
    clip_meta: dict[str, Any],
    signals: dict[str, Any],
    scores: dict[str, Any],
) -> AnalystReport:
    """Deterministic templated report used when OPENAI_API_KEY is missing."""
    is_sincere = clip_meta.get("ground_truth") == "sincere"
    name = clip_meta.get("subject", "Subject")
    hr_d = signals.get("hr_delta_bpm", 0)
    f0_d = signals.get("f0_delta_hz", 0)
    au15 = signals.get("au15_max_intensity", 0)
    hedging = signals.get("hedging_count", 0)

    if is_sincere:
        summary = (
            f"{name}'s testimony shows a heart-rate delta of {hr_d} bpm and an F0 "
            f"delta of {f0_d} Hz consistent with elevated arousal under public "
            f"scrutiny. AU6 (Duchenne) was detected; AU15 lip-suppression peaked "
            f"at {au15:.1f}, well below the typical denial range. Hedging language "
            f"was minimal ({hedging}). The signal pattern is consistent with "
            f"high-conviction whistleblower testimony."
        )
        comparative = (
            "Across the archive, this profile is structurally distinct from "
            "deceptive denials: arousal is high, but sincerity markers (AU6, "
            "specificity, low hedging) co-occur. Treat this as a sincerity "
            "counter-example rather than a deception case."
        )
    else:
        summary = (
            f"{name}'s denial shows a heart-rate delta of {hr_d} bpm and an F0 "
            f"delta of {f0_d} Hz, both elevated relative to a neutral baseline. "
            f"AU15 lip-suppression peaked at {au15:.1f}; hedging language "
            f"appeared {hedging} time(s) in the {signals.get('speech_rate_wpm', 0):.0f} "
            f"wpm utterance. The composite pattern is consistent with patterns "
            f"observed in historically resolved false denials."
        )
        comparative = (
            "Among archive entries with confirmed false-denial outcomes, this "
            "clip's deception score sits in the upper range. The pattern "
            "resembles cases later resolved against the speaker on the public "
            "record."
        )
    qualifications = (
        "This is not a truth determination. Physiological arousal can reflect "
        "stress, fear, anger, fatigue, or other causes. Some signals on this "
        "clip were extracted using fallback estimators where the source video "
        "did not permit clean rPPG / AU extraction; treat the report as a "
        "research-grade prototype, not a forensic verdict."
    )
    return AnalystReport(
        behavioral_summary=summary,
        comparative_profile=comparative,
        qualifications=qualifications,
    )
