"""VerdictTextPrior-v1 inference service via Modal.

This module provides a single public function ``score_transcript`` that calls the
trained DeBERTa-v3-base model stored in the ``verdict-m1-models`` Modal Volume
and returns P(resolved_false | transcript) in [0, 1].

The model is loaded lazily inside a Modal container function so no GPU or large
model weights are required on the local machine. Falls back to ``None``
gracefully when Modal credentials are unavailable or the network call fails —
the rest of the pipeline is unaffected (text_deception_prior stays None).

Usage:
    from services.text_prior_service import score_transcript
    prior = score_transcript("I did not have sexual relations with that woman.")
    # prior -> float e.g. 0.91, or None on failure
"""

from __future__ import annotations

import os
import functools
from typing import Optional

import modal

# ---------------------------------------------------------------------------
# Modal app + volume configuration
# ---------------------------------------------------------------------------

MODEL_VOLUME_NAME = "verdict-m1-models"
MODEL_PATH_IN_VOLUME = (
    "/runs/verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z/final"
)
APP_NAME = "verdict-text-prior-inference"
MODEL_MOUNT = "/mnt/verdict-models"

# ---------------------------------------------------------------------------
# Modal image: minimal inference-only deps
# ---------------------------------------------------------------------------

_image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install(
        "torch>=2.5,<3",
        "transformers>=4.46,<5",
        "sentencepiece>=0.2,<0.3",
        "protobuf>=5,<6",
        "numpy>=1.26,<3",
    )
    .env({"TOKENIZERS_PARALLELISM": "false"})
)

# ---------------------------------------------------------------------------
# Modal app definition
# ---------------------------------------------------------------------------

_app = modal.App(APP_NAME)
_model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME)


@_app.function(
    image=_image,
    gpu=None,           # CPU inference for short transcripts is fast enough
    cpu=2,
    memory=3096,
    timeout=60,
    min_containers=0,   # cold-start acceptable; this is an async nudge signal
    max_containers=3,
    scaledown_window=60,
    volumes={MODEL_MOUNT: _model_volume},
)
def _infer_text_prior(transcripts: list[str]) -> list[float]:
    """Load model from volume and return P(resolved_false) for each transcript.

    Batch mode so multiple segments can be scored in one container start.
    Temperature scaling is applied using the calibration JSON saved alongside
    the model during training.
    """
    import json
    import numpy as np
    import torch
    from pathlib import Path
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_dir = Path(MODEL_MOUNT) / MODEL_PATH_IN_VOLUME.lstrip("/")
    calib_path = model_dir / "verdict_calibration.json"

    # Load tokenizer + model
    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.eval()

    # Read calibration temperature (set during training)
    temperature = 1.0
    if calib_path.exists():
        calib = json.loads(calib_path.read_text(encoding="utf-8"))
        temperature = float(calib.get("temperature", 1.0))

    results: list[float] = []
    with torch.no_grad():
        for text in transcripts:
            enc = tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=False,
            )
            logits = model(**enc).logits  # shape [1, 2]
            scaled = logits / temperature
            probs = torch.softmax(scaled, dim=-1)
            # label 1 == resolved_false (set during training)
            p_false = float(probs[0, 1].item())
            results.append(float(np.clip(p_false, 0.0, 1.0)))

    return results


# ---------------------------------------------------------------------------
# Public API — called by linguistic.py
# ---------------------------------------------------------------------------


@functools.lru_cache(maxsize=1)
def _modal_available() -> bool:
    """Return True if Modal credentials are configured."""
    try:
        import modal
        # If token env vars or ~/.modal.toml exist, we're good
        token_id = os.environ.get("MODAL_TOKEN_ID", "")
        token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")
        toml_path = os.path.expanduser("~/.modal.toml")
        return bool(token_id and token_secret) or os.path.exists(toml_path)
    except Exception:
        return False


def score_transcript(transcript: str) -> Optional[float]:
    """Return P(resolved_false | transcript) from VerdictTextPrior-v1.

    Returns None if Modal is unavailable or inference fails.
    Calls are synchronous from the caller's perspective — Modal handles the
    container scheduling transparently.
    """
    if not transcript or not transcript.strip():
        return None
    if not _modal_available():
        return None
    try:
        with _app.run():
            results = _infer_text_prior.remote([transcript.strip()])
        if results:
            return float(results[0])
        return None
    except Exception as exc:  # pragma: no cover
        # Log but never crash the pipeline
        try:
            from verdict_pipeline.utils import get_logger
            log = get_logger("text_prior_service")
            log.warning("VerdictTextPrior-v1 inference failed: %s", exc)
        except Exception:
            pass
        return None
