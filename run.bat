@echo off
rem ==========================================================
rem  Keep this file PLAIN ASCII with CRLF line endings.
rem  Do not put non-ASCII text here, and do not use "chcp":
rem  cmd.exe can lose its place when the code page changes
rem  mid-file, then the program is never launched at all.
rem  Chinese messages are printed by the application itself.
rem ==========================================================
cd /d "%~dp0"
title Bill Screenshot OCR - service window

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo   Runtime not ready. Please run setup.bat first.
    echo.
    pause
    exit /b 1
)

echo.
echo   Starting... please keep this window open.
echo   The browser will open automatically.
echo   If it does not, open this address manually:
echo       http://127.0.0.1:8848
echo.

".venv\Scripts\python.exe" "bill_ui\bill_ui.py"

echo.
echo   Service stopped.
pause
