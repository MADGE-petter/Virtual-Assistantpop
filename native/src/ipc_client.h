#pragma once

#include <windows.h>
#include <string>
#include <functional>
#include <thread>
#include <atomic>
#include <iostream>

class IpcClient {
public:
    using MessageCallback = std::function<void(const std::string&)>;

    IpcClient(const std::string& pipeName = "\\\\.\\pipe\\pop_mascot_ipc")
        : m_pipeName(pipeName), m_pipe(INVALID_HANDLE_VALUE), m_running(false) {}

    ~IpcClient() {
        disconnect();
    }

    bool connectToPipe(int maxRetries = 30, int retryDelayMs = 200) {
        for (int i = 0; i < maxRetries; ++i) {
            m_pipe = CreateFileA(
                m_pipeName.c_str(),
                GENERIC_READ | GENERIC_WRITE,
                0,
                NULL,
                OPEN_EXISTING,
                0,
                NULL
            );

            if (m_pipe != INVALID_HANDLE_VALUE) {
                DWORD mode = PIPE_READMODE_BYTE;
                SetNamedPipeHandleState(m_pipe, &mode, NULL, NULL);
                m_running = true;
                m_readerThread = std::thread(&IpcClient::readLoop, this);
                return true;
            }

            Sleep(retryDelayMs);
        }
        return false;
    }

    void disconnect() {
        m_running = false;
        if (m_pipe != INVALID_HANDLE_VALUE) {
            CloseHandle(m_pipe);
            m_pipe = INVALID_HANDLE_VALUE;
        }
        if (m_readerThread.joinable()) {
            m_readerThread.join();
        }
    }

    bool sendMessage(const std::string& jsonMsg) {
        if (m_pipe == INVALID_HANDLE_VALUE) return false;
        std::string payload = jsonMsg + "\n";
        DWORD bytesWritten = 0;
        BOOL ok = WriteFile(m_pipe, payload.c_str(), (DWORD)payload.length(), &bytesWritten, NULL);
        return ok && (bytesWritten == payload.length());
    }

    void onMessage(MessageCallback cb) {
        m_callback = cb;
    }

    bool isConnected() const {
        return m_pipe != INVALID_HANDLE_VALUE;
    }

private:
    void readLoop() {
        char buffer[4096];
        std::string accumulated;

        while (m_running && m_pipe != INVALID_HANDLE_VALUE) {
            DWORD bytesRead = 0;
            BOOL success = ReadFile(m_pipe, buffer, sizeof(buffer) - 1, &bytesRead, NULL);
            if (!success || bytesRead == 0) {
                break;
            }

            buffer[bytesRead] = '\0';
            accumulated += buffer;

            size_t pos;
            while ((pos = accumulated.find('\n')) != std::string::npos) {
                std::string line = accumulated.substr(0, pos);
                accumulated.erase(0, pos + 1);

                // Trim line
                while (!line.empty() && (line.back() == '\r' || line.back() == ' ')) line.pop_back();
                if (!line.empty() && m_callback) {
                    m_callback(line);
                }
            }
        }
    }

    std::string m_pipeName;
    HANDLE m_pipe;
    std::atomic<bool> m_running;
    std::thread m_readerThread;
    MessageCallback m_callback;
};

