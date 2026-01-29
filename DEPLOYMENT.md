# Windows Headless Deployment Guide

Deploy Streamlit apps as background services on Windows that start automatically at boot.

---

## Quick Start

1. **Edit Configuration** in both `.bat` files:
   ```batch
   set APP_NAME=Your App Name
   set APP_PORT=8501
   ```

2. **Run `Deploy_Server.bat` as Administrator** (one time)

3. **Done!** App starts automatically on every boot.

---

## File Structure

```
Your App/
├── app.py              # Main Streamlit app
├── requirements.txt    # Python dependencies
├── Run_App.bat         # Runner (starts the app)
└── Deploy_Server.bat   # Installer (one-time setup)
```

---

## Configuration Reference

### Run_App.bat
```batch
set APP_NAME=Footfall Tracker    :: Display name
set APP_PORT=8501                :: Network port
set APP_FILE=app.py              :: Entry point
```

### Deploy_Server.bat
```batch
set APP_NAME=Footfall Tracker    :: Display name (for firewall rule)
set SERVICE_NAME=FootfallService :: Windows Task Scheduler name
set APP_PORT=8501                :: Must match Run_App.bat
set STARTUP_DELAY=0001:00        :: Delay after boot (MM:SS)
```

---

## Running Multiple Apps

### Port Assignment
Each app needs a unique port:

| App | Port | Startup Delay |
|-----|------|---------------|
| App 1 | 8501 | 0001:00 (1 min) |
| App 2 | 8502 | 0002:00 (2 min) |
| App 3 | 8503 | 0003:00 (3 min) |

### Why Stagger Delays?
- Prevents CPU spike at boot
- Avoids database lock conflicts
- Gives each app time to fully initialize

### Resource Guide

| Server RAM | Recommended Max Apps |
|------------|---------------------|
| 4 GB | 2-3 apps |
| 8 GB | 5-8 apps |
| 16 GB | 10+ apps |

Each idle Streamlit app uses ~100-300 MB RAM.

---

## Commands

### Start App Manually
```cmd
Run_App.bat
```

### Stop App
```cmd
taskkill /f /im streamlit.exe
```

### Uninstall Service
```cmd
schtasks /delete /tn "YourServiceName" /f
```

### View Running Tasks
```cmd
schtasks /query /tn "YourServiceName"
```

### View Firewall Rules
```cmd
netsh advfirewall firewall show rule name="Your App Name"
```

---

## Troubleshooting

### "Port already in use"
Another app is using the same port. Change `APP_PORT` to a different number.

### App doesn't start at boot
1. Check Task Scheduler: `taskschd.msc`
2. Find your service and check "Last Run Result"
3. Ensure the batch file path is correct

### Can't access from other computers
1. Check firewall rule was created
2. Use `ipconfig` to find your IP address
3. Access via `http://YOUR_IP:PORT`

### Python not found
Install Python and ensure it's in your PATH:
```cmd
python --version
```

---

## Best Practices Checklist

- [ ] Each app has a unique port number
- [ ] Each app has a unique service name
- [ ] Startup delays are staggered (1 min apart)
- [ ] `APP_PORT` matches in both `.bat` files
- [ ] Run `Deploy_Server.bat` as Administrator
- [ ] Test with `Run_App.bat` before deploying

---

## Template for New Apps

Copy these files to your new app folder and edit the configuration:

**Run_App.bat** - Change lines 8-10:
```batch
set APP_NAME=My New App
set APP_PORT=8502
set APP_FILE=app.py
```

**Deploy_Server.bat** - Change lines 8-11:
```batch
set APP_NAME=My New App
set SERVICE_NAME=MyNewAppService
set APP_PORT=8502
set STARTUP_DELAY=0002:00
```
