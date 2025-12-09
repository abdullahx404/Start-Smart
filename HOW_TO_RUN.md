# How to Run Start-Smart Application

This guide will help you run both the backend and frontend of the Start-Smart application.

## Prerequisites
- ✅ PostgreSQL installed and running (default port: 5432)
- ✅ Database `startsmart_dev` created
- ✅ Python 3.13 installed
- ✅ Flutter SDK installed
- ✅ Environment variables configured in `.env` files
- ✅ Google Maps API Key configured

---

## Application Features

### 🔍 AI-Powered Location Intelligence
The application provides intelligent business location analysis for entrepreneurs in Karachi:

1. **Business Type Selection** - Search and select from available business types (Gym, Cafe)
2. **Location Selection** - Default location is Clifton, Karachi. Tap on the map to select any location within Clifton
3. **Radius Selection** - Choose analysis radius: 300m, 500m, 750m, or 1000m
4. **Analysis Mode**:
   - **Fast Mode** (~1-2 seconds): Quick rule-based analysis
   - **AI Mode** (~5-15 seconds): Deep LLM-powered insights with detailed reasoning

### 📊 Analysis Results
- Score breakdown (Overall, Demand, Supply Gap, Confidence)
- Key factors affecting the location
- AI-generated insights and recommendations
- Alternative business suggestions

---

## Step-by-Step Guide

### **Step 1: Start PostgreSQL Service**
Make sure PostgreSQL is running on your system.

**Windows:**
```powershell
# PostgreSQL should start automatically with Windows
# Or check in Services (services.msc) for "postgresql-x64-XX"
```

---

### **Step 2: Start the Backend Server**

#### Open PowerShell/Terminal and run:

```powershell
# Navigate to backend directory
cd "c:\Users\Abdullah\OneDrive - Higher Education Commission\Semester 5\SE322 SDA\ProjectETC\Start-Smart\backend"

# Run the backend server
C:/Users/Abdullah/AppData/Local/Programs/Python/Python313/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using WatchFiles
✅ Database connection verified
✅ StartSmart API ready!
INFO:     Application startup complete.
```

**Backend is now running at:** http://127.0.0.1:8000

**API Documentation:** http://127.0.0.1:8000/docs

---

### **Step 3: Start the Frontend (Flutter App)**

#### Open a NEW PowerShell/Terminal window and run:

```powershell
# Navigate to frontend directory
cd "c:\Users\Abdullah\OneDrive - Higher Education Commission\Semester 5\SE322 SDA\ProjectETC\Start-Smart\frontend"

# Run the Flutter app on Chrome
flutter run -d chrome
```

**Expected Output:**
```
Launching lib\main.dart on Chrome in debug mode...
Waiting for connection from debug service on Chrome...

Flutter run key commands.
r Hot reload.
R Hot restart.
```

**Frontend will automatically open in Chrome browser.**

---

## Quick Commands Reference

### To Stop Services:

**Stop Backend (in backend terminal):**
```powershell
Ctrl + C
```

**Stop Frontend (in frontend terminal):**
```powershell
q  # Press 'q' to quit
```

**Or kill all processes:**
```powershell
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*dart*"} | Stop-Process -Force
```

---

### Hot Reload (Frontend Only):
When you make changes to Flutter code:
- Press **`r`** for hot reload (quick, preserves state)
- Press **`R`** for hot restart (full restart)

---

## Troubleshooting

### Backend Issues:

**Problem:** "Database connection failed"
```powershell
# Solution: Check PostgreSQL is running and credentials in .env file
# Verify with:
psql -U postgres -d startsmart_dev
```

**Problem:** "Port 8000 already in use"
```powershell
# Solution: Kill existing Python processes
Get-Process python | Stop-Process -Force
```

### Frontend Issues:

**Problem:** "Network error: ClientException"
- **Solution:** Make sure backend is running first (Step 2)
- Check backend URL in `frontend/lib/utils/constants.dart` is `http://localhost:8000/api/v1`

**Problem:** "Flutter failed to delete build directory"
```powershell
# Solution: Clean and rebuild
flutter clean
flutter run -d chrome
```

---

## Running in Production Mode

### Backend:
```powershell
# Without auto-reload
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000
```

### Frontend:
```powershell
# Build for web
flutter build web

# Serve the build
cd build\web
python -m http.server 8080
```

---

## Environment Variables

### Backend `.env` file location:
`Start-Smart/backend/.env`

Required variables:
```env
DATABASE_URL=postgresql://postgres:YOUR_PASSWORD@localhost:5432/startsmart_dev
GOOGLE_PLACES_API_KEY=your_key_here
ENVIRONMENT=development
LOG_LEVEL=INFO
```

---

## Ports Used

| Service | Port | URL |
|---------|------|-----|
| Backend API | 8000 | http://127.0.0.1:8000 |
| Frontend (Dev) | Auto (50000+) | Opened by Flutter |
| PostgreSQL | 5432 | localhost:5432 |

---

## Quick Start (All in One)

### Open Terminal 1 - Backend:
```powershell
cd "c:\Users\Abdullah\OneDrive - Higher Education Commission\Semester 5\SE322 SDA\ProjectETC\Start-Smart\backend"
C:/Users/Abdullah/AppData/Local/Programs/Python/Python313/python.exe -m uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Open Terminal 2 - Frontend:
```powershell
cd "c:\Users\Abdullah\OneDrive - Higher Education Commission\Semester 5\SE322 SDA\ProjectETC\Start-Smart\frontend"
flutter run -d chrome
```

**Done!** 🚀 Both services are now running.

---

## Using the Application

### Step 1: Click "AI-Powered Analysis"
From the landing screen, tap the main button to start location analysis.

### Step 2: Select Business Type
Type in the search bar (e.g., "Gym" or "Cafe"). The predictive search will show available options. Select your desired business type.

### Step 3: Select Location
- Default location is **Clifton, Karachi**
- Tap anywhere on the map within Clifton to select a different location
- Use the building icon button to reset to Clifton center

### Step 4: Configure Analysis
- **Mode**: Toggle between Fast (quick) and AI (detailed) analysis
- **Radius**: Select analysis radius (300m - 1000m)

### Step 5: Analyze
Click "Analyze with AI" or "Quick Analysis" to get results.

### Step 6: View Results
- See overall score and breakdown
- Review key factors
- Read AI insights (in AI mode)
- Consider alternative recommendations

---

## Additional Resources

- **API Documentation:** http://127.0.0.1:8000/docs
- **Redoc API Docs:** http://127.0.0.1:8000/redoc
- **Backend Logs:** Check terminal running backend
- **Flutter DevTools:** Shown in frontend terminal output

---

**Last Updated:** December 6, 2025
