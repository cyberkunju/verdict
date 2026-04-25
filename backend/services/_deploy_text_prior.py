"""Modal app definition for VerdictTextPrior-v1 — deploy with: modal deploy _deploy_text_prior.py"""

import modal

APP_NAME = "verdict-text-prior-inference"
MODEL_VOLUME_NAME = "verdict-m1-models"
MODEL_MOUNT = "/mnt/verdict-models"
MODEL_PATH_IN_VOLUME = (
    "/runs/verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z/final"
)

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

app = modal.App(APP_NAME)
_model_volume = modal.Volume.from_name(MODEL_VOLUME_NAME)


@app.function(
    image=_image,
    gpu=None,
    cpu=2,
    memory=3096,
    timeout=120,
    min_containers=0,
    max_containers=3,
    scaledown_window=120,
    volumes={MODEL_MOUNT: _model_volume},
)
def _infer_text_prior(transcripts: list[str]) -> list[float]:
    """Load model from volume and return P(resolved_false) for each transcript."""
    import json
    import numpy as np
    import torch
    from pathlib import Path
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    model_dir = Path(MODEL_MOUNT) / MODEL_PATH_IN_VOLUME.lstrip("/")
    calib_path = model_dir / "verdict_calibration.json"

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir), use_fast=True)
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir))
    model.eval()

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
            logits = model(**enc).logits
            scaled = logits / temperature
            probs = torch.softmax(scaled, dim=-1)
            p_false = float(probs[0, 1].item())
            results.append(float(np.clip(p_false, 0.0, 1.0)))

    return results
