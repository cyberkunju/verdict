# Modal Training Status

Last updated: 2026-04-25 14:50 IST

## Completed Run

| Field | Value |
|---|---|
| Model | `VerdictTextPrior-v1` |
| Base model | `microsoft/deberta-v3-base` |
| Modal app | `verdict-text-prior-training` |
| Modal model volume | `verdict-m1-models` |
| Modal final model path | `/runs/verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z/final` |
| Modal run URL | `https://modal.com/apps/cyberkunju/main/ap-L3fgJQZTjFZkn6YteaHcSw` |
| GPU | `L40S` |
| Runtime | `436.7s` training time after setup |
| Current app state after run | `stopped`, `0` tasks |

## Data Used

| Split | `resolved_false` | `resolved_true` |
|---|---:|---:|
| Train | 28,270 | 14,136 |
| Validation | 3,533 | 1,766 |
| Test | 3,533 | 1,766 |

Source rows scanned: `210,403`

Rows kept after label/language/English/dedupe filters: `80,281`

Rows sampled for training/evaluation: `53,004`

## Results

Validation:

| Metric | Value |
|---|---:|
| Accuracy | 0.9072 |
| ROC-AUC | 0.9654 |
| False-class precision | 0.9471 |
| False-class recall | 0.9117 |
| False-class F1 | 0.9290 |
| Macro F1 | 0.8974 |

Held-out test at threshold `0.5`:

| Metric | Value |
|---|---:|
| Accuracy | 0.9011 |
| ROC-AUC | 0.9607 |
| Brier score | 0.0741 |
| ECE, 15 bins | 0.0368 |
| Temperature | 1.6646 |
| False-class precision | 0.9375 |
| False-class recall | 0.9125 |
| False-class F1 | 0.9248 |
| Macro F1 | 0.8902 |

## Local Records

- Metrics JSON: `M1-data/manifests/verdict_text_prior_v1_modal_metrics.json`
- Modal run log: `M1-data/manifests/modal_train_20260425_143743.log`
- First failed smoke run log: `M1-data/manifests/modal_train_20260425_143357.log`

The first run was stopped automatically after a gradient-checkpointing backward
graph issue. Its partial artifact directory was deleted from the Modal Volume.
