@echo off
setlocal
cd /d "%~dp0"

:: --- Check for Admin ---
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Run as Administrator!
    pause
    exit /b
)

echo ============================================
echo   Footfall Tracker - Server Deployment
echo ============================================
echo.

:: --- 1. Open Firewall (Port 8501) ---
echo [INFO] Opening firewall port 8501...
netsh advfirewall firewall add rule name="Footfall Tracker" dir=in action=allow protocol=TCP localport=8501

:: --- 2. Create Scheduled Task (At Startup) ---
set "BATCH_PATH=%~dp0Run_App.bat"

echo [INFO] Creating startup service...
:: /sc onstart = Run at boot
:: /ru "%USERNAME%" /rp * = Run as specific user (prompt for password)
:: /rl highest = Run as Admin level
:: /delay 0001:00 = Wait 1 minute after boot before starting
schtasks /create /tn "FootfallTrackerService" /tr "\"%BATCH_PATH%\"" /sc onstart /delay 0001:00 /ru "%USERNAME%" /rp * /rl highest /f

echo.
echo ============================================
echo [OK] Service Installed Successfully!
echo.
echo The app will:
echo   - Start automatically at Windows boot
echo   - Auto-restart if it crashes
echo   - Be accessible at http://localhost:8501
echo   - Be accessible on LAN at http://YOUR_IP:8501
echo.
echo To start now, run: Run_App.bat
echo To uninstall: schtasks /delete /tn "FootfallTrackerService" /f
echo ============================================
pause
