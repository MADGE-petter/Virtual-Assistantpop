#pragma once

#include <string>

// Pop Voice Engine IPC Protocol Constants
#define POP_VOICE_PIPE_NAME "\\\\.\\pipe\\pop_voice_ipc"

namespace PopVoiceIPC {
    // Inbound commands from Python
    constexpr const char* CMD_INIT_STT      = "init_stt";
    constexpr const char* CMD_INIT_LLM      = "init_llm";
    constexpr const char* CMD_START_LISTEN  = "start_listen";
    constexpr const char* CMD_STOP_LISTEN   = "stop_listen";
    constexpr const char* CMD_GENERATE      = "generate";
    constexpr const char* CMD_INTERRUPT     = "interrupt";
    constexpr const char* CMD_QUIT          = "quit";

    // Outbound events to Python
    constexpr const char* EV_STT_TEXT       = "stt_text";
    constexpr const char* EV_LLM_CHUNK      = "llm_chunk";
    constexpr const char* EV_LLM_SENTENCE   = "llm_sentence";
    constexpr const char* EV_LLM_DONE       = "llm_done";
    constexpr const char* EV_VOICE_STATE    = "voice_state";
    constexpr const char* EV_ERROR          = "error";
    constexpr const char* EV_AUDIO_LEVEL    = "audio_level";
}

