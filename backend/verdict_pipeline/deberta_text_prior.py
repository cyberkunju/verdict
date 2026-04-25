"""DeBERTa-v3 text deception prior (preferred over TF-IDF TextPrior-v0).

Loads the fine-tuned ``microsoft/deberta-v3-base`` checkpoint from
``backend/models/deberta_deception/`` (produced by ``modal_deberta.py`` and
pulled with ``modal run ... pull_artifacts``). Exposes a single
``predict(text) -> float`` returning P(deceptive) in [0, 1].

Falls back transparently to None if the model directory is missing or torch /
transformers cannot be imported. ``linguistic._text_deception_prior`` then
falls back to the TF-IDF model.

Why this exists: the TF-IDF TextPrior-v0 was trained on news fact-check claims
(LIAR), which mismatches the first-person testimonial style of the VERDICT
archive. The DeBERTa model is fine-tuned on a balanced mix of Diplomacy
(first-person game messages) + LIAR + AVeriTeC, so it generalizes across
domains.
"""
from __future__ import annotations

from pathlib import Path
from threading import Lock

from .utils import get_logger

log = get_logger("deberta_prior")

_MODEL_DIR = Path(__file__).resolve().parents[1] / "models" / "deberta_deception"
_LOCK = Lock()
_PIPE = None
_LOAD_FAILED = False


def _try_load():
    """Lazy-load the DeBERTa pipeline once. Thread-safe."""
    global _PIPE, _LOAD_FAILED
    if _PIPE is not None or _LOAD_FAILED:
        return _PIPE
    with _LOCK:
        if _PIPE is not None or _LOAD_FAILED:
            return _PIPE
        if not _MODEL_DIR.exists():
            log.info("[deberta] model dir missing at %s -- falling back", _MODEL_DIR)
            _LOAD_FAILED = True
            return None
        try:
            import torch
            from transformers import (
                AutoModelForSequenceClassification,
                AutoTokenizer,
            )
            tok = AutoTokenizer.from_pretrained(str(_MODEL_DIR))
            model = AutoModelForSequenceClassification.from_pretrained(str(_MODEL_DIR))
            device = "cuda" if torch.cuda.is_available() else "cpu"
            model = model.to(device).eval()
            _PIPE = {"tok": tok, "model": model, "device": device}
            log.info("[deberta] loaded fine-tune from %s on %s", _MODEL_DIR.name, device)
            return _PIPE
        except Exception as e:
            log.warning("[deberta] load failed: %s", e)
            _LOAD_FAILED = True
            return None


def is_available() -> bool:
    return _try_load() is not None


def predict(text: str) -> float | None:
    """Return P(deceptive) in [0, 1] or None if model unavailable."""
    pipe = _try_load()
    if pipe is None or not text or not text.strip():
        return None
    try:
        import torch
        tok = pipe["tok"]
        model = pipe["model"]
        device = pipe["device"]
        # Truncate at 256 tokens to match training.
        enc = tok(text, return_tensors="pt", truncation=True, max_length=256)
        enc = {k: v.to(device) for k, v in enc.items()}
        with torch.no_grad():
            logits = model(**enc).logits
            probs = torch.softmax(logits, dim=-1).cpu().numpy()[0]
        # label 1 = deceptive (id2label set in training)
        return float(probs[1])
    except Exception as e:
        log.warning("[deberta] predict failed: %s", e)
        return None
