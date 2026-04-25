"""Reusable analyzer orchestration for live inputs."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Callable

from verdict_pipeline import extract_facial, extract_rppg, extract_voice, linguistic, score, transcribe
from verdict_pipeline.config import LLM_MODEL, LLM_TEMPERATURE, OPENAI_API_KEY
from verdict_pipeline.schema import ClipReport, ClipScores, ClipSignals, SignalQuality
from verdict_pipeline.utils import get_logger

from services.similarity_service import top_similar_from_archive
from services.text_prior_service import score_transcript

log = get_logger("analysis_service")

ProgressCb = Callable[[str], None]

CLAIM_PATTERNS = (
    "did not",
    "didn't",
    "never",
    "not",
    "no",
    "i am",
    "i'm",
    "we",
    "truth",
    "fraud",
    "crook",
    "innocent",
    "accurate",
    "worked",
    "works",
)


def _first_sentence(text: str) -> str:
    cleaned = " ".join(text.split())
    if not cleaned:
        return "Unlabeled public statement"
    sentence = cleaned.split(".")[0].strip()
    return sentence[:220] if sentence else cleaned[:220]


def _sentence_candidates(transcript_text: str, segments: list[dict[str, Any]]) -> list[str]:
    candidates: list[str] = []
    if segments:
        for segment in segments:
            txt = str(segment.get("text", "")).strip()
            if txt:
                candidates.append(" ".join(txt.split()))

    if not candidates:
        chunks = [part.strip() for part in re.split(r"[.!?]+", transcript_text) if part.strip()]
        candidates.extend(chunks)

    seen: set[str] = set()
    deduped: list[str] = []
    for sentence in candidates:
        if sentence in seen:
            continue
        seen.add(sentence)
        deduped.append(sentence)
    return deduped


def _statement_importance(sentence: str) -> float:
    lower = sentence.lower()
    words = re.findall(r"[a-zA-Z']+", lower)
    wc = len(words)
    if wc == 0:
        return 0.0

    density = min(wc / 24.0, 1.0)
    claim_hits = sum(1 for token in CLAIM_PATTERNS if token in lower)
    has_first_person = 1.0 if re.search(r"\b(i|we|my|our|me|us)\b", lower) else 0.0
    has_number_or_name = 1.0 if re.search(r"\d|\b[A-Z][a-z]+\b", sentence) else 0.0
    too_short_penalty = 0.6 if wc < 6 else 0.0

    return (density * 1.2) + (claim_hits * 0.7) + (has_first_person * 0.6) + (has_number_or_name * 0.3) - too_short_penalty


def _select_key_statement(transcript_text: str, segments: list[dict[str, Any]], requested_statement: str | None) -> str:
    if requested_statement and requested_statement.strip():
        return " ".join(requested_statement.split())[:260]

    candidates = _sentence_candidates(transcript_text, segments)
    if not candidates:
        return _first_sentence(transcript_text)

    picked = max(candidates, key=_statement_importance)
    return picked[:260]


def _text_prior_inference(selected_statement: str, transcript_text: str) -> dict[str, Any]:
    prob: float | None = None
    source = "selected_statement"

    try:
        prob = score_transcript(selected_statement)
    except Exception as exc:  # pragma: no cover
        log.warning("text prior score failed on selected statement: %s", exc)

    if prob is None and transcript_text.strip():
        source = "full_transcript_fallback"
        try:
            prob = score_transcript(transcript_text.strip()[:700])
        except Exception as exc:  # pragma: no cover
            log.warning("text prior score failed on transcript fallback: %s", exc)

    if prob is None:
        return {
            "model_name": "VerdictTextPrior-v1",
            "statement_used": selected_statement,
            "statement_source": source,
            "probability_resolved_false": None,
            "label": "unavailable",
            "confidence": None,
        }

    p = max(0.0, min(1.0, float(prob)))
    if p >= 0.62:
        label = "likely_false"
    elif p <= 0.38:
        label = "likely_true"
    else:
        label = "uncertain"
    confidence = int(round(min(1.0, abs(p - 0.5) * 2.0) * 100))
    return {
        "model_name": "VerdictTextPrior-v1",
        "statement_used": selected_statement,
        "statement_source": source,
        "probability_resolved_false": round(p, 4),
        "label": label,
        "confidence": confidence,
    }


def _build_report(
    *,
    subject: str,
    statement: str,
    signals: dict[str, Any],
    scores: dict[str, int],
    signal_quality: dict[str, str],
    similar_matches: list[dict],
    text_prior: dict[str, Any],
) -> dict[str, str]:
    model_line = ""
    if text_prior.get("probability_resolved_false") is not None:
        model_line = (
            f" Text-prior model VerdictTextPrior-v1 on selected statement “{statement}” gives "
            f"P(resolved_false)={text_prior['probability_resolved_false']:.2f} ({text_prior['label']})."
        )
    behavioral_summary = (
        f"{subject}'s segment shows a heart-rate shift from {signals['hr_baseline_bpm']} to "
        f"{signals['hr_peak_bpm']} bpm (Δ {signals['hr_delta_bpm']}), with voice F0 moving from "
        f"{signals['f0_baseline_hz']} to {signals['f0_peak_hz']} Hz (Δ {signals['f0_delta_hz']}). "
        f"AU15 peaked at {signals['au15_max_intensity']:.2f}, AU14 at {signals['au14_max_intensity']:.2f}, "
        f"and hedging markers appeared {signals['hedging_count']} time(s). Composite scores are deception "
        f"{scores['deception']}, sincerity {scores['sincerity']}, stress {scores['stress']}, confidence {scores['confidence']}.{model_line}"
    )
    if similar_matches:
        neighbors = ", ".join(
            f"{item['subject']} ({item['clip_id']}, sim {item['similarity']:.2f})" for item in similar_matches
        )
        comparative_profile = (
            f"Nearest archive neighbors for “{statement}” are {neighbors}. The current profile sits closest to those "
            "archive score vectors rather than as an isolated outlier. Use those historical cases as calibration context, not proof."
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


def _build_report_with_openai(
    *,
    subject: str,
    statement: str,
    context: str,
    signals: dict[str, Any],
    scores: dict[str, int],
    signal_quality: dict[str, str],
    similar_matches: list[dict],
    text_prior: dict[str, Any],
) -> dict[str, str] | None:
    if not OPENAI_API_KEY:
        return None
    try:
        from openai import OpenAI

        system_prompt = (
            "You are VERDICT, a cautious physiological signal analyst. "
            "Output strict JSON with keys behavioral_summary, comparative_profile, qualifications. "
            "Never claim absolute truth. Use measured numbers and include caveats."
        )
        user_prompt = (
            f"Subject: {subject}\n"
            f"Statement: {statement}\n"
            f"Context: {context}\n"
            f"TextPrior: {json.dumps(text_prior)}\n"
            f"Signals: {json.dumps(signals)}\n"
            f"Scores: {json.dumps(scores)}\n"
            f"SignalQuality: {json.dumps(signal_quality)}\n"
            f"SimilarMatches: {json.dumps(similar_matches)}\n"
            "Write concise high-signal analysis in 3 sections."
        )

        client = OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=LLM_MODEL,
            temperature=LLM_TEMPERATURE,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        raw = resp.choices[0].message.content or "{}"
        data = json.loads(raw)
        report = ClipReport.model_validate(data)
        return report.model_dump(mode="json")
    except Exception as exc:  # pragma: no cover
        log.warning("OpenAI summary failed, using template fallback: %s", exc)
        return None


def _emit(progress: ProgressCb | None, phase: str) -> None:
    if progress:
        progress(phase)


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
    progress: ProgressCb | None = None,
) -> dict[str, Any]:
    _emit(progress, "transcribing")
    tr = transcribe.transcribe(video_path, clip_id="default")
    selected_statement = _select_key_statement(tr.text, tr.segments, statement)
    _emit(progress, "extracting_text")
    lf = linguistic.extract(tr.text, include_text_prior=False)
    text_prior = _text_prior_inference(selected_statement, tr.text)

    _emit(progress, "extracting_voice")
    vf = extract_voice.extract(video_path, clip_id="default", transcript=tr.text, word_count=lf.word_count)
    _emit(progress, "extracting_facial")
    ff = extract_facial.extract(video_path, clip_id="default")
    _emit(progress, "extracting_rppg")
    rp = extract_rppg.extract(video_path, clip_id="default")

    _emit(progress, "scoring")
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
        text_deception_prior=text_prior["probability_resolved_false"],
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
    statement_text = selected_statement
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

    _emit(progress, "synthesizing")
    report_payload = _build_report_with_openai(
        subject=subject_name,
        statement=statement_text,
        context=context_text,
        signals=signals_payload,
        scores=scores_payload,
        signal_quality=signal_quality,
        similar_matches=similar,
        text_prior=text_prior,
    )
    if report_payload is None:
        report_payload = _build_report(
        subject=subject_name,
        statement=statement_text,
        signals=signals_payload,
        scores=scores_payload,
        signal_quality=signal_quality,
        similar_matches=similar,
        text_prior=text_prior,
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
        "text_prior": text_prior,
    }
