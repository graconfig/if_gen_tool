@echo off
chcp 65001 > nul
echo ========================================
echo   SAP IF マッピング処理
echo ========================================
echo.

python main.py %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] 処理が失敗しました。ログを確認してください。
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] 処理が完了しました。
pause
