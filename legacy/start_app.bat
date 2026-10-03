@echo off
echo =========================================================================
echo  TRAFFIC CONTROL ROOM // AUTO ACCIDENT DETECTION SYSTEM (FULL STACK)
echo =========================================================================
echo Starting FastAPI Backend on http://127.0.0.1:8000 ...
start "Backend Server" cmd /k "C:\v\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Starting React + Vite HUD Frontend on http://localhost:3000 ...
start "Frontend Console" cmd /k "cd frontend && npm run dev"

echo.
echo System Initialized!
echo Backend API Docs: http://127.0.0.1:8000/docs
echo Frontend Console: http://localhost:3000
echo Demo Login: Username 'command' | Password 'control123'
echo =========================================================================
