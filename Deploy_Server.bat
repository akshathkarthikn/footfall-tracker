@echo off
setlocal
cd /d "%~dp0"

:: ============================================
:: CONFIGURATION - Edit these for each app
:: ============================================
set APP_NAME=Footfall Tracker
set SERVICE_NAME=FootfallTrackerService
set APP_PORT=8501
set STARTUP_DELAY=0001:00

:: Delay format: HHMM:SS (0001:00 = 1 minute, 0002:00 = 2 minutes)
:: Stagger delays for multiple apps to prevent CPU spike at boot

:: ============================================
:: ADMIN CHECK
:: ============================================
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Please run as Administrator!
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b
)

echo.
echo ============================================
echo   %APP_NAME% - Server Deployment
echo ============================================
echo.

:: ============================================
:: 1. FIREWALL RULE
:: ============================================
echo [1/2] Opening firewall port %APP_PORT%...
netsh advfirewall firewall delete rule name="%APP_NAME%" >nul 2>&1
netsh advfirewall firewall add rule name="%APP_NAME%" dir=in action=allow protocol=TCP localport=%APP_PORT%
echo       Done.
echo.

:: ============================================
:: 2. SCHEDULED TASK (Windows Service)
:: ============================================
echo [2/2] Creating startup service...
set "BATCH_PATH=%~dp0Run_App.bat"

:: Remove existing task if any
schtasks /delete /tn "%SERVICE_NAME%" /f >nul 2>&1

:: Create new task
:: /sc onstart  = Run at Windows boot (no login required)
:: /delay       = Wait before starting (stagger multiple apps)
:: /ru /rp      = Run as user (will prompt for password)
:: /rl highest  = Run with elevated privileges
schtasks /create /tn "%SERVICE_NAME%" /tr "\"%BATCH_PATH%\"" /sc onstart /delay %STARTUP_DELAY% /ru "%USERNAME%" /rp * /rl highest /f

echo       Done.
echo.

:: ============================================
:: SUCCESS
:: ============================================
echo ============================================
echo [OK] Deployment Complete!
echo.
echo Configuration:
echo   - App Name:    %APP_NAME%
echo   - Port:        %APP_PORT%
echo   - Startup:     %STARTUP_DELAY% after boot
echo   - Service:     %SERVICE_NAME%
echo.
echo Access URLs:
echo   - Local:       http://localhost:%APP_PORT%
echo   - LAN:         http://YOUR_IP:%APP_PORT%
echo.
echo Commands:
echo   - Start now:   Run_App.bat
echo   - Stop:        taskkill /f /im streamlit.exe
echo   - Uninstall:   schtasks /delete /tn "%SERVICE_NAME%" /f
echo ============================================
pause
