@echo off
cd /d "%~dp0.."
".venv\Scripts\python.exe" -m pip install -r requirements-dev.txt
".venv\Scripts\python.exe" -m pytest -v
pause
