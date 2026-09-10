@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 账单截图识别工具 - 服务窗口

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo   还没有准备好运行环境。
    echo   请先双击同目录的 setup.bat 安装依赖。
    echo.
    pause
    exit /b 1
)

echo.
echo   账单截图识别工具
echo   --------------------------------------------
echo   浏览器会自动打开，请稍等几秒。
echo   如果一直没反应，手动访问：http://127.0.0.1:8848
echo.
echo   本窗口是程序本体，使用期间不要关闭。
echo   关掉本窗口 = 退出程序。
echo   --------------------------------------------
echo.

".venv\Scripts\python.exe" "bill_ui\bill_ui.py"

echo.
echo   服务已停止。
pause
