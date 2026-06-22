@echo off
echo ========================================
echo  FARE MATRIX — First-time setup
echo ========================================
echo.

REM Check Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Download from python.org and re-run this script.
    pause
    exit /b 1
)

echo [1/3] Creating virtual environment...
python -m venv venv
call venv\Scripts\activate.bat

echo [2/3] Installing dependencies...
pip install -r requirements.txt

echo [3/3] Setting up config...
if not exist .env (
    copy .env.example .env
    echo.
    echo .env file created. Open it and fill in your credentials:
    echo   - HOTELBEDS_API_KEY and HOTELBEDS_SECRET   (your Bedsonline credentials)
    echo   - AMADEUS_API_KEY and AMADEUS_API_SECRET    (free at amadeus.com/developers)
    echo   - EMAIL_FROM, EMAIL_TO, SMTP_PASSWORD       (optional, for email delivery)
    echo.
    notepad .env
) else (
    echo .env already exists — skipping.
)

echo.
echo ========================================
echo  Setup complete!
echo  Next: fill in your .env, then run:
echo    run.bat
echo ========================================
pause
