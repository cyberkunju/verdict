"""VerdictTextPrior-v1 inference service via Modal.

Provides score_transcript() that calls the deployed Modal function
and returns P(resolved_false | transcript) in [0, 1].

Falls back to None gracefully when Modal is unavailable.
"""

from __future__ import annotations

import os
import subprocess
import functools
from typing import Optional


# ---------------------------------------------------------------------------
# Modal app config
# ---------------------------------------------------------------------------

MODEL_VOLUME_NAME = "verdict-m1-models"
MODEL_PATH_IN_VOLUME = (
    "/runs/verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z/final"
)
APP_NAME = "verdict-text-prior-inference"
MODEL_MOUNT = "/mnt/verdict-models"


@functools.lru_cache(maxsize=1)
def _modal_available() -> bool:
    """Return True if Modal credentials are configured."""
    try:
        token_id = os.environ.get("MODAL_TOKEN_ID", "")
        token_secret = os.environ.get("MODAL_TOKEN_SECRET", "")
        toml_path = os.path.expanduser("~/.modal.toml")
        return bool(token_id and token_secret) or os.path.exists(toml_path)
    except Exception:
        return False


def _deploy_if_needed() -> None:
    """Deploy the Modal app if not already deployed."""
    import modal
    try:
        modal.Function.from_name(APP_NAME, "_infer_text_prior")
    except modal.exception.NotFoundError:
        # Need to deploy first
        deploy_script = os.path.join(os.path.dirname(__file__), "_deploy_text_prior.py")
        subprocess.run(
            ["modal", "deploy", deploy_script],
            check=True,
            capture_output=True,
            timeout=120,
        )


def score_transcript(transcript: str) -> Optional[float]:
    """Return P(resolved_false | transcript) from VerdictTextPrior-v1.

    Uses modal.Function.from_name to call the already-deployed function.
    Falls back to None if Modal is unavailable or inference fails.
    """
    if not transcript or not transcript.strip():
        return None
    if not _modal_available():
        return None
    try:
        import modal

        # Try to look up the deployed function
        try:
            fn = modal.Function.from_name(APP_NAME, "_infer_text_prior")
        except modal.exception.NotFoundError:
            # Deploy and retry
            _deploy_if_needed()
            fn = modal.Function.from_name(APP_NAME, "_infer_text_prior")

        results = fn.remote([transcript.strip()])
        if results:
            return float(results[0])
        return None
    except Exception as exc:
        try:
            from verdict_pipeline.utils import get_logger
            log = get_logger("text_prior_service")
            log.warning("VerdictTextPrior-v1 inference failed: %s", exc)
        except Exception:
            pass
        return None
