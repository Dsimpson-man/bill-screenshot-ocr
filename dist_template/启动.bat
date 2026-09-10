@echo off
chcp 65001 >nul
title 账单截图识别工具 - 服务窗口
cd /d "%~dp0账单截图识别工具"

set PORT=8848
set URL=http://127.0.0.1:%PORT%

echo.
echo   账单截图识别工具
echo   --------------------------------------------
echo   正在启动，首次启动需要解压，约 15~30 秒。
echo   浏览器会自动打开，请不要关掉本窗口。
echo.
echo   如果浏览器没反应，手动访问：%URL%
echo   关掉本窗口即退出程序。
echo   --------------------------------------------
echo.

if not exist "账单截图识别工具.exe" (
    echo   [错误] 找不到「账单截图识别工具.exe」。
    echo   请确认解压时把整个文件夹一起解压出来，
    echo   不要只单独把 exe 拖出来。
    echo.
    pause
    exit /b 1
)

账单截图识别工具.exe

echo.
echo   服务已停止。
pause
