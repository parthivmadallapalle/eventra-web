@echo off
title EVENTRA - Unified Platform Launcher
cls
echo =====================================================================
echo                      EVENTRA UNIFIED PLATFORM
echo     Intelligent Event Management, Sponsorship & Crowd Safety
echo =====================================================================
echo.
echo  All Eventra files are combined into this directory:
echo   - eventra.c    : C Core Engine (Module 1 Auth & RBAC)
echo   - eventra.exe  : Win64 Compiled Binary
echo   - users.dat    : Persistent Binary Database
echo   - index.html   : Standalone Unified Web Application (All Modules)
echo   - styles.css   : Glassmorphic Modern Dark Design System
echo   - app.js       : Client-side Engine with QR Canvas & Gate Scanner
echo.
echo  Available Options:
echo   [1] Launch Eventra Web Platform in Default Browser (Local Server)
echo   [2] Open Eventra Web Single-File (index.html directly)
echo   [3] Run Eventra C Terminal Console (eventra.exe)
echo   [4] Recompile Eventra C Core (gcc eventra.c -o eventra.exe)
echo   [5] Exit
echo.
set /p opt="Enter choice [1-5]: "

if "%opt%"=="1" (
    echo.
    echo Starting Eventra PostgreSQL Server on http://localhost:3000 ...
    start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:3000/"
    node "%~dp0server/server.js"
) else if "%opt%"=="2" (
    echo.
    echo Starting Eventra Backend Server in background and launching Web App...
    start /b "" node "%~dp0server/server.js"
    timeout /t 2 /nobreak >nul
    start "" "%~dp0index.html"
) else if "%opt%"=="3" (
    echo.
    echo Running Eventra C CLI Application...
    "%~dp0eventra.exe"
    pause
) else if "%opt%"=="4" (
    echo.
    echo Compiling eventra.c with GCC...
    gcc -Wall -O2 "%~dp0eventra.c" -o "%~dp0eventra.exe"
    if %errorlevel% equ 0 (
        echo Compilation succeeded! Executable eventra.exe updated.
    ) else (
        echo Compilation failed! Please verify GCC is installed and in PATH.
    )
    pause
) else (
    exit /b 0
)
