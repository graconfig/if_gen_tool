@echo off
chcp 65001 > nul
echo ========================================
echo   SAP IF Design Tool - GUI
echo ========================================
echo.

set SCRIPT_DIR=%~dp0

if exist "%SCRIPT_DIR%venv\Scripts\python.exe" (
    set PYTHON="%SCRIPT_DIR%venv\Scripts\python.exe"
) else if exist "%SCRIPT_DIR%.venv\Scripts\python.exe" (
    set PYTHON="%SCRIPT_DIR%.venv\Scripts\python.exe"
) else (
    set PYTHON=python
)

%PYTHON% "%SCRIPT_DIR%gui_main.py"

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] GUI の起動に失敗しました。
    pause
    exit /b %ERRORLEVEL%
)
