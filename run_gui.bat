@echo off
chcp 65001 > nul
cd /d "%~dp0"
venv\Scripts\python.exe gui_main.py
if %ERRORLEVEL% neq 0 pause
