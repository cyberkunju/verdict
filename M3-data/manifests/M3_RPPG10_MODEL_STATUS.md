# M3 rPPG-10 Model Status

Generated: 2026-04-25

Model:

- `m3_rppg10_quality_gated_ensemble_v1`
- Evaluated artifact: `M3-data/models/m3_rppg10_quality_gated_ensemble_v1/model.joblib`
- Deployment artifact trained on all usable rPPG-10 windows: `M3-data/models/m3_rppg10_quality_gated_ensemble_v1/deployment_all_data_model.joblib`
- Metrics: `M3-data/manifests/m3_rppg10_quality_gated_ensemble_v1_metrics.json`
- Modal run: `m3-rppg10-quality-gated-ensemble-v1-20260425T111528Z`
- Modal run URL: `https://modal.com/apps/cyberkunju/main/ap-BmQ8ir1e7IbjJOhb3QtuDV`
- Modal model volume: `verdict-m3-models`
- Modal run artifact path: `/runs/m3-rppg10-quality-gated-ensemble-v1-20260425T111528Z/model`
- Modal latest artifact path: `/latest-rppg10/model`
- Modal latest metrics mirror: `M3-data/manifests/m3_rppg10_modal_latest_metrics.json`

Data:

- Source archive: `rPPG-10.zip`
- SHA256: `4FAED19048DB8DCE15BD9C8F5087BC580AB64DC55A9401873804237EBD9CE62F`
- Extracted dataset: `M3-data/raw/public/rPPG-10/dataset/Dataset_rPPG-10`
- Usable subjects: `26`
- Skipped subject: `Subject_4` because one ROI video cannot be opened.
- Training windows: `869`
- Validation windows: `290`
- Test windows: `347`

Method:

- Mean RGB traces from rPPG-10 ROI videos.
- ECG-derived heart-rate labels.
- GREEN, POS, and CHROM rPPG candidates for forehead, cheek1, and cheek2.
- Temporal smoothing and jump-from-smooth continuity features.
- ExtraTrees heart-rate fusion model.
- RandomForest expected-error model used as quality/reject gate.

Subject-held-out evaluation:

- Full test MAE: `13.5003` BPM.
- Full test RMSE: `21.7292` BPM.
- Full test within 5 BPM: `0.4380`.
- Quality-gated test coverage: `0.1239`.
- Quality-gated test MAE: `3.6887` BPM.
- Quality-gated test within 5 BPM: `0.7674`.
- Quality-gated test within 10 BPM: `1.0`.

Deployment all-data artifact:

- Trained on all usable rPPG-10 windows: `1506`.
- Training-only MAE: `1.4287` BPM.
- Training-only within 5 BPM: `0.9389`.

Interpretation:

This is a real usable M3 prototype model, but it is not production-top-notch.
It performs well only when its quality gate accepts a window. Full-coverage
generalization is still too weak, so production integration must use the quality
gate and mark rejected windows as low-confidence instead of outputting a hard HR.

Next quality jump requires more raw synchronized datasets: UBFC-rPPG, UBFC-Phys,
MMPD, rPPG public benchmark, MCD-rPPG or VitalVideos, and VERDICT own capture.
