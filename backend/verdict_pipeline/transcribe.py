"""Transcription via faster-whisper with word-level timestamps."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from .config import WHISPER_COMPUTE_TYPE, WHISPER_DEVICE, WHISPER_MODEL
from .utils import get_logger

log = get_logger("transcribe")


@dataclass
class TranscriptResult:
    text: str
    word_count: int
    duration: float
    language: str = "en"
    segments: list[dict] = field(default_factory=list)
    quality: str = "real"  # "real" | "fallback"

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "word_count": self.word_count,
            "duration": self.duration,
            "language": self.language,
            "segments": self.segments,
            "quality": self.quality,
        }


_FALLBACK_TRANSCRIPTS: dict[str, str] = {
    "nixon_1973":     "I welcome this kind of examination because people have got to know whether or not their president is a crook. Well, I am not a crook. I have earned everything I have got.",
    "clinton_1998":   "I want to say one thing to the American people. I want you to listen to me. I'm going to say this again. I did not have sexual relations with that woman, Miss Lewinsky.",
    "armstrong_2005": "I have never doped. I can say it again, but I have never doped.",
    "holmes_2018":    "Our technology works, and the test results we have provided to patients are accurate.",
    "sbf_2022":       "FTX customer funds were never used by Alameda Research, and we managed everything appropriately.",
    "haugen_2021":    "Facebook's own research shows their products harm children, weaken democracy, and inflame ethnic violence. Internal documents prove it.",
}


def fallback_result(clip_id: str) -> TranscriptResult:
    text = _FALLBACK_TRANSCRIPTS.get(clip_id, "")
    return TranscriptResult(
        text=text,
        word_count=len([w for w in text.split() if w]),
        duration=0.0,
        language="en",
        segments=[],
        quality="fallback",
    )


def transcribe(
    audio_or_video_path: Path | str,
    *,
    clip_id: str = "default",
    model_name: Optional[str] = None,
) -> TranscriptResult:
    """Transcribe a media file. Returns ``fallback_result`` on failure."""
    try:
        from faster_whisper import WhisperModel  # type: ignore
    except Exception as exc:
        log.warning("faster-whisper unavailable for %s: %s", clip_id, exc)
        return fallback_result(clip_id)

    try:
        device = "cpu" if WHISPER_DEVICE == "auto" else WHISPER_DEVICE
        compute_type = "int8" if WHISPER_COMPUTE_TYPE == "auto" else WHISPER_COMPUTE_TYPE
        model = WhisperModel(model_name or WHISPER_MODEL, device=device, compute_type=compute_type)
        segments, info = model.transcribe(
            str(audio_or_video_path),
            beam_size=5,
            vad_filter=True,
            word_timestamps=True,
            language="en",
        )
        seg_list: list[dict] = []
        text_chunks: list[str] = []
        for seg in segments:
            seg_list.append({
                "start": float(seg.start),
                "end": float(seg.end),
                "text": seg.text.strip(),
            })
            text_chunks.append(seg.text.strip())
        text = " ".join(text_chunks).strip()
        if not text:
            return fallback_result(clip_id)
        return TranscriptResult(
            text=text,
            word_count=len([w for w in text.split() if w]),
            duration=float(getattr(info, "duration", 0.0) or 0.0),
            language=str(getattr(info, "language", "en") or "en"),
            segments=seg_list,
            quality="real",
        )
    except Exception as exc:
        log.warning("whisper transcription failed on %s: %s", clip_id, exc)
        return fallback_result(clip_id)
