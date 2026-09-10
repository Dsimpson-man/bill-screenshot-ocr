@echo off
chcp 65001 >nul
cd /d "%~dp0"
title 账单截图识别工具 - 安装依赖

echo.
echo   账单截图识别工具 - 环境准备
echo   --------------------------------------------
echo   只需执行一次，之后直接双击 run.bat
echo   --------------------------------------------
echo.

set PYCMD=
where py >nul 2>&1 && set PYCMD=py -3
if "%PYCMD%"=="" ( where python >nul 2>&1 && set PYCMD=python )

if "%PYCMD%"=="" (
    echo   [错误] 没有找到 Python。
    echo.
    echo   请先安装 Python 3.9 或更高版本：
    echo     https://www.python.org/downloads/
    echo   安装时务必勾选 "Add Python to PATH"。
    echo.
    pause
    exit /b 1
)

echo   [1/3] 使用 Python 命令：%PYCMD%
%PYCMD% -m venv .venv
if errorlevel 1 (
    echo   [错误] 创建虚拟环境失败。
    pause
    exit /b 1
)

echo   [2/3] 升级 pip ...
".venv\Scripts\python.exe" -m pip install --upgrade pip

echo   [3/3] 安装依赖，首次约需 1~3 分钟（会下载 OCR 模型）...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo   [错误] 依赖安装失败，请检查网络后重新运行本脚本。
    pause
    exit /b 1
)

echo.
echo   --------------------------------------------
echo   安装完成！以后双击 run.bat 启动即可。
echo   --------------------------------------------
echo.
pause
