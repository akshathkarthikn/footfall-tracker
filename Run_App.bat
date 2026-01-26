@echo off
setlocal
cd /d "%~dp0"

:: --- 1. Auto-Setup Python Environment ---
if not exist "venv" (
    echo [INFO] Creating venv...
    python -m venv venv
)

:: --- 2. Auto-Install Dependencies ---
if exist "requirements.txt" (
    echo [INFO] Installing dependencies...
    .\venv\Scripts\pip install -r requirements.txt --quiet
)

:: --- 3. Run Loop (Auto-Restart) ---
:run_loop
echo [INFO] Starting Footfall Tracker...

:: Run Streamlit (Bind to 0.0.0.0 for network access)
.\venv\Scripts\streamlit run app.py ^
    --server.port 8501 ^
    --server.address 0.0.0.0 ^
    --server.headless true

:: If app stops/crashes, wait and restart
echo [WARN] App crashed! Restarting in 5s...
timeout /t 5 /nobreak >nul
goto run_loop
