@echo off
chcp 65001 >nul 2>&1
title MieMie Helper - 安装

echo ============================================
echo   MieMie Helper 安装程序
echo ============================================
echo.

:: ---- 检查 Python ----
echo [1/5] 检查 Python ...
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.13+
    echo        下载地址: https://www.python.org/downloads/
    echo        安装时务必勾选 "Add Python to PATH"
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do echo        已安装 Python %%v

:: ---- 检查 uv ----
echo.
echo [2/5] 检查 uv 包管理器 ...
uv --version >nul 2>&1
if errorlevel 1 (
    echo        未找到 uv，正在安装 ...
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    if errorlevel 1 (
        echo [错误] uv 安装失败，请手动安装
        echo        https://docs.astral.sh/uv/getting-started/installation/
        pause
        exit /b 1
    )
    echo        uv 安装完成，请关闭此窗口后重新打开 install.bat
    pause
    exit /b 0
)
for /f "tokens=*" %%v in ('uv --version 2^>^&1') do echo        已安装 %%v

:: ---- 检查 Node.js ----
echo.
echo [3/5] 检查 Node.js ...
node --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Node.js，请先安装 Node.js LTS
    echo        下载地址: https://nodejs.org/
    pause
    exit /b 1
)
for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo        已安装 Node.js %%v

:: ---- 安装 Python 依赖 ----
echo.
echo [4/5] 安装 Python 依赖 ...
uv sync
if errorlevel 1 (
    echo [错误] Python 依赖安装失败
    pause
    exit /b 1
)
echo        Python 依赖安装完成

:: ---- 构建前端 ----
echo.
echo [5/5] 构建前端 ...
if not exist "frontend\package.json" (
    echo [错误] 未找到 frontend/package.json
    pause
    exit /b 1
)
cd frontend
call npm install
if errorlevel 1 (
    echo [错误] npm install 失败
    cd ..
    pause
    exit /b 1
)
call npm run build
if errorlevel 1 (
    echo [错误] 前端构建失败
    cd ..
    pause
    exit /b 1
)
cd ..
echo        前端构建完成

:: ---- 完成 ----
echo.
echo ============================================
echo   安装完成！
echo   双击 start.bat 启动应用
echo ============================================
pause
