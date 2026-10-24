@echo off
setlocal
cd /d "%~dp0.."
set "WAVEASSURE_WFDB_ROOT=D:\WaveAssure-Datasets"
if not exist ".venv\Scripts\python.exe" (
 py -3.11 -m venv .venv
 if errorlevel 1 (echo Python 3.11 required & pause & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements-ml.txt
if errorlevel 1 (echo Dependency installation failed & pause & exit /b 1)
echo Auditing VTaC datasets and their official split...
".venv\Scripts\python.exe" benchmarks\train_vtac.py --root "%WAVEASSURE_WFDB_ROOT%" --audit
if errorlevel 1 (echo Need both event_labels.csv and benchmark_data_split.csv & pause & exit /b 1)
echo Training only if there are sufficient valid true and false labelled recordings in each split...
".venv\Scripts\python.exe" benchmarks\train_vtac.py --root "%WAVEASSURE_WFDB_ROOT%" --output "models\vtac" --dataset-version 1.0
if errorlevel 1 (echo No research model installed. Add verified labelled recordings and retry. & pause & exit /b 1)
echo Training finished. Restart WaveAssure to load the research model status.
pause
