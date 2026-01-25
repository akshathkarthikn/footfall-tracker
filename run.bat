@echo off
title Footfall Tracker
cd /d "%~dp0"

echo.
echo ========================================
echo       Footfall Tracker
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment.
        echo Make sure Python is installed and in PATH.
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt -q

REM Start the application
echo.
echo Starting Footfall Tracker...
echo Access the app at: http://localhost:8501
echo.
echo Press Ctrl+C to stop the server.
echo.
streamlit run app.py --server.port 8501 --server.address 0.0.0.0

pause
