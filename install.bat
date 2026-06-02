@echo off
setlocal enabledelayedexpansion

echo.
echo  ============================================================
echo   H.A.D.E.S  --  One-Command Installer (no C++ required)
echo  ============================================================
echo.

:: ── Check Python ─────────────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python is not installed or not on PATH.
    echo         Download from https://www.python.org/downloads/
    pause
    exit /b 1
)

for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  Python %PYVER% detected.
echo.

:: ── Create venv ───────────────────────────────────────────────────────────────
if not exist "venv\" (
    echo  Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo  ERROR: Could not create virtual environment.
        pause
        exit /b 1
    )
    echo  Virtual environment created.
) else (
    echo  Virtual environment already exists, skipping.
)
echo.

:: ── Activate and install dependencies ────────────────────────────────────────
echo  Installing dependencies (this may take a few minutes)...
call venv\Scripts\activate.bat
pip install --upgrade pip --quiet
pip install -r requirements.txt
if errorlevel 1 (
    echo  ERROR: pip install failed. Check requirements.txt and your internet connection.
    pause
    exit /b 1
)
echo.
echo  Dependencies installed.
echo.

:: ── Copy .env ─────────────────────────────────────────────────────────────────
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env" >nul
        echo  Created .env from .env.example
        echo  IMPORTANT: Open .env and fill in your API keys before running HADES.
    )
) else (
    echo  .env already exists, skipping.
)
echo.

:: ── Piper CLI binary (prebuilt — no Visual C++ needed) ───────────────────────
if not exist "piper\piper.exe" (
    echo  Downloading Piper TTS CLI binary for Windows...
    python -c "import urllib.request,zipfile,io; print('  Fetching piper_windows_amd64.zip ...'); data=urllib.request.urlopen('https://github.com/rhasspy/piper/releases/download/2023.11.14-2/piper_windows_amd64.zip').read(); zipfile.ZipFile(io.BytesIO(data)).extractall('.'); print('  Piper CLI ready.')"
    if errorlevel 1 (
        echo  WARNING: Could not download Piper CLI. HADES will run without voice output.
        echo           Download manually from: https://github.com/rhasspy/piper/releases
    )
) else (
    echo  Piper CLI already present.
)
echo.

:: ── Piper voice model ─────────────────────────────────────────────────────────
if not exist "voices\en_GB-alan-medium.onnx" (
    echo  Downloading Piper voice model (en_GB-alan-medium, ~60 MB)...
    python -c "import urllib.request,os; base='https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_GB/alan/medium/'; os.makedirs('voices',exist_ok=True); [urllib.request.urlretrieve(base+f,'voices/'+f) or print('  Downloaded',f) for f in ['en_GB-alan-medium.onnx','en_GB-alan-medium.onnx.json'] if not os.path.exists('voices/'+f)]"
    if errorlevel 1 (
        echo  WARNING: Could not download voice model. Run the app and it will retry.
    )
) else (
    echo  Piper voice model found.
)
echo.

:: ── Done ─────────────────────────────────────────────────────────────────────
echo  ============================================================
echo   Installation complete!
echo.
echo   Next steps:
echo    1. Edit .env and add your API keys
echo    2. Run:  venv\Scripts\activate  ^&^&  python main.py
echo  ============================================================
echo.
pause
