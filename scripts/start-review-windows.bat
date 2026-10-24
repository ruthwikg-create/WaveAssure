@echo off
cd /d "%~dp0.."
if not exist ".venv\Scripts\python.exe" (
  echo Install dependencies by launching start-windows.bat once.
  pause
  exit /b 1
)
if "%WAVEASSURE_REVIEW_KEY%"=="" (
  echo ERROR: Set WAVEASSURE_REVIEW_KEY to a random 32+ character secret in PowerShell.
  echo See docs\REVIEW_MODE.md
  pause
  exit /b 1
)
set "WAVEASSURE_WORKSPACE_MODE=review"
".venv\Scripts\python.exe" -m uvicorn waveassure.api:app --host 127.0.0.1 --port 8001
pause
