@echo off
rem ==========================================================
rem  Keep this file PLAIN ASCII with CRLF line endings.
rem  Do not put non-ASCII text here, and do not use "chcp":
rem  cmd.exe can lose its place when the code page changes
rem  mid-file, then the program is never launched at all.
rem  Chinese messages are printed by the application itself.
rem ==========================================================
cd /d "%~dp0"
title Bill Screenshot OCR - setup

echo.
echo   Preparing the Python environment...
echo   --------------------------------------------
echo   Run this only once, then use run.bat.
echo   --------------------------------------------
echo.

set PYCMD=
where py >nul 2>&1 && set PYCMD=py -3
if "%PYCMD%"=="" ( where python >nul 2>&1 && set PYCMD=python )

if "%PYCMD%"=="" (
    echo   [ERROR] Python not found.
    echo.
    echo   Please install Python 3.9 or newer from
    echo     https://www.python.org/downloads/
    echo   and tick "Add Python to PATH" during setup.
    echo.
    pause
    exit /b 1
)

echo   [1/3] Using: %PYCMD%
%PYCMD% -m venv .venv
if errorlevel 1 (
    echo   [ERROR] Failed to create the virtual environment.
    pause
    exit /b 1
)

echo   [2/3] Upgrading pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo   [3/3] Installing dependencies (first run downloads the OCR model, 1~3 min) ...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo   [ERROR] Dependency installation failed. Check your network and retry.
    pause
    exit /b 1
)

echo.
echo   --------------------------------------------
echo   Done. From now on just double-click run.bat.
echo   --------------------------------------------
echo.
pause
