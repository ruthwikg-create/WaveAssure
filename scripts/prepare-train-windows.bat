@echo off
setlocal
cd /d "%~dp0.."
set "WAVEASSURE_WFDB_ROOT=D:\WaveAssure-Datasets"
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
  if errorlevel 1 (echo Python 3.11 is required & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements-ml.txt
if errorlevel 1 (echo Dependency installation failed & pause & exit /b 1)
echo Resuming only SELECTED labelled VTaC files; this may be slow on PhysioNet.
echo Stop anytime with CTRL+C. Re-run THIS SAME FILE to continue.
".venv\Scripts\python.exe" benchmarks\prepare_and_train.py --root "%WAVEASSURE_WFDB_ROOT%" --output models\vtac --version 1.0
if errorlevel 1 (echo Model NOT installed yet. See reason above. & pause & exit /b 1)
echo Research model installed. Restart WaveAssure. CLINICAL USE PROHIBITED.
pause
