"""Derived calibration metrics from processed archive clips."""

from __future__ import annotations

from services.archive_service import load_archive_clips

LABELS = ["true", "false", "sincere"]


def predict_label(clip: dict) -> str:
    scores = clip["scores"]
    if scores["sincerity"] >= max(scores["deception"], 60):
        return "sincere"
    if scores["deception"] >= 60:
        return "false"
    return "true"


def build_calibration_summary() -> dict:
    clips = load_archive_clips()
    confusion = {actual: {pred: 0 for pred in LABELS} for actual in LABELS}
    signal_quality_counts = {
        channel: {"real": 0, "fallback": 0, "manual": 0}
        for channel in ("rppg", "facial_au", "voice", "transcript")
    }
    scatter_points = []
    correct = 0

    for clip in clips:
        predicted = predict_label(clip)
        actual = clip["ground_truth"]
        confusion[actual][predicted] += 1
        correct += int(predicted == actual)
        scatter_points.append(
            {
                "clip_id": clip["clip_id"],
                "subject": clip["subject"],
                "ground_truth": actual,
                "predicted_label": predicted,
                "deception": clip["scores"]["deception"],
                "sincerity": clip["scores"]["sincerity"],
                "stress": clip["scores"]["stress"],
                "confidence": clip["scores"]["confidence"],
            }
        )
        for channel, quality in clip["signal_quality"].items():
            signal_quality_counts[channel][quality] += 1

    total = len(clips)
    accuracy = round((correct / total) * 100) if total else 0
    return {
        "total_clips": total,
        "accuracy_percent": accuracy,
        "confusion_matrix": confusion,
        "scatter_points": scatter_points,
        "signal_quality_counts": signal_quality_counts,
    }
