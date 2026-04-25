"""Linguistic deception / sincerity feature extraction.

Uses spaCy ``en_core_web_sm`` for tokenization, POS, and dependency parse.
Computes a feature vector that feeds the composite scoring engine:

- ``hedging_count``           : count of hedge / mitigator tokens
- ``pronoun_drop_rate``       : 1 - (first-person pronouns / expected baseline)
- ``negation_density``        : negation tokens / total tokens
- ``certainty_count``         : count of certainty markers
- ``specificity_score``       : 0-1, density of named entities, dates, numbers
- ``verbal_immediacy``        : 0-1, fraction of present-tense first-person clauses
- ``affect_positive``         : LIWC-lite count
- ``affect_negative``         : LIWC-lite count
- ``avg_sentence_length``     : tokens per sentence

If spaCy or the model is missing, returns a deterministic fallback vector and
records ``signal_quality.linguistic = "fallback"`` upstream.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass

from .config import BACKEND_DIR

# ---------------------------------------------------------------------------
# Lexicons
# ---------------------------------------------------------------------------

HEDGE_WORDS: frozenset[str] = frozenset({
    "kind", "sort", "maybe", "perhaps", "possibly", "probably", "somewhat",
    "rather", "fairly", "quite", "almost", "nearly", "approximately",
    "roughly", "around", "about", "i think", "i guess", "i suppose",
    "i believe", "to be honest", "honestly", "frankly", "actually",
    "basically", "essentially", "literally", "really", "kinda", "sorta",
    "you know", "i mean", "well", "uh", "um", "er", "ah", "like",
    "or something", "anyway", "anyhow", "whatever", "supposedly",
    "allegedly", "apparently", "seemingly", "presumably",
})

CERTAINTY_WORDS: frozenset[str] = frozenset({
    "definitely", "absolutely", "certainly", "clearly", "obviously",
    "undoubtedly", "unquestionably", "without doubt", "for sure",
    "no doubt", "indeed", "of course", "naturally", "exactly",
    "precisely", "categorically", "unequivocally",
})

# LIWC-lite affect lexicons (compact public-domain seed sets).
POSITIVE_AFFECT: frozenset[str] = frozenset({
    "love", "great", "happy", "good", "best", "wonderful", "fantastic",
    "amazing", "excellent", "beautiful", "kind", "fortunate", "blessed",
    "proud", "grateful", "thankful", "honest", "trust", "joy", "hope",
})

NEGATIVE_AFFECT: frozenset[str] = frozenset({
    "hate", "bad", "terrible", "awful", "horrible", "wrong", "sad",
    "angry", "fear", "afraid", "worry", "anxious", "stress", "nervous",
    "regret", "guilt", "shame", "sorry", "disappointed", "upset",
})

NEGATION_TOKENS: frozenset[str] = frozenset({
    "not", "no", "never", "none", "nothing", "neither", "nor",
    "n't", "cannot", "without",
})

FIRST_PERSON_SINGULAR: frozenset[str] = frozenset({
    "i", "me", "my", "mine", "myself", "i'm", "i've", "i'd", "i'll",
})

FIRST_PERSON_PLURAL: frozenset[str] = frozenset({
    "we", "us", "our", "ours", "ourselves", "we're", "we've", "we'd",
    "we'll",
})

# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------


@dataclass
class LinguisticFeatures:
    hedging_count: int
    pronoun_drop_rate: float
    negation_density: float
    certainty_count: int
    specificity_score: float
    verbal_immediacy: float
    affect_positive: int
    affect_negative: int
    avg_sentence_length: float
    word_count: int
    text_deception_prior: float | None
    quality: str  # "real" | "fallback"

    def to_dict(self) -> dict:
        return asdict(self)


# ---------------------------------------------------------------------------
# spaCy backend (optional)
# ---------------------------------------------------------------------------


_SPACY_NLP = None  # cached pipeline


def _load_spacy():
    """Return a cached spaCy pipeline or ``None`` if unavailable."""
    global _SPACY_NLP
    if _SPACY_NLP is not None:
        return _SPACY_NLP
    try:
        import spacy  # type: ignore

        try:
            _SPACY_NLP = spacy.load("en_core_web_sm")
        except OSError:
            return None
        return _SPACY_NLP
    except ImportError:
        return None


def _text_deception_prior(transcript: str) -> float | None:
    """Return P(resolved_false | transcript) from VerdictTextPrior-v1 via Modal.

    Calls the Modal inference service which loads the trained DeBERTa-v3-base
    model from verdict-m1-models volume. Returns None gracefully if Modal is
    unavailable so the rest of the pipeline is unaffected.
    """
    try:
        from services.text_prior_service import score_transcript
        return score_transcript(transcript)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract(transcript: str) -> LinguisticFeatures:
    """Extract linguistic features from ``transcript``.

    Tries spaCy first; on failure falls back to a regex-based estimator that
    still returns a fully populated feature vector. Quality flag distinguishes.
    """
    if not transcript or not transcript.strip():
        return _empty_features()

    nlp = _load_spacy()
    if nlp is not None:
        try:
            features = _extract_spacy(transcript, nlp)
            features.text_deception_prior = _text_deception_prior(transcript)
            return features
        except Exception:  # pragma: no cover - defensive
            pass
    features = _extract_regex_fallback(transcript)
    features.text_deception_prior = _text_deception_prior(transcript)
    return features


# ---------------------------------------------------------------------------
# spaCy implementation
# ---------------------------------------------------------------------------


def _extract_spacy(transcript: str, nlp) -> LinguisticFeatures:
    doc = nlp(transcript)

    tokens = [t for t in doc if not t.is_space]
    word_count = max(len(tokens), 1)

    lower_text = transcript.lower()
    hedging = _count_phrases(lower_text, HEDGE_WORDS)
    certainty = _count_phrases(lower_text, CERTAINTY_WORDS)

    fps_singular = sum(1 for t in tokens if t.text.lower() in FIRST_PERSON_SINGULAR)
    fps_plural = sum(1 for t in tokens if t.text.lower() in FIRST_PERSON_PLURAL)
    expected_fps = max(0.06 * word_count, 1)  # ~6% baseline
    fps_total = fps_singular + 0.5 * fps_plural
    pronoun_drop_rate = max(0.0, min(1.0, 1.0 - fps_total / expected_fps))

    negations = sum(1 for t in tokens if t.text.lower() in NEGATION_TOKENS or t.dep_ == "neg")
    negation_density = negations / word_count

    affect_pos = sum(1 for t in tokens if t.lemma_.lower() in POSITIVE_AFFECT)
    affect_neg = sum(1 for t in tokens if t.lemma_.lower() in NEGATIVE_AFFECT)

    # Specificity = density of named entities + numbers + dates.
    spec_hits = sum(
        1
        for t in tokens
        if t.ent_type_ in {"PERSON", "ORG", "GPE", "DATE", "TIME", "MONEY", "PERCENT", "CARDINAL", "ORDINAL"}
    )
    specificity_score = min(1.0, spec_hits / max(word_count / 10, 1))

    # Verbal immediacy: present tense + first person.
    immediacy_hits = sum(
        1
        for t in tokens
        if t.pos_ == "VERB" and t.morph.get("Tense") == ["Pres"] and any(
            tok.text.lower() in FIRST_PERSON_SINGULAR for tok in t.head.lefts
        )
    )
    verbal_immediacy = min(1.0, immediacy_hits / max(word_count / 15, 1))

    sents = [s for s in doc.sents]
    avg_sent_len = (
        sum(len([t for t in s if not t.is_space]) for s in sents) / max(len(sents), 1)
    )

    return LinguisticFeatures(
        hedging_count=hedging,
        pronoun_drop_rate=pronoun_drop_rate,
        negation_density=negation_density,
        certainty_count=certainty,
        specificity_score=specificity_score,
        verbal_immediacy=verbal_immediacy,
        affect_positive=affect_pos,
        affect_negative=affect_neg,
        avg_sentence_length=avg_sent_len,
        word_count=word_count,
        text_deception_prior=None,
        quality="real",
    )


# ---------------------------------------------------------------------------
# Regex fallback (used when spaCy unavailable)
# ---------------------------------------------------------------------------


_WORD_RE = re.compile(r"[A-Za-z']+")
_SENT_SPLIT = re.compile(r"[.!?]+")


def _extract_regex_fallback(transcript: str) -> LinguisticFeatures:
    lower = transcript.lower()
    words = _WORD_RE.findall(lower)
    word_count = max(len(words), 1)

    hedging = _count_phrases(lower, HEDGE_WORDS)
    certainty = _count_phrases(lower, CERTAINTY_WORDS)

    fps_singular = sum(1 for w in words if w in FIRST_PERSON_SINGULAR)
    fps_plural = sum(1 for w in words if w in FIRST_PERSON_PLURAL)
    expected_fps = max(0.06 * word_count, 1)
    fps_total = fps_singular + 0.5 * fps_plural
    pronoun_drop_rate = max(0.0, min(1.0, 1.0 - fps_total / expected_fps))

    negations = sum(1 for w in words if w in NEGATION_TOKENS)
    negation_density = negations / word_count

    affect_pos = sum(1 for w in words if w in POSITIVE_AFFECT)
    affect_neg = sum(1 for w in words if w in NEGATIVE_AFFECT)

    # Cheap specificity: digits + capitalized non-initial tokens.
    digits = len(re.findall(r"\d+", transcript))
    caps = len(re.findall(r"(?<!^)(?<![.!?]\s)[A-Z][a-z]+", transcript))
    specificity_score = min(1.0, (digits + caps) / max(word_count / 10, 1))

    # Crude immediacy: count of "I am" / "I'm" / "we are".
    immediacy_hits = (
        len(re.findall(r"\bi\s+am\b", lower))
        + len(re.findall(r"\bi'm\b", lower))
        + len(re.findall(r"\bwe\s+are\b", lower))
    )
    verbal_immediacy = min(1.0, immediacy_hits / max(word_count / 30, 1))

    sents = [s for s in _SENT_SPLIT.split(transcript) if s.strip()]
    avg_sent_len = sum(len(_WORD_RE.findall(s)) for s in sents) / max(len(sents), 1)

    return LinguisticFeatures(
        hedging_count=hedging,
        pronoun_drop_rate=pronoun_drop_rate,
        negation_density=negation_density,
        certainty_count=certainty,
        specificity_score=specificity_score,
        verbal_immediacy=verbal_immediacy,
        affect_positive=affect_pos,
        affect_negative=affect_neg,
        avg_sentence_length=avg_sent_len,
        word_count=word_count,
        text_deception_prior=None,
        quality="fallback",
    )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _count_phrases(haystack_lower: str, lexicon: frozenset[str]) -> int:
    """Count whole-token / multi-word phrase occurrences in lowercase text."""
    total = 0
    for phrase in lexicon:
        if " " in phrase or "'" in phrase:
            total += len(re.findall(rf"(?<!\w){re.escape(phrase)}(?!\w)", haystack_lower))
        else:
            total += len(re.findall(rf"\b{re.escape(phrase)}\b", haystack_lower))
    return total


def _empty_features() -> LinguisticFeatures:
    return LinguisticFeatures(
        hedging_count=0,
        pronoun_drop_rate=0.0,
        negation_density=0.0,
        certainty_count=0,
        specificity_score=0.0,
        verbal_immediacy=0.0,
        affect_positive=0,
        affect_negative=0,
        avg_sentence_length=0.0,
        word_count=0,
        text_deception_prior=None,
        quality="fallback",
    )
