@echo off
setlocal
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Virtual environment not found. Run setup_windows.bat first.
  pause
  exit /b 1
)
call .venv\Scripts\activate.bat
start "" http://127.0.0.1:5000
python backend\app.py
pause
