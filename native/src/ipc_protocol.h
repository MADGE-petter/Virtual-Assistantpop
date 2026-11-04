#pragma once

#include <string>

// Pop Mascot IPC Protocol Constants
#define POP_MASCOT_PIPE_NAME "\\\\.\\pipe\\pop_mascot_ipc"

namespace PopIPC {
    // Inbound commands from Python
    constexpr const char* CMD_SET_VOICE_STATE = "set_voice_state";
    constexpr const char* CMD_SET_CHARACTER   = "set_character";
    constexpr const char* CMD_SET_MUSIC       = "set_music";
    constexpr const char* CMD_WAKE_UP         = "wake_up";
    constexpr const char* CMD_SET_VISIBLE     = "set_visible";
    constexpr const char* CMD_MOVE            = "move";
    constexpr const char* CMD_RAISE           = "raise";
    constexpr const char* CMD_QUIT            = "quit";

    // Outbound events to Python
    constexpr const char* EV_TOGGLE_MAIN_WIN  = "toggle_main_window";
    constexpr const char* EV_TOGGLE_MIC       = "toggle_mic";
    constexpr const char* EV_OPEN_COLLECTION  = "open_collection";
    constexpr const char* EV_POS_CHANGED      = "position_changed";
}

