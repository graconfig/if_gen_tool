@echo off
chcp 65001 > nul
echo ========================================
echo   知識ベース アップロード
echo ========================================
echo.

python main.py --upload %*

if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] アップロードが失敗しました。ログを確認してください。
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [OK] アップロードが完了しました。
pause
