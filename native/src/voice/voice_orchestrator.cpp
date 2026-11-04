#include "voice_orchestrator.h"
#include <iostream>
#include <sstream>

VoiceOrchestrator::VoiceOrchestrator() {
    m_audioCapture = std::make_unique<WasapiAudioCapture>();
    m_sentenceStreamer.setCallback([this](const std::string& sentence) {
        this->onSentenceChunk(sentence);
    });
}

VoiceOrchestrator::~VoiceOrchestrator() {
    stopListening();
}

bool VoiceOrchestrator::initialize() {
    if (!m_audioCapture->initialize(16000)) {
        std::cerr << "[VoiceOrchestrator] Failed to initialize WASAPI Audio Capture." << std::endl;
        return false;
    }

    m_audioCapture->setAudioDataCallback([this](const int16_t* pcm, size_t count) {
        this->onAudioData(pcm, count);
    });

    m_audioCapture->setAudioLevelCallback([this](float level) {
        this->onAudioLevel(level);
    });

    setState(VoiceState::Idle);
    std::cout << "[VoiceOrchestrator] Initialized successfully." << std::endl;
    return true;
}

bool VoiceOrchestrator::startListening() {
    m_cancelRequested.store(false);
    if (!m_audioCapture->start()) {
        emitEvent(PopVoiceIPC::EV_ERROR, "{\"error\": \"Failed to start WASAPI capture\"}");
        return false;
    }

    setState(VoiceState::Listening);
    return true;
}

void VoiceOrchestrator::stopListening() {
    if (m_audioCapture) {
        m_audioCapture->stop();
    }
    setState(VoiceState::Idle);
}

void VoiceOrchestrator::setState(VoiceState state) {
    m_state.store(state);
    std::string json = "{\"state\": \"" + std::string(voiceStateToString(state)) + "\"}";
    emitEvent(PopVoiceIPC::EV_VOICE_STATE, json);
}

void VoiceOrchestrator::interrupt() {
    m_cancelRequested.store(true);
    std::cout << "[VoiceOrchestrator] Interrupted by user / barge-in triggered." << std::endl;
    emitEvent("interrupt", "{\"reason\": \"user_barge_in\"}");
    setState(VoiceState::Listening);
}

void VoiceOrchestrator::onAudioData(const int16_t* pcm16, size_t sampleCount) {
    if (m_state.load() != VoiceState::Listening) {
        return;
    }
    // PCM samples can be streamed to Sherpa-ONNX online recognizer stream here
}

void VoiceOrchestrator::onAudioLevel(float level) {
    // 1. Emit audio level for UI mascot animation / visualizer
    std::ostringstream ss;
    ss << "{\"level\": " << level << "}";
    emitEvent(PopVoiceIPC::EV_AUDIO_LEVEL, ss.str());

    // 2. Duplex Barge-in Detection:
    // If bot is speaking (TTS playing) and user speaks loudly for > 200ms, interrupt immediately!
    if (m_state.load() == VoiceState::SpeakingTTS) {
        if (level >= m_speechEnergyThreshold) {
            m_bargeInCounter++;
            if (m_bargeInCounter >= 4) { // ~120-150ms of sustained speech
                std::cout << "[VoiceOrchestrator] Barge-in speech detected during TTS playback! (level=" << level << ")" << std::endl;
                m_bargeInCounter = 0;
                interrupt();
            }
        } else {
            if (m_bargeInCounter > 0) m_bargeInCounter--;
        }
    } else {
        m_bargeInCounter = 0;
    }
}

void VoiceOrchestrator::processUserSpeech(const std::string& text) {
    setState(VoiceState::ProcessingSTT);
    std::string json = "{\"text\": \"" + text + "\"}";
    emitEvent(PopVoiceIPC::EV_STT_TEXT, json);
}

void VoiceOrchestrator::streamLLMResponse(const std::string& prompt) {
    m_cancelRequested.store(false);
    setState(VoiceState::ThinkingLLM);
    m_sentenceStreamer.reset();

    // Emits start of generation
    emitEvent("llm_start", "{\"prompt\": \"" + prompt + "\"}");
}

void VoiceOrchestrator::onSentenceChunk(const std::string& sentence) {
    if (m_cancelRequested.load()) return;

    // Transition to Speaking state when the first sentence is emitted for TTS
    if (m_state.load() == VoiceState::ThinkingLLM) {
        setState(VoiceState::SpeakingTTS);
    }

    std::string json = "{\"sentence\": \"" + sentence + "\"}";
    emitEvent(PopVoiceIPC::EV_LLM_SENTENCE, json);
}

void VoiceOrchestrator::emitEvent(const std::string& eventType, const std::string& jsonData) {
    if (m_eventCallback) {
        m_eventCallback(eventType, jsonData);
    }
}

