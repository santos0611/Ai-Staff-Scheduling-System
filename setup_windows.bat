@echo off
setlocal
cd /d "%~dp0"

echo Creating Python virtual environment...
py -m venv .venv
if errorlevel 1 (
  echo Failed to create the virtual environment. Ensure Python is installed.
  pause
  exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt

if not exist .env (
  copy .env.example .env >nul
  echo.
  echo Created .env from .env.example.
  echo IMPORTANT: edit .env and enter your local MySQL password before running the app.
)

echo.
echo Python setup complete.
echo Next: import database\schema.sql into MySQL, update .env, then run seed_demo.bat.
pause
