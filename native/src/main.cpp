#include <windows.h>
#include <iostream>
#include "ipc_client.h"
#include "mascot_window.h"

// Simple JSON field parser helper without heavy external dependencies
std::string extractJsonField(const std::string& json, const std::string& key) {
    std::string needle = "\"" + key + "\":";
    size_t pos = json.find(needle);
    if (pos == std::string::npos) return "";

    pos += needle.length();
    while (pos < json.length() && (json[pos] == ' ' || json[pos] == '\"')) pos++;

    size_t endPos = pos;
    while (endPos < json.length() && json[endPos] != '\"' && json[endPos] != ',' && json[endPos] != '}') {
        endPos++;
    }

    return json.substr(pos, endPos - pos);
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    // Determine IPC pipe name
    std::string pipeName = "\\\\.\\pipe\\pop_mascot_ipc";
    std::string cmdLine(lpCmdLine);
    size_t pipeArg = cmdLine.find("--pipe=");
    if (pipeArg != std::string::npos) {
        std::string customPipe = cmdLine.substr(pipeArg + 7);
        size_t space = customPipe.find(' ');
        if (space != std::string::npos) customPipe = customPipe.substr(0, space);
        if (!customPipe.empty()) {
            pipeName = "\\\\.\\pipe\\" + customPipe;
        }
    }

    IpcClient ipc(pipeName);
    MascotWindow mascot(hInstance, ipc);

    // Initial position bottom-right on default monitor
    RECT workArea;
    SystemParametersInfoA(SPI_GETWORKAREA, 0, &workArea, 0);
    int initX = workArea.right - 150;
    int initY = workArea.bottom - 150;

    if (!mascot.create(initX, initY, 120)) {
        return 1;
    }

    // Connect to Python IPC bus in background
    ipc.onMessage([&](const std::string& msg) {
        std::string cmd = extractJsonField(msg, "cmd");
        if (cmd == "set_voice_state") {
            std::string state = extractJsonField(msg, "state");
            mascot.setVoiceState(state);
        } else if (cmd == "set_character") {
            std::string cid = extractJsonField(msg, "id");
            std::string skinDir = extractJsonField(msg, "skin_dir");
            mascot.setCharacter(cid, skinDir);
        } else if (cmd == "set_music") {
            std::string playing = extractJsonField(msg, "playing");
            mascot.setMusicMode(playing == "true" || playing == "1");
        } else if (cmd == "wake_up") {
            mascot.wakeUp();
        } else if (cmd == "set_visible") {
            std::string vis = extractJsonField(msg, "visible");
            mascot.setVisible(vis == "true" || vis == "1");
        } else if (cmd == "move") {
            int x = atoi(extractJsonField(msg, "x").c_str());
            int y = atoi(extractJsonField(msg, "y").c_str());
            mascot.moveTo(x, y);
        } else if (cmd == "quit") {
            PostQuitMessage(0);
        }
    });

    // Try connecting to IPC
    std::thread([&]() {
        ipc.connectToPipe();
    }).detach();

    mascot.setVisible(true);
    mascot.runMessageLoop();

    return 0;
}

