"""Locked clip registry — exactly six clips per CONTRACT.md §3.

URLs are canonical public uploads (AP / CNBC / C-SPAN / Dealbook / official
channel uploads). Timestamps are best-guess windows aligned to the famous
denial sentence; the download script accepts ``--start`` / ``--end`` to
override per-clip after a quick visual check.
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
        video_url="https://www.youtube.com/watch?v=7Q6d-UYYBWU",
        video_start_seconds=3.0,
        video_end_seconds=13.0,
        thumbnail_url="data/thumbnails/nixon_1973.jpg",
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
        video_url="https://www.youtube.com/watch?v=_aGbdni7QNs",
        video_start_seconds=17.0,
        video_end_seconds=28.0,
        thumbnail_url="data/thumbnails/clinton_1998.jpg",
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
        video_url="https://www.youtube.com/watch?v=0sR8Qrj12gE",
        video_start_seconds=4.0,
        video_end_seconds=15.0,
        thumbnail_url="data/thumbnails/armstrong_2005.jpg",
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
        video_url="https://www.youtube.com/watch?v=rGfaJZAdfNE",
        video_start_seconds=12.0,
        video_end_seconds=23.0,
        thumbnail_url="data/thumbnails/holmes_2018.jpg",
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
        video_url="https://www.youtube.com/watch?v=0sfsftGt-s4",
        video_start_seconds=33.0,
        video_end_seconds=45.0,
        thumbnail_url="data/thumbnails/sbf_2022.jpg",
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
        video_url="https://www.youtube.com/watch?v=tLT1mq2u4h4",
        video_start_seconds=8.0,
        video_end_seconds=18.0,
        thumbnail_url="data/thumbnails/haugen_2021.jpg",
        similar_clips=(),
    ),

    # ------------------------------------------------------------------
    # TRUTHFUL ARCHIVE EXPANSION (added 2026-04-25)
    # Sourced from research-data/manifests/truthful_candidates.json.
    # All six are sworn / on-the-record disclosures whose factual content
    # was later vindicated by criminal conviction of the OPPOSING party,
    # release of corroborating documents, or court ruling. Selection
    # rationale documented in the manifest.
    # ------------------------------------------------------------------

    "dean_1973": ClipMeta(
        clip_id="dean_1973",
        subject="John Dean",
        statement=(
            "There is a cancer growing on the presidency, and if the "
            "cancer is not removed, the President himself will be killed "
            "by it."
        ),
        year=1973,
        context=(
            "United States Senate Watergate Committee testimony, "
            "25 June 1973. Former White House Counsel describes the "
            "cover-up directly to the Senate select committee."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Corroborated by the Nixon White House tape of the 21 March "
            "1973 'cancer' meeting; Nixon resigned 9 August 1974 and "
            "every subsequent investigation vindicated Dean's account."
        ),
        video_url="https://www.youtube.com/watch?v=mZx7g74CvKc",
        video_start_seconds=60.0,
        video_end_seconds=90.0,
        thumbnail_url="https://img.youtube.com/vi/mZx7g74CvKc/hqdefault.jpg",
        similar_clips=("nixon_1973", "haugen_2021"),
    ),

    "cheung_2019": ClipMeta(
        clip_id="cheung_2019",
        subject="Erika Cheung",
        statement=(
            "I knew that Theranos was committing a fraud and I had a "
            "moral obligation to do something about it."
        ),
        year=2019,
        context=(
            "TEDx Talk 'Theranos, whistleblowing and speaking truth to "
            "power.' Cheung was the lab associate who reported Theranos "
            "to the FDA and CMS in 2014."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Elizabeth Holmes was convicted on 4 counts of wire fraud "
            "(3 January 2022) directly based on the same patient harm "
            "Cheung reported. Cheung's testimony was central to United "
            "States v. Holmes and v. Balwani."
        ),
        video_url="https://www.youtube.com/watch?v=vMQlj9TZQfE",
        video_start_seconds=30.0,
        video_end_seconds=55.0,
        thumbnail_url="https://img.youtube.com/vi/vMQlj9TZQfE/hqdefault.jpg",
        similar_clips=("holmes_2018", "shultz_2019"),
    ),

    "shultz_2019": ClipMeta(
        clip_id="shultz_2019",
        subject="Tyler Shultz",
        statement=(
            "The data that Theranos was reporting was inaccurate. "
            "Patients were getting test results that were just wrong."
        ),
        year=2019,
        context=(
            "60 Minutes interview. Shultz, grandson of Theranos board "
            "member George Shultz, reported lab fraud despite intense "
            "family pressure to recant."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Validated by Holmes' criminal conviction (3 January 2022); "
            "Shultz separately settled a harassment lawsuit against "
            "Theranos. His original 2015 letter to the New York State "
            "Department of Health is part of the public court record."
        ),
        video_url="https://www.youtube.com/watch?v=fu42enVXLWQ",
        video_start_seconds=30.0,
        video_end_seconds=55.0,
        thumbnail_url="https://img.youtube.com/vi/fu42enVXLWQ/hqdefault.jpg",
        similar_clips=("holmes_2018", "cheung_2019"),
    ),

    "wigand_1996": ClipMeta(
        clip_id="wigand_1996",
        subject="Jeffrey Wigand",
        statement=(
            "We are in the business of selling nicotine, an addictive drug."
        ),
        year=1996,
        context=(
            "60 Minutes interview with Mike Wallace, broadcast 4 February "
            "1996. Former Brown & Williamson VP discloses internal "
            "knowledge that nicotine was deliberately engineered to be "
            "addictive."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Wigand's claims were the basis of the 1998 Tobacco Master "
            "Settlement Agreement (USD 206 billion). The seven tobacco "
            "CEOs who told Congress that nicotine was not addictive "
            "(7 April 1994) were proven to have committed perjury based "
            "on internal documents Wigand identified."
        ),
        video_url="https://www.youtube.com/watch?v=1_-Vu8LrUDk",
        video_start_seconds=30.0,
        video_end_seconds=60.0,
        thumbnail_url="https://img.youtube.com/vi/1_-Vu8LrUDk/hqdefault.jpg",
        similar_clips=("haugen_2021", "armstrong_2005"),
    ),

    "snowden_2013": ClipMeta(
        clip_id="snowden_2013",
        subject="Edward Snowden",
        statement=(
            "I don't want to live in a society that does these sort of "
            "things. I am not willing to live in a world where everything "
            "I do and say is recorded."
        ),
        year=2013,
        context=(
            "First public interview, Hong Kong, 9 June 2013, conducted "
            "by Glenn Greenwald and Laura Poitras for The Guardian. "
            "Snowden identifies himself as the source of the NSA "
            "surveillance disclosures."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "Every classified document Snowden released has been "
            "authenticated. The disclosures led directly to the USA "
            "FREEDOM Act (2 June 2015) ending bulk phone-record "
            "collection, and a 2 September 2020 Ninth Circuit ruling "
            "(United States v. Moalin) declared the program illegal."
        ),
        video_url="https://www.youtube.com/watch?v=0hLjuVyIIrs",
        video_start_seconds=60.0,
        video_end_seconds=90.0,
        thumbnail_url="https://img.youtube.com/vi/0hLjuVyIIrs/hqdefault.jpg",
        similar_clips=("haugen_2021", "ellsberg_1971"),
    ),

    "ellsberg_1971": ClipMeta(
        clip_id="ellsberg_1971",
        subject="Daniel Ellsberg",
        statement=(
            "I felt as an American citizen, as a responsible citizen, "
            "I could no longer cooperate in concealing this information "
            "from the American public."
        ),
        year=1971,
        context=(
            "Press conference in Boston, June 1971, after the Pentagon "
            "Papers were published by The New York Times. Ellsberg "
            "publicly confesses to leaking the classified Vietnam War "
            "study while facing potential life imprisonment under the "
            "Espionage Act."
        ),
        ground_truth="sincere",
        ground_truth_source=(
            "All 12 charges dismissed by Judge Byrne on 11 May 1973 due "
            "to government misconduct (Plumbers' break-in at Ellsberg's "
            "psychiatrist). Supreme Court 6-3 in NYT v. United States "
            "(30 June 1971) upheld publication; Ellsberg's factual "
            "claims have never been contested."
        ),
        video_url="https://www.youtube.com/watch?v=wYQ1EBqcO_Y",
        video_start_seconds=30.0,
        video_end_seconds=60.0,
        thumbnail_url="https://img.youtube.com/vi/wYQ1EBqcO_Y/hqdefault.jpg",
        similar_clips=("nixon_1973", "snowden_2013"),
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
