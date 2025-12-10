@echo off
cd /d "%~dp0"
call .venv\Scripts\activate.bat
echo Starting Backend Server on http://localhost:8000
echo API Documentation: http://localhost:8000/docs
echo Press Ctrl+C to stop the server
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
pause
