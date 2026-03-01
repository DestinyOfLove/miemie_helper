@echo off
chcp 65001 >nul 2>&1
title MieMie Helper

:: ---- 检查依赖 ----
uv --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 uv，请先运行 install.bat
    pause
    exit /b 1
)

if not exist ".venv" (
    echo 首次运行，正在安装依赖 ...
    uv sync
    if errorlevel 1 (
        echo [错误] 依赖安装失败，请先运行 install.bat
        pause
        exit /b 1
    )
)

if not exist "static\index.html" (
    echo 未检测到前端构建产物，正在构建 ...
    cd frontend
    call npm install && call npm run build
    cd ..
    if not exist "static\index.html" (
        echo [错误] 前端构建失败，请先运行 install.bat
        pause
        exit /b 1
    )
)

:: ---- 启动应用 ----
echo.
echo ============================================
echo   MieMie Helper 启动中 ...
echo   浏览器访问: http://localhost:4001
echo   按 Ctrl+C 停止
echo ============================================
echo.

:: 延迟 2 秒后打开浏览器
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:4001"

uv run python main.py
pause
