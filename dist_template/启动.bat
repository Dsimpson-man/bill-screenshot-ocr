@echo off
rem ==========================================================
rem  本文件必须保存为 GBK(cp936) 编码 + CRLF 换行！
rem  不要改成 UTF-8，也不要加 chcp 65001：
rem  cmd.exe 在读取过程中切换代码页会解析错位，
rem  导致脚本只执行一部分，程序根本不会被调用。
rem ==========================================================
cd /d "%~dp0"
title 账单截图识别工具 - 服务窗口

set "URL=http://127.0.0.1:8848"

echo.
echo   账单截图识别工具
echo   --------------------------------------------
echo   正在启动，首次启动约需 15~30 秒。
echo   浏览器会自动打开，请不要关掉本窗口。
echo.
echo   如果浏览器没反应，手动访问：%URL%
echo   关掉本窗口即退出程序。
echo   --------------------------------------------
echo.

set "APPEXE=%~dp0账单截图识别工具\账单截图识别工具.exe"

if not exist "%APPEXE%" (
    rem 目录可能被改名了，改为按 _internal 标记查找
    set "APPEXE="
    for /d %%d in (*) do if exist "%%d\_internal" for %%f in ("%%d\*.exe") do set "APPEXE=%%~ff"
)

if not defined APPEXE (
    echo   [错误] 找不到程序文件。
    echo   请确认解压时把整个文件夹一起解压出来，
    echo   不要只单独把 exe 拖出来。
    echo.
    pause
    exit /b 1
)

for %%i in ("%APPEXE%") do cd /d "%%~dpi"
"%APPEXE%"

echo.
echo   服务已停止。
pause
