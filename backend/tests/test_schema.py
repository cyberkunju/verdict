import pytest

from verdict_pipeline.schema import validate_clip


def _payload() -> dict:
    return {
        "schema_version": "1.0",
        "clip_id": "sample_2026",
        "subject": "Sample Speaker",
        "statement": "This is a sample statement.",
        "year": 2026,
        "context": "Synthetic test payload",
        "ground_truth": "true",
        "ground_truth_source": "Synthetic test",
        "video_url": "https://example.com/video.mp4",
        "video_start_seconds": 0.0,
        "video_end_seconds": 12.0,
        "thumbnail_url": "data/thumbnails/sample_2026.jpg",
        "signals": {
            "hr_baseline_bpm": 72.0,
            "hr_peak_bpm": 88.0,
            "hr_delta_bpm": 16.0,
            "hrv_rmssd_ms": 21.0,
            "au15_max_intensity": 1.8,
            "au14_max_intensity": 1.1,
            "au6_present": False,
            "au24_max_intensity": 1.6,
            "f0_baseline_hz": 120.0,
            "f0_peak_hz": 137.0,
            "f0_delta_hz": 17.0,
            "jitter_percent": 1.5,
            "shimmer_db": 1.2,
            "speech_rate_wpm": 125.0,
            "hedging_count": 2,
            "pronoun_drop_rate": 0.2,
            "transcript": "Synthetic transcript.",
            "timeline": [
                {"t": float(i), "hr": 72.0 + i, "f0": 120.0 + i, "au15": 0.5 + i * 0.1, "deception": 40.0 + i}
                for i in range(10)
            ],
        },
        "scores": {
            "deception": 61,
            "sincerity": 36,
            "stress": 58,
            "confidence": 49,
        },
        "llm_report": {
            "behavioral_summary": "Synthetic behavioral summary for test coverage.",
            "comparative_profile": "Synthetic comparative profile for test coverage.",
            "qualifications": "Synthetic qualifications for test coverage.",
        },
        "similar_clips": ["other_2026", "third_2026"],
        "signal_quality": {
            "rppg": "real",
            "facial_au": "fallback",
            "voice": "real",
            "transcript": "manual",
        },
    }


def test_validate_clip_accepts_valid_payload() -> None:
    clip = validate_clip(_payload())
    assert clip.clip_id == "sample_2026"


def test_validate_clip_rejects_invalid_window() -> None:
    bad = _payload()
    bad["video_end_seconds"] = 0.0
    with pytest.raises(Exception):
        validate_clip(bad)
