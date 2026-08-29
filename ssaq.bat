@echo off
title The Smart Skills Academy Qalagay - Fee Voucher System
cd /d "%~dp0"
if not exist "app.py" (
    cd /d "d:\college_voucher_system\ssaq_voucher_system"
)

echo ===============================================================
echo       The Smart Skills Academy Qalagay
echo       Fee Voucher & Student Management System
echo ===============================================================
echo.
echo Admin Contact: Rashid Zada (0347-0983567)
echo Starting Local Server at http://127.0.0.1:5000 ...
echo Opening your web browser automatically...
echo Keep this window open while using the application.
echo.
echo ===============================================================

:: Open browser after a brief 2 second delay so server starts
start "" /b cmd /c "timeout /t 2 /nobreak >nul & start http://127.0.0.1:5000"

:: Start the Flask app
python app.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo An error occurred while running the application.
    pause
)
