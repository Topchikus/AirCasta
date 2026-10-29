@echo off
chcp 65001 >nul
title AirCasta - AirPlay Receiver & DropCast
cd /d "%~dp0"

if exist "%~dp0bin\runtime\bin" (
    set "PATH=%~dp0bin\runtime\bin;%PATH%"
    set "GST_PLUGIN_PATH=%~dp0bin\runtime\lib\gstreamer-1.0"
    set "GST_PLUGIN_SYSTEM_PATH=%~dp0bin\runtime\lib\gstreamer-1.0"
) else if exist "C:\msys64\ucrt64\bin" (
    set "PATH=C:\msys64\ucrt64\bin;%PATH%"
)

set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py"
if not defined PY_CMD (
    where python >nul 2>&1 && set "PY_CMD=python"
)

if not defined PY_CMD (
    echo.
    echo ========================================================
    echo  [ОШИБКА] Python не найден на этом компьютере!
    echo ========================================================
    echo  Для запуска AirCasta установите Python 3:
    echo  - Скачайте с официального сайта: https://www.python.org/downloads/
    echo  - Или выполните в консоли: winget install Python.Python.3.13
    echo.
    pause
    exit /b 1
)

%PY_CMD% -c "import PyQt6, zeroconf, cryptography, aiohttp, qrcode, psutil" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [Установка] Первый запуск: автоматическая установка необходимых модулей...
    %PY_CMD% -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [ОШИБКА] Не удалось установить зависимости. Проверьте интернет-соединение.
        pause
        exit /b 1
    )
)

%PY_CMD% main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Приложение завершило работу с ошибкой.
    pause
)
