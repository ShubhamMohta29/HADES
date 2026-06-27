# DEPENDENCIES Security Report

## Status: MEDIUM

## Findings

`requirements.txt` lists all dependencies without version pins. This violates the CLAUDE.md security rule: "Pin exact versions in package.json / requirements.txt (no ^ or ~ in production)".

### Unpinned packages in `requirements.txt`

```
groq
speechrecognition
pyaudio
requests
psutil
pyautogui
pyperclip
pycaw; platform_system == "Windows"
comtypes; platform_system == "Windows"
python-dotenv
spotipy
opencv-python
Pillow
pywebview
sounddevice
soundfile
supabase
sentence-transformers
openwakeword
numpy
```

Without version pins:
- `pip install -r requirements.txt` on a new machine may install different versions than those tested
- A dependency with a compromised release could be installed automatically
- Reproducible builds are not possible

### Currently installed versions (from `pip list`):
```
comtypes==1.4.15
face-recognition==1.3.0
groq==1.1.0
numpy==2.1.1
opencv-python==4.11.0.86
Pillow==10.3.0
psutil==5.9.8
PyAudio==0.2.14
PyAutoGUI==0.9.54
pycaw==20251023
pyperclip==1.11.0
python-dotenv==1.1.1
pywebview==6.2.1
requests==2.34.2
sentence-transformers==5.6.0
sounddevice==0.5.5
SpeechRecognition==3.14.5
spotipy==2.26.0
supabase==2.22.2
```

`soundfile` and `openwakeword` were not found in the installed packages list — they may not be installed in the current environment.

### No lock file

There is no `requirements.lock`, `poetry.lock`, or `pip.lock` in the repository. `install.bat` creates a venv and runs `pip install -r requirements.txt` without a lock file, meaning each install may resolve different dependency versions.

### Legitimacy check

All packages in `requirements.txt` are well-known, widely downloaded packages on PyPI with long histories. No suspicious packages detected. ✅

## What's at risk

- Supply chain attack via a compromised package version installed automatically
- Broken installs if a new version introduces a breaking change
- Non-reproducible builds make debugging environment-specific issues difficult

## What's already secure

- All packages are legitimate, well-known libraries
- No packages with suspiciously low download counts or recent publish dates

## Recommendations

1. **(MEDIUM — fix)** Pin all packages to exact versions in `requirements.txt` using the currently installed versions.
2. **(LOW)** Consider adding a `requirements-dev.txt` for development-only packages (`pytest`, `PyInstaller`).
