"""Archive similarity helpers for live and archived analyses."""

from __future__ import annotations

import math

from services.archive_service import load_archive_clips


def _vector(scores: dict) -> tuple[float, float, float, float]:
    return (
        float(scores["deception"]),
        float(scores["sincerity"]),
        float(scores["stress"]),
        float(scores["confidence"]),
    )


def _cosine(a: tuple[float, ...], b: tuple[float, ...]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def top_similar_from_archive(
    scores: dict,
    *,
    exclude_clip_id: str | None = None,
    limit: int = 3,
) -> list[dict]:
    target = _vector(scores)
    ranked: list[dict] = []
    for clip in load_archive_clips():
        if exclude_clip_id and clip["clip_id"] == exclude_clip_id:
            continue
        similarity = _cosine(target, _vector(clip["scores"]))
        ranked.append(
            {
                "clip_id": clip["clip_id"],
                "subject": clip["subject"],
                "statement": clip["statement"],
                "ground_truth": clip["ground_truth"],
                "similarity": round(similarity, 4),
                "scores": clip["scores"],
            }
        )
    ranked.sort(key=lambda item: item["similarity"], reverse=True)
    return ranked[:limit]


def assign_similar_clip_ids(payloads: list[dict], *, limit: int = 2) -> list[dict]:
    ranked_payloads: list[dict] = []
    for payload in payloads:
        target = _vector(payload["scores"])
        candidates = []
        for other in payloads:
            if other["clip_id"] == payload["clip_id"]:
                continue
            candidates.append(
                (
                    _cosine(target, _vector(other["scores"])),
                    other["clip_id"],
                )
            )
        candidates.sort(key=lambda item: item[0], reverse=True)
        payload["similar_clips"] = [clip_id for _, clip_id in candidates[:limit]]
        ranked_payloads.append(payload)
    return ranked_payloads
