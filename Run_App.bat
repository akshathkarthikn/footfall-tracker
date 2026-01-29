@echo off
setlocal
cd /d "%~dp0"

:: ============================================
:: CONFIGURATION - Edit these for each app
:: ============================================
set APP_NAME=Footfall Tracker
set APP_PORT=8502
set APP_FILE=app.py

:: ============================================
:: AUTO-SETUP
:: ============================================

:: --- 1. Create Python Environment ---
if not exist "venv" (
    echo [INFO] Creating virtual environment...
    python -m venv venv
)

:: --- 2. Install Dependencies ---
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    .\venv\Scripts\pip install -r requirements.txt --quiet
)

:: --- 3. Run Loop (Auto-Restart on Crash) ---
:run_loop
echo.
echo ============================================
echo   %APP_NAME%
echo   Running on port %APP_PORT%
echo   Access: http://localhost:%APP_PORT%
echo ============================================
echo.

:: Run Streamlit (0.0.0.0 = accessible on LAN)
.\venv\Scripts\streamlit run %APP_FILE% ^
    --server.port %APP_PORT% ^
    --server.address 0.0.0.0 ^
    --server.headless true

:: If app crashes, wait and restart
echo.
echo [WARN] %APP_NAME% stopped! Restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto run_loop
