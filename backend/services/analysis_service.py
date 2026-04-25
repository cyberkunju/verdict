"""Reusable analyzer orchestration for live inputs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from verdict_pipeline import extract_facial, extract_rppg, extract_voice, linguistic, score, transcribe
from verdict_pipeline.schema import ClipReport, ClipScores, ClipSignals, SignalQuality

from services.similarity_service import top_similar_from_archive


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "Unlabeled public statement"
    sentence = cleaned.split(".")[0].strip()
    return sentence[:180] if sentence else cleaned[:180]


def _build_report(
    *,
    subject: str,
    statement: str,
    signals: dict[str, Any],
    scores: dict[str, int],
    signal_quality: dict[str, str],
    similar_matches: list[dict],
) -> dict[str, str]:
    behavioral_summary = (
        f"{subject}'s segment shows a heart-rate shift from {signals['hr_baseline_bpm']} to "
        f"{signals['hr_peak_bpm']} bpm (Δ {signals['hr_delta_bpm']}), with voice F0 moving from "
        f"{signals['f0_baseline_hz']} to {signals['f0_peak_hz']} Hz (Δ {signals['f0_delta_hz']}). "
        f"AU15 peaked at {signals['au15_max_intensity']:.2f}, AU14 at {signals['au14_max_intensity']:.2f}, "
        f"and hedging markers appeared {signals['hedging_count']} time(s). Composite scores are deception "
        f"{scores['deception']}, sincerity {scores['sincerity']}, stress {scores['stress']}, confidence {scores['confidence']}."
    )
    if similar_matches:
        neighbors = ", ".join(
            f"{item['subject']} ({item['clip_id']}, sim {item['similarity']:.2f})" for item in similar_matches
        )
        comparative_profile = (
            f"Nearest archive neighbors for “{statement}” are {neighbors}. The current profile sits closest to those "
            f"archive score vectors rather than as an isolated outlier. Use those historical cases as calibration context, not proof."
        )
    else:
        comparative_profile = (
            "No archive neighbors were available for comparison. Treat this run as a standalone physiological and linguistic profile, "
            "not a historical classification."
        )
    qualifications = (
        "This is not a truth determination. Physiological arousal can reflect stress, fear, anger, fatigue, rehearsal, or other causes. "
        f"Signal quality flags: rppg={signal_quality['rppg']}, facial_au={signal_quality['facial_au']}, "
        f"voice={signal_quality['voice']}, transcript={signal_quality['transcript']}."
    )
    report = ClipReport(
        behavioral_summary=behavioral_summary,
        comparative_profile=comparative_profile,
        qualifications=qualifications,
    )
    return report.model_dump(mode="json")


def analyze_video(
    *,
    video_path: Path,
    source_url: str = "",
    start_seconds: float | None = None,
    end_seconds: float | None = None,
    subject: str | None = None,
    statement: str | None = None,
    context: str | None = None,
    year: int | None = None,
) -> dict[str, Any]:
    tr = transcribe.transcribe(video_path, clip_id="default")
    lf = linguistic.extract(tr.text)
    vf = extract_voice.extract(video_path, clip_id="default", transcript=tr.text, word_count=lf.word_count)
    ff = extract_facial.extract(video_path, clip_id="default")
    rp = extract_rppg.extract(video_path, clip_id="default")

    cs = score.compute_scores(
        hr_baseline=rp.hr_baseline_bpm,
        hr_peak=rp.hr_peak_bpm,
        hr_delta=rp.hr_delta_bpm,
        hrv_rmssd=rp.hrv_rmssd_ms,
        au15_max=ff.au15_max_intensity,
        au14_max=ff.au14_max_intensity,
        au6_present=ff.au6_present,
        au24_max=ff.au24_max_intensity,
        f0_baseline=vf.f0_baseline_hz,
        f0_peak=vf.f0_peak_hz,
        f0_delta=vf.f0_delta_hz,
        jitter_percent=vf.jitter_percent,
        shimmer_db=vf.shimmer_db,
        speech_rate_wpm=vf.speech_rate_wpm,
        hedging_count=lf.hedging_count,
        pronoun_drop_rate=lf.pronoun_drop_rate,
        word_count=lf.word_count,
        certainty_count=lf.certainty_count,
        specificity_score=lf.specificity_score,
        affect_negative=lf.affect_negative,
        rppg_timeline=[{"t": s.t, "hr": s.hr} for s in rp.timeline],
    )

    signal_quality = SignalQuality(
        rppg=rp.quality,
        facial_au=ff.quality,
        voice=vf.quality,
        transcript=tr.quality,
    ).model_dump(mode="json")

    scores_payload = ClipScores(
        deception=cs.deception,
        sincerity=cs.sincerity,
        stress=cs.stress,
        confidence=cs.confidence,
    ).model_dump(mode="json")

    similar = top_similar_from_archive(scores_payload, limit=3)
    subject_name = subject or "Submitted speaker"
    statement_text = statement or _first_sentence(tr.text)
    context_text = context or "User-submitted public video segment"

    signals_payload = ClipSignals(
        hr_baseline_bpm=rp.hr_baseline_bpm,
        hr_peak_bpm=rp.hr_peak_bpm,
        hr_delta_bpm=rp.hr_delta_bpm,
        hrv_rmssd_ms=rp.hrv_rmssd_ms,
        au15_max_intensity=ff.au15_max_intensity,
        au14_max_intensity=ff.au14_max_intensity,
        au6_present=ff.au6_present,
        au24_max_intensity=ff.au24_max_intensity,
        f0_baseline_hz=vf.f0_baseline_hz,
        f0_peak_hz=vf.f0_peak_hz,
        f0_delta_hz=vf.f0_delta_hz,
        jitter_percent=vf.jitter_percent,
        shimmer_db=vf.shimmer_db,
        speech_rate_wpm=vf.speech_rate_wpm,
        hedging_count=lf.hedging_count,
        pronoun_drop_rate=lf.pronoun_drop_rate,
        transcript=tr.text,
        timeline=[
            {"t": p.t, "hr": p.hr, "f0": p.f0, "au15": p.au15, "deception": p.deception}
            for p in cs.timeline
        ],
    ).model_dump(mode="json")

    report_payload = _build_report(
        subject=subject_name,
        statement=statement_text,
        signals=signals_payload,
        scores=scores_payload,
        signal_quality=signal_quality,
        similar_matches=similar,
    )

    return {
        "subject": subject_name,
        "statement": statement_text,
        "year": year,
        "context": context_text,
        "video_url": source_url,
        "video_start_seconds": float(start_seconds or 0.0),
        "video_end_seconds": float(end_seconds or 0.0),
        "thumbnail_url": "",
        "signals": signals_payload,
        "scores": scores_payload,
        "llm_report": report_payload,
        "signal_quality": signal_quality,
        "similar_archive_matches": similar,
    }
