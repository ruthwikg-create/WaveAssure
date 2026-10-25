@echo off
setlocal
cd /d "%~dp0.."
if errorlevel 1 (
  echo [WaveAssure] ERROR: Cannot open the project folder.
  exit /b 1
)
set "VENV_PY=.venv\Scripts\python.exe"
if exist "%VENV_PY%" goto :environment_ready

echo [WaveAssure] No virtual environment found. Creating one for this fresh clone...
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
echo [WaveAssure] ERROR: Python 3.11 or 3.12 was not found by the Windows Python launcher.
echo Install Python 3.11 from python.org, then rerun this script.
echo Check installed Python interpreters with: py -0p
exit /b 1

:creation_failed
echo [WaveAssure] ERROR: The virtual environment could not be created.
echo Check Python installation and folder permissions.
exit /b 1

:environment_ready
if not exist "%VENV_PY%" (
  echo [WaveAssure] ERROR: .venv\Scripts\python.exe is unavailable.
  echo Remove or rename a broken .venv directory only after checking for local data.
  exit /b 1
)
echo [WaveAssure] Installing test dependencies...
"%VENV_PY%" -m pip install -r requirements-dev.txt
if errorlevel 1 (
  echo [WaveAssure] ERROR: Test dependency installation failed.
  exit /b 1
)
echo [WaveAssure] Running software tests...
"%VENV_PY%" -m pytest -v
if errorlevel 1 (
  echo [WaveAssure] Tests FAILED. Do not treat this installation as verified.
  exit /b 1
)
echo [WaveAssure] Software tests passed. This is not clinical validation.
exit /b 0
