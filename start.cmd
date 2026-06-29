@echo off
title AI Control Center
cd /d "%~dp0"
echo ============================================
echo   AI Control Center
echo ============================================
if not exist config.json python -c "import config" 2>nul
echo Starting server on http://localhost:8900
echo (leave this window open; Ctrl+C to stop. First run? run setup.ps1 once.)
echo.
start "" http://localhost:8900
python server.py
pause
