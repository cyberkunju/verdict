"""Pipeline orchestrator: runs every layer end-to-end for one or all clips."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from . import SCHEMA_VERSION, clips as clip_registry
from . import extract_facial, extract_rppg, extract_voice, linguistic, score, synthesize, transcribe
from .config import PROCESSED_DIR, RAW_CLIPS_DIR, ensure_dirs
from .schema import Clip, validate_clip
from .utils import Timer, get_logger, setup_logging, write_json

log = get_logger("batch")


def process_clip(clip_id: str, *, video_path: Path | None = None) -> dict[str, Any]:
    """Run the full pipeline on one clip and return the validated payload dict."""
    meta = clip_registry.get_clip(clip_id)
    video_path = video_path or (RAW_CLIPS_DIR / f"{clip_id}.mp4")
    has_video = video_path.exists()
    if not has_video:
        log.warning("[yellow]video missing[/] %s — using fallbacks for all signal layers", video_path)

    # ---- Transcribe (drives word_count for voice + linguistic) ----
    with Timer("transcribe") as t_tr:
        tr = (
            transcribe.transcribe(video_path, clip_id=clip_id)
            if has_video
            else transcribe.fallback_result(clip_id)
        )
    log.info("transcribe %s [%s] %.2fs", clip_id, tr.quality, t_tr.elapsed)

    # ---- Linguistic ----
    with Timer("linguistic") as t_ln:
        lf = linguistic.extract(tr.text)
    log.info("linguistic %s [%s] %.2fs", clip_id, lf.quality, t_ln.elapsed)

    # ---- Voice ----
    with Timer("voice") as t_vc:
        vf = (
            extract_voice.extract(
                video_path, clip_id=clip_id, transcript=tr.text, word_count=lf.word_count
            )
            if has_video
            else extract_voice.fallback_features(clip_id, transcript=tr.text)
        )
    log.info("voice %s [%s] %.2fs", clip_id, vf.quality, t_vc.elapsed)

    # ---- Facial ----
    with Timer("facial") as t_fa:
        ff = (
            extract_facial.extract(video_path, clip_id=clip_id)
            if has_video
            else extract_facial.fallback_features(clip_id)
        )
    log.info("facial %s [%s] %.2fs", clip_id, ff.quality, t_fa.elapsed)

    # ---- rPPG ----
    with Timer("rppg") as t_rp:
        rp = (
            extract_rppg.extract(video_path, clip_id=clip_id)
            if has_video
            else extract_rppg.fallback_features(clip_id, duration=meta.duration or 12.0)
        )
    log.info("rppg %s [%s] %.2fs SNR=%.1fdB", clip_id, rp.quality, t_rp.elapsed, rp.snr_db)

    # ---- Score ----
    rppg_timeline_dicts = [{"t": s.t, "hr": s.hr} for s in rp.timeline]
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
        rppg_timeline=rppg_timeline_dicts,
    )

    signal_quality = {
        "rppg": rp.quality,
        "facial_au": ff.quality,
        "voice": vf.quality,
        "transcript": tr.quality,
    }

    # ---- LLM analyst ----
    with Timer("synthesize") as t_sy:
        report = synthesize.synthesize(
            clip_meta={
                "clip_id": meta.clip_id,
                "year": meta.year,
                "subject": meta.subject,
                "statement": meta.statement,
                "context": meta.context,
                "ground_truth": meta.ground_truth,
                "ground_truth_source": meta.ground_truth_source,
            },
            signals={
                "hr_baseline_bpm": rp.hr_baseline_bpm,
                "hr_peak_bpm": rp.hr_peak_bpm,
                "hr_delta_bpm": rp.hr_delta_bpm,
                "hrv_rmssd_ms": rp.hrv_rmssd_ms,
                "au15_max_intensity": ff.au15_max_intensity,
                "au14_max_intensity": ff.au14_max_intensity,
                "au6_present": ff.au6_present,
                "au24_max_intensity": ff.au24_max_intensity,
                "f0_baseline_hz": vf.f0_baseline_hz,
                "f0_peak_hz": vf.f0_peak_hz,
                "f0_delta_hz": vf.f0_delta_hz,
                "jitter_percent": vf.jitter_percent,
                "shimmer_db": vf.shimmer_db,
                "speech_rate_wpm": vf.speech_rate_wpm,
                "hedging_count": lf.hedging_count,
                "pronoun_drop_rate": lf.pronoun_drop_rate,
            },
            scores={
                "deception": cs.deception,
                "sincerity": cs.sincerity,
                "stress": cs.stress,
                "confidence": cs.confidence,
            },
            signal_quality=signal_quality,
            synchrony=cs.synchrony,
            similar_clips=list(meta.similar_clips),
        )
    log.info("synthesize %s %.2fs", clip_id, t_sy.elapsed)

    # ---- Assemble Clip payload ----
    payload = {
        "schema_version": SCHEMA_VERSION,
        "clip_id": meta.clip_id,
        "subject": meta.subject,
        "statement": meta.statement,
        "year": meta.year,
        "context": meta.context,
        "ground_truth": meta.ground_truth,
        "ground_truth_source": meta.ground_truth_source,
        "video_url": meta.video_url or "",
        "video_start_seconds": meta.video_start_seconds,
        "video_end_seconds": meta.video_end_seconds or (meta.video_start_seconds + 12.0),
        "thumbnail_url": meta.thumbnail_url,
        "signals": {
            "hr_baseline_bpm": rp.hr_baseline_bpm,
            "hr_peak_bpm": rp.hr_peak_bpm,
            "hr_delta_bpm": rp.hr_delta_bpm,
            "hrv_rmssd_ms": rp.hrv_rmssd_ms,
            "au15_max_intensity": ff.au15_max_intensity,
            "au14_max_intensity": ff.au14_max_intensity,
            "au6_present": ff.au6_present,
            "au24_max_intensity": ff.au24_max_intensity,
            "f0_baseline_hz": vf.f0_baseline_hz,
            "f0_peak_hz": vf.f0_peak_hz,
            "f0_delta_hz": vf.f0_delta_hz,
            "jitter_percent": vf.jitter_percent,
            "shimmer_db": vf.shimmer_db,
            "speech_rate_wpm": vf.speech_rate_wpm,
            "hedging_count": lf.hedging_count,
            "pronoun_drop_rate": lf.pronoun_drop_rate,
            "transcript": tr.text,
            "timeline": [
                {"t": p.t, "hr": p.hr, "f0": p.f0, "au15": p.au15, "deception": p.deception}
                for p in cs.timeline
            ],
        },
        "scores": {
            "deception": cs.deception,
            "sincerity": cs.sincerity,
            "stress": cs.stress,
            "confidence": cs.confidence,
        },
        "llm_report": report.model_dump(),
        "similar_clips": list(meta.similar_clips),
        "signal_quality": signal_quality,
    }

    validate_clip(payload)
    return payload


def write_outputs(payloads: list[dict]) -> None:
    """Write per-clip JSONs and the combined ``all_clips.json`` handoff."""
    ensure_dirs()
    for p in payloads:
        out = PROCESSED_DIR / f"{p['clip_id']}.json"
        write_json(out, p)
        log.info("wrote %s", out)
    all_path = PROCESSED_DIR / "all_clips.json"
    write_json(all_path, payloads)
    log.info("[bold green]wrote handoff[/] %s (%d clips)", all_path, len(payloads))


def main(argv: list[str] | None = None) -> int:
    setup_logging()
    p = argparse.ArgumentParser(description="Run VERDICT pipeline on all clips.")
    p.add_argument("--only", nargs="*", default=None, help="Limit to these clip_ids.")
    args = p.parse_args(argv)

    targets = args.only or clip_registry.all_clip_ids()
    payloads: list[dict] = []
    for cid in targets:
        try:
            log.info("=" * 12 + f" {cid} " + "=" * 12)
            payloads.append(process_clip(cid))
        except Exception as exc:
            log.exception("failed clip %s: %s", cid, exc)
    write_outputs(payloads)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
