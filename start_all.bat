@echo off
echo ============================================
echo AI Voyage Estimation System - Quick Start
echo ============================================
echo.
echo Starting Backend Server...
start "Backend - Port 8000" cmd /k "%~dp0start_backend.bat"
timeout /t 3 /nobreak > nul

echo Starting Frontend Server...
start "Frontend - Port 5500" cmd /k "%~dp0start_frontend.bat"
timeout /t 2 /nobreak > nul

echo.
echo ============================================
echo Servers Started Successfully!
echo ============================================
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:5500
echo API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Opening frontend in your default browser...
timeout /t 2 /nobreak > nul
start http://localhost:5500
echo.
echo Both servers are running in separate windows.
echo Close those windows to stop the servers.
echo.
pause
