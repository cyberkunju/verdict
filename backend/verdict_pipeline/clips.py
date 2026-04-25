"""Locked clip registry — exactly six clips per CONTRACT.md §3.

URLs and timestamps are placeholders; verify and update in Phase 1 before
running ``download_clip.py``. Subject metadata, ground truth, and similarity
links are authoritative.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ClipMeta:
    clip_id: str
    subject: str
    statement: str
    year: int
    context: str
    ground_truth: str  # "true" | "false" | "sincere"
    ground_truth_source: str
    video_url: str
    video_start_seconds: float
    video_end_seconds: float
    thumbnail_url: str = ""
    similar_clips: tuple[str, ...] = field(default_factory=tuple)

    @property
    def duration(self) -> float:
        return self.video_end_seconds - self.video_start_seconds


# ---------------------------------------------------------------------------
# Registry — 6 clips, immutable order matters for archive display
# ---------------------------------------------------------------------------


CLIPS: dict[str, ClipMeta] = {
    "nixon_1973": ClipMeta(
        clip_id="nixon_1973",
        subject="Richard Nixon",
        statement="I am not a crook.",
        year=1973,
        context=(
            "Press conference at Walt Disney World, Orlando, Florida, "
            "responding to questions about Watergate."
        ),
        ground_truth="false",
        ground_truth_source=(
            "Resigned 9 August 1974 after release of the 'smoking gun' "
            "tape; Watergate cover-up confirmed by US House Judiciary "
            "Committee impeachment articles."
        ),
        video_url="",  # TODO: set to the canonical YouTube clip URL.
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=("clinton_1998", "armstrong_2005"),
    ),
    "clinton_1998": ClipMeta(
        clip_id="clinton_1998",
        subject="Bill Clinton",
        statement=(
            "I did not have sexual relations with that woman, "
            "Miss Lewinsky."
        ),
        year=1998,
        context=(
            "White House press conference, 26 January 1998, in response "
            "to the Lewinsky scandal allegations."
        ),
        ground_truth="false",
        ground_truth_source=(
            "Subsequent grand-jury testimony and the 1998 Starr Report "
            "established the relationship; Clinton was impeached on "
            "perjury / obstruction-of-justice charges."
        ),
        video_url="",  # TODO
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=("nixon_1973", "armstrong_2005"),
    ),
    "armstrong_2005": ClipMeta(
        clip_id="armstrong_2005",
        subject="Lance Armstrong",
        statement="I have never doped.",
        year=2005,
        context=(
            "Public denial of doping allegations during the height of his "
            "Tour de France dominance."
        ),
        ground_truth="false",
        ground_truth_source=(
            "Confessed in January 2013 interview with Oprah Winfrey; "
            "lifetime ban from cycling and stripped of seven Tour de "
            "France titles by USADA."
        ),
        video_url="",  # TODO
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=("clinton_1998", "holmes_2018"),
    ),
    "holmes_2018": ClipMeta(
        clip_id="holmes_2018",
        subject="Elizabeth Holmes",
        statement=(
            "Our technology works, and the test results we have provided "
            "patients are accurate."
        ),
        year=2018,
        context=(
            "Defending Theranos's Edison blood-testing device against "
            "Wall Street Journal reporting on falsified results."
        ),
        ground_truth="false",
        ground_truth_source=(
            "Convicted on four counts of fraud in January 2022; sentenced "
            "to 11 years 3 months in federal prison."
        ),
        video_url="",  # TODO
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=("sbf_2022", "armstrong_2005"),
    ),
    "sbf_2022": ClipMeta(
        clip_id="sbf_2022",
        subject="Sam Bankman-Fried",
        statement=(
            "FTX customer funds were never used by Alameda Research."
        ),
        year=2022,
        context=(
            "Public statements and interviews after FTX's collapse, "
            "denying co-mingling of customer assets with Alameda."
        ),
        ground_truth="false",
        ground_truth_source=(
            "Convicted on seven counts of fraud and conspiracy in "
            "November 2023; sentenced to 25 years in federal prison."
        ),
        video_url="",  # TODO
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=("holmes_2018", "armstrong_2005"),
    ),
    "haugen_2021": ClipMeta(
        clip_id="haugen_2021",
        subject="Frances Haugen",
        statement=(
            "Facebook's own research shows their products harm children "
            "and weaken democracy."
        ),
        year=2021,
        context=(
            "United States Senate Subcommittee testimony, 5 October "
            "2021, on Facebook's internal research disclosures."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Whistleblower disclosure verified by tens of thousands of "
            "internal Facebook documents released to the SEC and "
            "reported by The Wall Street Journal as 'The Facebook "
            "Files'."
        ),
        video_url="",  # TODO
        video_start_seconds=0.0,
        video_end_seconds=15.0,
        thumbnail_url="",
        similar_clips=(),
    ),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def get_clip(clip_id: str) -> ClipMeta:
    """Look up a clip by id. Raises ``KeyError`` if unknown."""
    if clip_id not in CLIPS:
        raise KeyError(
            f"Unknown clip_id: {clip_id!r}. "
            f"Allowed: {sorted(CLIPS.keys())}"
        )
    return CLIPS[clip_id]


def all_clip_ids() -> list[str]:
    """Return the locked list of clip_ids in archive display order."""
    return list(CLIPS.keys())


def all_clips() -> list[ClipMeta]:
    """Return all six clip metas in archive display order."""
    return list(CLIPS.values())
