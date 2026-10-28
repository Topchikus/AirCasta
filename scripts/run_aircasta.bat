@echo off
title AirCasta - AirPlay Receiver
cd /d "%~dp0\.."

:: Add MSYS2 UCRT64 to PATH for runtime GStreamer and SSL DLLs
if exist "C:\msys64\ucrt64\bin" (
    set "PATH=C:\msys64\ucrt64\bin;%PATH%"
)

:: Run using Python launcher or python in PATH
where py >nul 2>&1
if %ERRORLEVEL% equ 0 (
    py main.py
) else (
    python main.py
)
pause
