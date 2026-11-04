@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Pop Assistant - C++ Native Core Build Script
echo ===================================================

set BIN_DIR=%~dp0bin
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

set SRC_FILES="%~dp0src\main.cpp" "%~dp0src\mascot_window.cpp"
set OUT_EXE="%BIN_DIR%\PopMascotNative.exe"

REM 1. Check for MSVC (cl.exe)
where cl.exe >nul 2>nul
if %errorlevel% equ 0 (
    echo [Build] Found MSVC Compiler: cl.exe
    cl /nologo /O2 /std:c++17 /EHsc /W3 %SRC_FILES% /link /SUBSYSTEM:WINDOWS user32.lib gdi32.lib gdiplus.lib msimg32.lib /OUT:%OUT_EXE%
    if %errorlevel% equ 0 (
        echo [Build] Successfully generated %OUT_EXE%
        exit /b 0
    )
)

REM 2. Check for MinGW / GCC (g++.exe)
where g++.exe >nul 2>nul
if %errorlevel% equ 0 (
    echo [Build] Found MinGW Compiler: g++.exe
    g++ -O3 -std=c++17 -mwindows %SRC_FILES% -lgdi32 -lgdiplus -lmsimg32 -o %OUT_EXE%
    if %errorlevel% equ 0 (
        echo [Build] Successfully generated %OUT_EXE%
        exit /b 0
    )
)

echo [Build Error] No C++ compiler (cl.exe or g++.exe) found in PATH!
echo To compile Native Core, please install Visual Studio (with C++ Desktop workload) or MinGW-w64.
echo (Python will continue to run seamlessly using in-process MiniMascotWidget fallback).
exit /b 1

