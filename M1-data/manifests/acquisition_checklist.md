# M1 Acquisition Checklist

Review license/terms before downloading raw data.

## real_life_trial_deception_umich

- Name: Real-Life Deception Detection Dataset
- Category: deception_multimodal
- Priority: P0
- URL: https://lit.eecs.umich.edu/deceptiondetection/
- License status: research_dataset_terms_required
- Use for: fusion_pretraining, linguistic_model, hard_eval
- Action: review terms, record approval, then acquire.

## perez_rosas_lrec_2014_multimodal

- Name: A Multimodal Dataset for Deception Detection
- Category: deception_physiological
- Priority: P1
- URL: https://aclanthology.org/L14-1673/
- License status: check_acl_and_dataset_terms
- Use for: physio_linguistic_pretraining, fusion_pretraining
- Action: review terms, record approval, then acquire.

## ubfc_rppg

- Name: UBFC-rPPG
- Category: rppg
- Priority: P0
- URL: https://paperswithcode.com/dataset/ubfc-rppg
- License status: check_dataset_terms
- Use for: rppg_training, rppg_eval
- Action: review terms, record approval, then acquire.

## pure_rppg

- Name: PURE rPPG Dataset
- Category: rppg
- Priority: P0
- URL: https://www.tu-ilmenau.de/en/neurob/data-sets-code/pulse-rate-detection-dataset-pure
- License status: request_or_terms_required
- Use for: rppg_training, cross_dataset_eval
- Action: review terms, record approval, then acquire.

## ubfc_phys

- Name: UBFC-Phys
- Category: rppg_stress
- Priority: P0
- URL: https://team.inria.fr/robotlearn/ubfc-phys/
- License status: noncommercial_or_terms_required
- Use for: rppg_training, stress_model, contact_to_contactless_distillation
- Action: review terms, record approval, then acquire.

## mmpd_rppg

- Name: MMPD Multi-Domain Mobile Video Physiology Dataset
- Category: rppg
- Priority: P1
- URL: https://github.com/THU-CS-PI/MMPD_rPPG_dataset
- License status: check_repo_terms
- Use for: rppg_robustness, mobile_domain_eval
- Action: review terms, record approval, then acquire.

## ravdess

- Name: RAVDESS
- Category: voice_face_emotion
- Priority: P0
- URL: https://zenodo.org/records/1188976
- License status: cc_by_nc_sa_4_0_research_only
- Use for: voice_arousal_training, face_expression_training
- Action: review terms, record approval, then acquire.

## iemocap

- Name: IEMOCAP
- Category: voice_multimodal_emotion
- Priority: P0
- URL: https://sail.usc.edu/iemocap/
- License status: access_agreement_required
- Use for: voice_arousal_training, multimodal_emotion_eval
- Action: review terms, record approval, then acquire.

## crema_d

- Name: CREMA-D
- Category: voice_face_emotion
- Priority: P1
- URL: https://cheyneycomputerscience.github.io/CREMA-D/
- License status: check_project_terms
- Use for: voice_arousal_training, face_expression_training
- Action: review terms, record approval, then acquire.

## msp_podcast

- Name: MSP-Podcast
- Category: naturalistic_voice_emotion
- Priority: P0
- URL: https://www.lab-msp.com/MSP/MSP-Podcast.html
- License status: request_or_terms_required
- Use for: voice_arousal_training, naturalistic_voice_eval
- Action: review terms, record approval, then acquire.

## disfa

- Name: DISFA
- Category: facial_action_units
- Priority: P0
- URL: http://mohammadmahoor.com/disfa/
- License status: request_required
- Use for: au_training, au_eval
- Action: review terms, record approval, then acquire.

## bp4d

- Name: BP4D / BP4D+
- Category: facial_action_units
- Priority: P0
- URL: http://www.cs.binghamton.edu/~lijun/Research/3DFE/3DFE_Analysis.html
- License status: request_required
- Use for: au_training, au_eval, contact_to_contactless_distillation
- Action: review terms, record approval, then acquire.

## openface

- Name: OpenFace
- Category: facial_feature_extractor
- Priority: P0
- URL: https://github.com/TadasBaltrusaitis/OpenFace
- License status: tool_license_and_model_terms
- Use for: pseudo_labeling, baseline_features, au_extraction
- Action: review terms, record approval, then acquire.

## faceforensicspp

- Name: FaceForensics++
- Category: integrity_deepfake
- Priority: P0
- URL: https://github.com/ondyari/FaceForensics
- License status: request_or_terms_required
- Use for: integrity_gate_training, deepfake_eval
- Action: review terms, record approval, then acquire.

## dfdc

- Name: DeepFake Detection Challenge Dataset
- Category: integrity_deepfake
- Priority: P1
- URL: https://www.kaggle.com/c/deepfake-detection-challenge/data
- License status: kaggle_terms_required
- Use for: integrity_gate_training, deepfake_eval
- Action: review terms, record approval, then acquire.

## celeb_df

- Name: Celeb-DF
- Category: integrity_deepfake
- Priority: P1
- URL: https://github.com/yuezunli/celeb-deepfakeforensics
- License status: request_or_terms_required
- Use for: deepfake_generalization_eval
- Action: review terms, record approval, then acquire.

## gdelt_tv

- Name: GDELT Television API / Internet Archive TV News
- Category: public_claim_discovery
- Priority: P0
- URL: https://blog.gdeltproject.org/gdelt-2-0-television-api-debuts/
- License status: metadata_api_terms_required
- Use for: claim_discovery, public_video_search
- Action: review terms, record approval, then acquire.

## internet_archive_tv

- Name: Internet Archive TV News Archive
- Category: public_claim_discovery
- Priority: P0
- URL: https://archive.org/details/tv
- License status: archive_terms_required
- Use for: claim_discovery, caption_search, video_locator
- Action: review terms, record approval, then acquire.

## cspan_video_library

- Name: C-SPAN Video Library
- Category: public_claim_discovery
- Priority: P0
- URL: https://www.c-span.org/
- License status: terms_required
- Use for: hearings, press_conferences, baseline_mining
- Action: review terms, record approval, then acquire.

## claimbuster

- Name: ClaimBuster Dataset
- Category: claim_detection
- Priority: P1
- URL: https://idir.uta.edu/claimbuster/
- License status: check_dataset_terms
- Use for: claim_segmenter_training, claim_worthiness
- Action: review terms, record approval, then acquire.

## politifact

- Name: PolitiFact
- Category: ground_truth_metadata
- Priority: P1
- URL: https://www.politifact.com/
- License status: metadata_citation_only_unless_licensed
- Use for: ground_truth_sources, claim_metadata
- Action: review terms, record approval, then acquire.

## wikidata

- Name: Wikidata
- Category: public_knowledge_graph
- Priority: P2
- URL: https://www.wikidata.org/wiki/Wikidata:Main_Page
- License status: cc0
- Use for: entity_resolution, subject_metadata, event_metadata
- Action: review terms, record approval, then acquire.
