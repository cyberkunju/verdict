# UBFC-rPPG Download Attempt

Generated: 2026-04-25

Official page:

- https://sites.google.com/view/ybenezeth/ubfcrppg

Official Drive folder:

- https://drive.google.com/drive/folders/1o0XU4gTIo46YfwaWjIgbtCncc-oF44Xk

Command attempted:

```powershell
python -m gdown --folder https://drive.google.com/drive/folders/1o0XU4gTIo46YfwaWjIgbtCncc-oF44Xk -O .\M3-data\raw\public\UBFC-rPPG
```

Result:

- Folder enumeration succeeded.
- `DATASET_1/10-gt/gtdump.xmp` downloaded successfully.
- First large `vid.avi` download was blocked by Google Drive quota:
  "Too many users have viewed or downloaded this file recently."

Important file ID that was blocked:

- `1ofeTAhg1Oo3X91APQ4AD1nHvuPi0OSGL`
- Browser URL: https://drive.google.com/uc?id=1ofeTAhg1Oo3X91APQ4AD1nHvuPi0OSGL

Next steps:

- Try the Drive folder in browser while logged into Google.
- Use "Add shortcut to Drive" or "Make a copy" if Google allows it.
- Retry `gdown` after 24 hours if quota resets.
