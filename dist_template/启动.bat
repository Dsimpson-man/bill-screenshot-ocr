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

set "URL=http://127.0.0.1:8848"

echo.
echo   Starting... please keep this window open.
echo   The browser will open automatically.
echo   If it does not, open this address manually:
echo       %URL%
echo.

rem Locate the program: find the subfolder that contains _internal.
set "APPEXE="
for /d %%d in (*) do if exist "%%d\_internal" for %%f in ("%%d\*.exe") do set "APPEXE=%%~ff"

if not defined APPEXE (
    echo   [ERROR] Program files not found.
    echo.
    echo   Please EXTRACT the whole zip into a folder first,
    echo   then run this file from inside that folder.
    echo   Do not run it from inside the zip viewer, and do not
    echo   move this file away from its folder.
    echo.
    pause
    exit /b 1
)

for %%i in ("%APPEXE%") do cd /d "%%~dpi"
"%APPEXE%"

echo.
echo   Service stopped.
pause
