@echo off
chcp 65001 > nul
echo === IF Gen Tool - Build EXE ===
cd /d "%~dp0"

call venv\Scripts\activate.bat

echo [1/3] Cleaning previous build...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul

echo [2/3] Running PyInstaller...
pyinstaller if_gen_tool.spec

if %ERRORLEVEL% neq 0 (
    echo BUILD FAILED.
    pause
    exit /b 1
)

echo [3/3] Done!
echo Output: dist\if_gen_tool.exe
dir dist\if_gen_tool.exe
pause
