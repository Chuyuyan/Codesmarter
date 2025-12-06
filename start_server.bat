@echo off
REM Activate virtual environment and start Flask server
cd /d %~dp0
call .venv\Scripts\activate.bat
python -m backend.app
pause

