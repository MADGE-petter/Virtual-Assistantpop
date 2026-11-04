cmake_minimum_required(VERSION 3.16)
project(PopNativeCore LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# ==============================================================================
# Target 1: PopMascotNative (Lightweight Direct2D/GDI+ Window)
# ==============================================================================
set(MASCOT_SOURCES
    src/main.cpp
    src/mascot_window.cpp
    src/mascot_window.h
    src/ipc_client.h
    src/ipc_protocol.h
)

add_executable(PopMascotNative WIN32 ${MASCOT_SOURCES})

target_link_libraries(PopMascotNative PRIVATE
    user32
    gdi32
    gdiplus
    msimg32
)

set_target_properties(PopMascotNative PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin"
)

# ==============================================================================
# Target 2: PopVoiceEngine (WASAPI Audio Capture, Sentence Streaming & IPC)
# ==============================================================================
set(VOICE_SOURCES
    src/voice/main_voice_engine.cpp
    src/voice/voice_orchestrator.cpp
    src/voice/voice_orchestrator.h
    src/voice/audio_capture_wasapi.cpp
    src/voice/audio_capture_wasapi.h
    src/voice/sentence_streamer.h
    src/voice/voice_ipc_protocol.h
)

add_executable(PopVoiceEngine ${VOICE_SOURCES})

target_link_libraries(PopVoiceEngine PRIVATE
    ole32
    oleaut32
    uuid
    avrt
    winmm
)

set_target_properties(PopVoiceEngine PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/bin"
)
