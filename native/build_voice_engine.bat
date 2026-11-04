@echo off
setlocal enabledelayedexpansion

echo ===================================================
echo   Building Pop Voice Engine (C++ Native)
echo ===================================================

set BIN_DIR=%~dp0bin
if not exist "%BIN_DIR%" mkdir "%BIN_DIR%"

where cl.exe >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [MSVC Detected] Compiling with cl.exe...
    cl.exe /nologo /O2 /W3 /EHsc /std:c++17 ^
        /I"%~dp0src" /I"%~dp0src\voice" ^
        "%~dp0src\voice\main_voice_engine.cpp" ^
        "%~dp0src\voice\voice_orchestrator.cpp" ^
        "%~dp0src\voice\audio_capture_wasapi.cpp" ^
        /link /OUT:"%BIN_DIR%\PopVoiceEngine.exe" ^
        ole32.lib oleaut32.lib uuid.lib avrt.lib winmm.lib
    
    if %ERRORLEVEL% equ 0 (
        echo [OK] PopVoiceEngine.exe built successfully at:
        echo      %BIN_DIR%\PopVoiceEngine.exe
        exit /b 0
    ) else (
        echo [ERROR] MSVC build failed.
        exit /b 1
    )
)

where g++ >nul 2>nul
if %ERRORLEVEL% equ 0 (
    echo [MinGW Detected] Compiling with g++...
    g++ -O3 -std=c++17 ^
        -I"%~dp0src" -I"%~dp0src\voice" ^
        "%~dp0src\voice\main_voice_engine.cpp" ^
        "%~dp0src\voice\voice_orchestrator.cpp" ^
        "%~dp0src\voice\audio_capture_wasapi.cpp" ^
        -lole32 -loleaut32 -luuid -lavrt -lwinmm ^
        -o "%BIN_DIR%\PopVoiceEngine.exe"
    
    if %ERRORLEVEL% equ 0 (
        echo [OK] PopVoiceEngine.exe built successfully with MinGW!
        exit /b 0
    )
)

echo [INFO] Neither cl.exe nor g++ is in system PATH.
echo [INFO] Pop Assistant will run using the seamless Python In-Process Fallback engine.
exit /b 0

