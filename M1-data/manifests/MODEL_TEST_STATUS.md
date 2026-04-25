# M1 Verdict Text Prior Test Status

Generated: 2026-04-25

Model run:

- `verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z`
- Modal model volume: `verdict-m1-models`
- Model artifact: `/runs/verdict-text-prior-v1-microsoft-deberta-v3-base-20260425T090809Z/final`
- Test report: `M1-data/manifests/verdict_text_prior_v1_post_training_eval.json`

Result: strong benchmark performance, but not production-approved under the strict quality gate.

Key holdout metrics at calibrated threshold `0.4`:

- Test accuracy: `0.9052651443668617`
- Test ROC-AUC: `0.9606842330154227`
- Test macro F1: `0.8939190413569695`
- Test ECE: `0.03584859994347139`
- Test confusion matrix labels: `[resolved_true, resolved_false]`
- Test confusion matrix: `[[1532, 234], [268, 3265]]`

Quality gate:

- `test_roc_auc_ge_0_95`: pass
- `test_macro_f1_ge_0_88`: pass
- `test_ece_le_0_05`: pass
- `all_labeled_smoke_probes_pass`: fail
- Overall: fail

Primary failure:

- The labeled smoke probe `water_boils_true` was predicted as `resolved_false` with probability `0.8958`.

Known weak slices:

- `averitec`: accuracy `0.7487`, macro F1 `0.7436`
- `liar_ucsb`: accuracy `0.6875`, macro F1 `0.6831`

Recommended next action:

- Add curated high-confidence true scientific/common-knowledge claims and hard negative calibration examples, then fine-tune a v2 model with validation-threshold selection and slice-aware acceptance gates.
