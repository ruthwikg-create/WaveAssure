@echo off
setlocal
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  py -3.11 -m venv .venv
  if errorlevel 1 (echo Python 3.11 environment creation failed & exit /b 1)
)
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pytest -q --junitxml=reports\junit-v0.7.xml
if errorlevel 1 (echo Tests failed - do not release & exit /b 1)
".venv\Scripts\python.exe" scripts\publication_audit.py
if errorlevel 1 (echo Publication checklist blocked - inspect report & exit /b 1)
echo Local research software checks passed. NOT clinically validated or certified.
