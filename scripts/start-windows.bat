@echo off
setlocal
cd /d "%~dp0.."
if errorlevel 1 (
  echo [WaveAssure] ERROR: Cannot open the project folder.
  exit /b 1
)
rem Launch the engineering workspace even if this shell previously used review mode.
set "WAVEASSURE_WORKSPACE_MODE=engineering"
if exist "D:\WaveAssure-Datasets" set "WAVEASSURE_WFDB_ROOT=D:\WaveAssure-Datasets"
set "VENV_PY=.venv\Scripts\python.exe"
if exist "%VENV_PY%" goto :environment_ready

echo [WaveAssure] Creating a virtual environment for this fresh clone...
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
  py -3.11 -m venv .venv
  if errorlevel 1 goto :creation_failed
  goto :environment_ready
)
py -3.12 --version >nul 2>&1
if not errorlevel 1 (
  py -3.12 -m venv .venv
  if errorlevel 1 goto :creation_failed
  goto :environment_ready
)
echo [WaveAssure] ERROR: Python 3.11 or 3.12 is required for the tested Windows setup.
echo Check installed interpreters with: py -0p
exit /b 1

:creation_failed
echo [WaveAssure] ERROR: Could not create the virtual environment.
exit /b 1

:environment_ready
if not exist "%VENV_PY%" (
  echo [WaveAssure] ERROR: Virtual environment Python executable was not found.
  exit /b 1
)
"%VENV_PY%" -m pip install -r requirements.txt
if errorlevel 1 (
  echo [WaveAssure] ERROR: Application dependency installation failed.
  exit /b 1
)
echo [WaveAssure] Starting local research application at http://127.0.0.1:8000
echo [WaveAssure] Chrome opens only after the local server reports ready.
"%VENV_PY%" -u scripts\run-local.py
if errorlevel 1 (
  echo [WaveAssure] ERROR: Application did not start. Read the Python/Uvicorn error printed above.
  echo [WaveAssure] For a direct error trace, run:
  echo [WaveAssure]   .\.venv\Scripts\python.exe -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8000
  exit /b 1
)
exit /b 0
