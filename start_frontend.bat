@echo off
cd /d "%~dp0frontend"
echo Starting Frontend Server on http://localhost:5500
echo Press Ctrl+C to stop the server
python -m http.server 5500
pause
