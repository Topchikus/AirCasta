@echo off
chcp 65001 >nul
title AirCasta - AirPlay Receiver
cd /d "%~dp0"

if exist "C:\msys64\ucrt64\bin" (
    set "PATH=C:\msys64\ucrt64\bin;%PATH%"
)

where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py main.py
) else (
    python main.py
)
pause
