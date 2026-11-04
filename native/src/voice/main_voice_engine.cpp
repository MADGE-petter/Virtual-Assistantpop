#include "voice_orchestrator.h"
#include "voice_ipc_protocol.h"
#include <windows.h>
#include <iostream>
#include <string>
#include <thread>
#include <atomic>
#include <mutex>
#include <regex>

std::mutex g_pipeWriteMutex;
HANDLE g_hPipe = INVALID_HANDLE_VALUE;
std::atomic<bool> g_running{true};

void writePipeEvent(const std::string& eventType, const std::string& jsonData) {
    std::lock_guard<std::mutex> lock(g_pipeWriteMutex);
    if (g_hPipe == INVALID_HANDLE_VALUE) return;

    std::string line = "{\"event\":\"" + eventType + "\",\"data\":" + jsonData + "}\n";
    DWORD bytesWritten = 0;
    WriteFile(g_hPipe, line.c_str(), static_cast<DWORD>(line.length()), &bytesWritten, nullptr);
    FlushFileBuffers(g_hPipe);
}

// Simple JSON field parser for incoming commands
std::string extractJsonField(const std::string& json, const std::string& field) {
    std::regex re("\"" + field + "\"\\s*:\\s*\"([^\"]*)\"");
    std::smatch match;
    if (std::regex_search(json, match, re) && match.size() > 1) {
        return match[1].str();
    }
    return "";
}

int main(int argc, char* argv[]) {
    std::cout << "[PopVoiceEngine] Starting C++ Voice & LLM Engine..." << std::endl;

    VoiceOrchestrator orchestrator;
    if (!orchestrator.initialize()) {
        std::cerr << "[PopVoiceEngine] Orchestrator init failed." << std::endl;
        return 1;
    }

    orchestrator.setEventCallback([](const std::string& ev, const std::string& data) {
        writePipeEvent(ev, data);
    });

    while (g_running.load()) {
        std::cout << "[PopVoiceEngine] Creating Named Pipe: " << POP_VOICE_PIPE_NAME << std::endl;

        g_hPipe = CreateNamedPipeA(
            POP_VOICE_PIPE_NAME,
            PIPE_ACCESS_DUPLEX,
            PIPE_TYPE_MESSAGE | PIPE_READMODE_MESSAGE | PIPE_WAIT,
            1, // Max instances
            65536, // Out buffer
            65536, // In buffer
            0,
            nullptr
        );

        if (g_hPipe == INVALID_HANDLE_VALUE) {
            std::cerr << "[PopVoiceEngine] Failed to create pipe. Error: " << GetLastError() << std::endl;
            std::this_thread::sleep_for(std::chrono::seconds(1));
            continue;
        }

        std::cout << "[PopVoiceEngine] Waiting for Python client to connect..." << std::endl;
        BOOL connected = ConnectNamedPipe(g_hPipe, nullptr) ? TRUE : (GetLastError() == ERROR_PIPE_CONNECTED);

        if (connected) {
            std::cout << "[PopVoiceEngine] Python client connected!" << std::endl;
            writePipeEvent("engine_ready", "{\"version\": \"1.0.0\", \"status\": \"connected\"}");

            char buffer[4096];
            DWORD bytesRead = 0;

            while (g_running.load()) {
                BOOL success = ReadFile(g_hPipe, buffer, sizeof(buffer) - 1, &bytesRead, nullptr);
                if (!success || bytesRead == 0) {
                    DWORD err = GetLastError();
                    if (err == ERROR_BROKEN_PIPE || err == ERROR_PIPE_NOT_CONNECTED) {
                        std::cout << "[PopVoiceEngine] Client disconnected." << std::endl;
                    }
                    break;
                }

                buffer[bytesRead] = '\0';
                std::string msg(buffer);

                std::string cmd = extractJsonField(msg, "cmd");
                if (cmd == PopVoiceIPC::CMD_START_LISTEN) {
                    orchestrator.startListening();
                } else if (cmd == PopVoiceIPC::CMD_STOP_LISTEN) {
                    orchestrator.stopListening();
                } else if (cmd == PopVoiceIPC::CMD_INTERRUPT) {
                    orchestrator.interrupt();
                } else if (cmd == PopVoiceIPC::CMD_GENERATE) {
                    std::string prompt = extractJsonField(msg, "prompt");
                    orchestrator.streamLLMResponse(prompt);
                } else if (cmd == "set_state") {
                    std::string stateStr = extractJsonField(msg, "state");
                    if (stateStr == "SPEAKING_TTS") orchestrator.setState(VoiceState::SpeakingTTS);
                    else if (stateStr == "IDLE") orchestrator.setState(VoiceState::Idle);
                    else if (stateStr == "LISTENING") orchestrator.setState(VoiceState::Listening);
                } else if (cmd == PopVoiceIPC::CMD_QUIT) {
                    std::cout << "[PopVoiceEngine] Quit command received." << std::endl;
                    g_running.store(false);
                    break;
                }
            }
        }

        CloseHandle(g_hPipe);
        g_hPipe = INVALID_HANDLE_VALUE;
        orchestrator.stopListening();
    }

    std::cout << "[PopVoiceEngine] Shutdown complete." << std::endl;
    return 0;
}

