@echo off
setlocal enabledelayedexpansion
title AirCasta - Build Backend (Windows)
echo ======================================================
echo    AirCasta - Сборка нативного AirPlay-движка Windows
echo ======================================================

set "PROJECT_ROOT=%~dp0\.."
set "BIN_DIR=%PROJECT_ROOT%\bin"
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

if not exist "C:\msys64\usr\bin\bash.exe" (
    echo [ОШИБКА] MSYS2 не найден в C:\msys64.
    echo Установите MSYS2 через winget: winget install MSYS2.MSYS2
    pause
    exit /b 1
)

echo [1/3] Проверка и установка пакетов MSYS2...
C:\msys64\usr\bin\bash.exe -lc "pacman -S --needed --noconfirm mingw-w64-ucrt-x86_64-gcc mingw-w64-ucrt-x86_64-cmake mingw-w64-ucrt-x86_64-ninja mingw-w64-ucrt-x86_64-openssl mingw-w64-ucrt-x86_64-libplist mingw-w64-ucrt-x86_64-gstreamer mingw-w64-ucrt-x86_64-gst-plugins-base mingw-w64-ucrt-x86_64-gst-plugins-good mingw-w64-ucrt-x86_64-gst-plugins-bad mingw-w64-ucrt-x86_64-gst-libav"

echo [2/3] Компиляция UxPlay через CMake и Ninja...
set "TEMP_SRC=C:\Users\%USERNAME%\AppData\Local\Temp\UxPlay"
if not exist "%TEMP_SRC%" (
    git clone --depth 1 https://github.com/FDH2/UxPlay.git "%TEMP_SRC%"
)

C:\msys64\usr\bin\bash.exe -lc "export PATH=/ucrt64/bin:/usr/bin:$PATH; cd /c/Users/$USER/AppData/Local/Temp/UxPlay && mkdir -p build && cd build && cmake .. -G Ninja -DCMAKE_BUILD_TYPE=Release && ninja"

echo [3/3] Копирование исполняемого файла в bin/...
copy /Y "%TEMP_SRC%\build\uxplay.exe" "%BIN_DIR%\uxplay.exe"

if exist "%BIN_DIR%\uxplay.exe" (
    echo [УСПЕХ] Файл %BIN_DIR%\uxplay.exe успешно собран и готов к работе!
) else (
    echo [ОШИБКА] Сборка не удалась.
)

pause
