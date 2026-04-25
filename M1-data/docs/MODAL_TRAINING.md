# Modal Training Runbook

This runbook trains the current VERDICT text prior on Modal GPU and persists
the output model in Modal storage.

## Volumes

- `verdict-m1-data`: read-only training data volume.
- `verdict-m1-models`: persistent model/checkpoint volume.

Upload the current processed text claims:

```powershell
modal volume create verdict-m1-data
modal volume create verdict-m1-models
modal volume put -f verdict-m1-data .\M1-data\processed\text_claims /text_claims/
```

The trainer searches recursively under `/text_claims`, so both
`/text_claims/*.jsonl` and `/text_claims/text_claims/*.jsonl` layouts are valid.

## Train

Default high-quality run:

```powershell
modal run .\M1-data\scripts\train_text_prior_modal.py --model-name microsoft/deberta-v3-base
```

The training function uses:

- `gpu="L40S"`
- `min_containers=0`
- `max_containers=1`
- `scaledown_window=2`
- `timeout=8h`

When the function exits, the GPU container is eligible for immediate scale-down.
Do not run with `--detach` unless you intentionally want the app to continue
after the local client disconnects.

## Artifacts

The trainer writes:

```text
verdict-m1-models:/runs/<run_name>/dataset_manifest.json
verdict-m1-models:/runs/<run_name>/metrics.json
verdict-m1-models:/runs/<run_name>/final/
```

Intermediate checkpoints are deleted after the final model is saved, so the
Volume keeps the deployment artifact and metrics without redundant checkpoint
weights.

List artifacts:

```powershell
modal volume ls verdict-m1-models /runs
```

Download a finished model:

```powershell
modal volume get verdict-m1-models /runs/<run_name>/final .\backend\models\verdict_text_prior_transformer_v1
```
