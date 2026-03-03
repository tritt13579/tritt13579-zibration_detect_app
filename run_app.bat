@echo off
cd /d "%~dp0"

if not exist ".venv\Scripts\pythonw.exe" (
  echo [ERROR] Virtual environment ".venv" was not found.
  echo Please run these commands once:
  echo   py -m venv .venv
  echo   .\.venv\Scripts\activate
  echo   pip install -r requirements.txt
  pause
  exit /b 1
)

set "PYTHONPATH=%cd%\src"
start "" ".venv\Scripts\pythonw.exe" -m app.main
