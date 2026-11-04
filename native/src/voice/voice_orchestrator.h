#pragma once

#include "audio_capture_wasapi.h"
#include "sentence_streamer.h"
#include "voice_ipc_protocol.h"
#include <string>
#include <memory>
#include <functional>
#include <atomic>
#include <mutex>
#include <vector>

enum class VoiceState {
    Idle,
    Listening,
    ProcessingSTT,
    ThinkingLLM,
    SpeakingTTS
};

inline const char* voiceStateToString(VoiceState state) {
    switch (state) {
        case VoiceState::Idle: return "IDLE";
        case VoiceState::Listening: return "LISTENING";
        case VoiceState::ProcessingSTT: return "PROCESSING_STT";
        case VoiceState::ThinkingLLM: return "THINKING_LLM";
        case VoiceState::SpeakingTTS: return "SPEAKING_TTS";
    }
    return "UNKNOWN";
}

/**
 * @brief High-performance Voice & LLM Orchestrator in C++.
 * Coordinates WASAPI mic -> ASR -> LLM token streaming -> Sentence chunker -> TTS playback.
 * Provides instant barge-in / interrupt when user speaks during TTS.
 */
class VoiceOrchestrator {
public:
    using EventCallback = std::function<void(const std::string& eventType, const std::string& jsonData)>;

    VoiceOrchestrator();
    ~VoiceOrchestrator();

    bool initialize();
    void setEventCallback(EventCallback cb) { m_eventCallback = cb; }

    // Control commands
    bool startListening();
    void stopListening();
    void processUserSpeech(const std::string& text);
    void streamLLMResponse(const std::string& prompt);
    void interrupt();
    void setState(VoiceState state);

    VoiceState getState() const { return m_state.load(); }

private:
    void onAudioData(const int16_t* pcm16, size_t sampleCount);
    void onAudioLevel(float level);
    void onSentenceChunk(const std::string& sentence);
    void emitEvent(const std::string& eventType, const std::string& jsonData);

    std::atomic<VoiceState> m_state{VoiceState::Idle};
    std::unique_ptr<WasapiAudioCapture> m_audioCapture;
    SentenceStreamer m_sentenceStreamer;
    EventCallback m_eventCallback;

    std::mutex m_mutex;
    std::atomic<bool> m_cancelRequested{false};

    // VAD / Barge-in detection
    float m_speechEnergyThreshold = 0.15f;
    int m_bargeInCounter = 0;
};

