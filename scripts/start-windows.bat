@echo off
cd /d "%~dp0.."
rem Launch the engineering workspace even if this shell previously used review mode.
set "WAVEASSURE_WORKSPACE_MODE=engineering"
if exist "D:\WaveAssure-Datasets" set "WAVEASSURE_WFDB_ROOT=D:\WaveAssure-Datasets"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 (echo Could not create Python environment & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (echo Dependency install failed & pause & exit /b 1)
start "" http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8000
pause
