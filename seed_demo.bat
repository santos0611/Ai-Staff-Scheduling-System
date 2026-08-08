@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Virtual environment not found. Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
python scripts\seed_demo.py
pause
