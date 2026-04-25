# Extended rPPG Dataset Discovery

Generated: 2026-04-25

This file records rPPG/heart-rate datasets found during the expanded search.
Datasets with synchronized ECG, PPG, BVP, or pulse-oximeter labels are valuable.
Random public videos without reference physiology are not valid HR training data.

## Direct / Partly Direct

### UBFC-rPPG

- Value: P0.
- Link: https://sites.google.com/view/ybenezeth/ubfcrppg
- Official Drive: https://drive.google.com/drive/folders/1o0XU4gTIo46YfwaWjIgbtCncc-oF44Xk
- Content: two datasets; webcam RGB video at 30 FPS, Logitech C920, CMS50E pulse-oximeter waveform and HR ground truth.
- Scale: Dataset 1 has 8 videos; Dataset 2 has 42 shared videos.
- Status: attempted automated Drive download. Folder listing worked, but the first large `vid.avi` was blocked by Google Drive quota. One small `gtdump.xmp` was downloaded.
- Local partial path: `M3-data/raw/public/UBFC-rPPG`.
- Need from user: try the Drive folder in browser or add to own Drive and retry later.

### UBFC-Phys

- Value: P0/P1 for VERDICT because it includes speech/stress/arithmetic tasks.
- Author page: https://sites.google.com/view/ybenezeth/ubfc-phys
- Data portal: https://search-data.ubfc.fr/FR-18008901306731-2022-05-05_UBFC-Phys-A-Multimodal-Dataset-For.html
- Content: 56 participants, three tasks each, video plus Empatica E4 BVP and EDA, anxiety scores.
- Data portal lists 8 files including subject archives:
  - `s1_to_s10.7z`: 142.38 GB
  - `s11_to_s20.7z`: 148.99 GB
  - `s21_to_s30.7z`: 136.44 GB
  - `s31_to_s40.7z`: 140.03 GB
  - `s41_to_s50.7z`: 141.29 GB
  - `s51_to_s56.7z`: 85.43 GB
- License: CC BY-NC-SA.
- Need from user: portal download may require interactive login/session; this is very valuable.

### rPPG-10

- Value: P0/P1 because it is long-duration and realistic natural-light data.
- Link: https://data.mendeley.com/datasets/bx8982xgwt/1
- Code: https://github.com/GRodrigues4/rPPG-10
- Content: 26 usable subjects, 10-minute recordings, three 64x64 ROI videos per subject, synchronized ECG `.npy`, participant/environment metadata.
- License: CC BY-NC-SA 4.0.
- Need from user: use Mendeley "Download All" if API/browser automation is blocked.

### Public Benchmark Dataset for Testing rPPG Algorithm Performance

- Value: P1, specifically for lighting, skin tone, motion, high HR and pulse-rate-change robustness.
- Link: https://figshare.com/articles/dataset/Public_Benchmark_Dataset_for_Testing_rPPG_Algorithm_Performance/12684059
- Reported size: 16.78 GB.
- Need from user: direct Figshare download may be possible through browser.

### LGI-PPGI

- Value: P1 for in-the-wild motion/exercise/urban conversation robustness.
- Link: https://github.com/partofthestars/LGI-PPGI-DB
- Content: 25 users, 100 videos, about 200 minutes, Logitech C270, CMS50E PPG, 25 FPS.
- License: CC BY 4.0.
- Status: current README says hosting is limited; first six session archives are listed but may be unavailable.
- Contact: info@cancontrols.com.

### MCD-rPPG

- Value: P0/P1 if access works. Very large and modern.
- Code: https://github.com/ksyegorov/mcd_rppg
- Dataset link from repo: https://huggingface.co/datasets/ksyegorov/MCD-rPPG
- Content claimed by repo: 600 subjects, 3600 videos, 3 camera views, rest/post-exercise, synchronized PPG and ECG, 13 health biomarkers.
- Local metadata collected: `M3-data/sources/mcd_rppg_metadata`.
- Need from user: Hugging Face access may require acceptance/login.

### COHFACE

- Value: P1/P2 for cross-dataset evaluation.
- Link: https://zenodo.org/records/4081054
- Content: 160 one-minute RGB face videos, 40 subjects, synchronized heart-rate and breathing-rate.
- Access: restricted Zenodo record; non-commercial EULA; institutional/professional email required.
- Local metadata collected: `M3-data/raw/restricted/COHFACE/zenodo_record_4081054.json`.
- Need from user: request access through Zenodo.

## Request / Agreement Required

### MMPD

- Value: P0. Probably the most important dataset for daily/mobile robustness.
- Link: https://github.com/McJackTang/MMPD_rPPG_dataset
- Content: 33 subjects, 11 hours, mobile videos, PPG labels, skin tone, motion, lighting, exercise/talking/walking labels.
- Status: metadata and release forms collected locally.
- Access: signed release agreement required; commercial use prohibited by dataset terms.

### VitalVideos / VitalVideos-Worldwide

- Value: P0 if accessible; scale and skin-tone diversity are very important.
- Link: https://vitalvideos.org/
- Paper: https://openaccess.thecvf.com/content/ICCV2025W/CVPM/papers/Toye_VitalVideos-Worldwide_A_large_and_diverse_rPPG_dataset_with_rich_ground_ICCVW_2025_paper.pdf
- Access: license/contact.
- Need from user: request/license access.

### VIPL-HR V1 / V2

- Value: P1 because of large less-constrained face-video HR benchmark coverage.
- V1: https://vipl.ict.ac.cn/resources/databases/201811/t20181129_32716.html
- V2: https://vipl.ict.ac.cn/resources/databases/202007/t20200714_32718.html
- Access: application/release agreement; academic/research constraints.

### ECG-Fitness

- Value: P1 for strong motion, exercise, high HR, non-frontal angles, and lighting interference.
- Link: https://cmp.felk.cvut.cz/~spetlrad/ecg-fitness/
- Content: 17 subjects, 207 videos, two Logitech C920 cameras, ECG reference, HR 56-159 BPM, about 200 GB.
- Access: signed request form emailed to dataset owner.

### V4V / MMSE-HR

- Value: P1/P2 for challenge-style non-contact physiological estimation.
- Link: https://vision4vitals.github.io/v4v_dataset.html
- Access: signed EULA; recipient must be full-time faculty/researcher/employee.
- Contact emails are listed on the dataset page.

### HRVCam

- Value: P1 if obtainable because it targets HRV from camera, not only HR.
- Link from rPPG-Trends: https://rice.app.box.com/s/noy6vn7k5g5bfvl9o6ekcjmgc9ng4yel
- Paper: https://www.spiedigitallibrary.org/journals/journal-of-biomedical-optics/volume-26/issue-02/022707/HRVCam-robust-camera-based-measurement-of-heart-rate-variability/10.1117/1.JBO.26.2.022707.full?SSO=1&tab=ArticleLink
- Need from user: try Box link and record access terms.

### Vicar-PPG-2

- Value: P2.
- Request form: https://docs.google.com/forms/d/e/1FAIpQLScwnW_D5M4JVovPzpxA0Bf1ZCTaG5vh7sYu48I0MVSpgltvdw/viewform
- Paper: https://arxiv.org/abs/2012.15846
- Access: Google Form request.

### OBF, PFF, NICU, MAHNOB-HCI

- Value: mostly P2 for cross-domain robustness; some are less directly aligned with webcam HR or have stricter access.
- MAHNOB-HCI: https://mahnob-db.eu/hci-tagging/
- MMSE-HR / related tech transfer page: https://binghamton.technologypublisher.com/tech/MMSE-HR_dataset_(Multimodal_Spontaneous_Expression-Heart_Rate_dataset)

## Tooling / Survey Assets Collected

- rPPG-Trends README and bibliography: `M3-data/sources/rppg_trends`.
- MCD-rPPG metadata CSV files: `M3-data/sources/mcd_rppg_metadata`.
- Existing rPPG-Toolbox checkout and pretrained checkpoint inventory: `research-data/pretrained/rppg_toolbox`, summarized in `M3-data/manifests/rppg_asset_inventory.json`.

## Current Practical Priority

1. Finish UBFC-rPPG download manually or retry after Google quota resets.
2. Download UBFC-Phys through the data portal if storage allows.
3. Download rPPG-10 from Mendeley.
4. Request MMPD full/mini dataset.
5. Request or license VitalVideos/MCD-rPPG.
6. Begin VERDICT own-capture dataset, because public datasets alone will not match final deployment.
