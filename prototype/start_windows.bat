@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 app.py --port 8766
) else (
  python app.py --port 8766
)
pause
