# VerdictFusion-v1 Labeling Guide

## Unit Of Annotation

Annotate one exact public claim, not a whole video.

Bad: "the entire interview."

Good: "00:31.2-00:38.6, the speaker says customer funds were not used by Alameda."

## Required Labels

| Field | Meaning |
|---|---|
| `claim_text` | Exact claim as spoken, cleaned for readability. |
| `claim_start_seconds` | Claim start time in source video. |
| `claim_end_seconds` | Claim end time in source video. |
| `speaker_name` | Person making the claim. |
| `ground_truth_label` | One of the allowed policy labels. |
| `ground_truth_source_url` | Court record, admission, correction, investigation, official report. |
| `label_confidence` | `high`, `medium`, or `low`. |
| `context_type` | press conference, hearing, trial, interview, deposition, debate, statement. |
| `claim_type` | denial, assertion, explanation, accusation, disclosure, apology. |
| `train_eligible` | Whether this can enter supervised training. |

## Quality Labels

Rate each 0-3:

- face visibility
- lighting
- camera stability
- audio clarity
- transcript alignment
- speaker isolation
- edit/splice risk

Examples with any critical quality score below 1 should usually be abstention
training examples rather than positive/negative training examples.

## Double Review

Every training-positive item needs two independent reviews. Disagreements go to
adjudication and stay out of training until resolved.
