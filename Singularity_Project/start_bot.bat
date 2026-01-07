@echo off
echo Starting Singularity Telegram Bot...
cd /d "%~dp0"
call venv\Scripts\activate.bat
python telegram_bridge.py
pause
















