#pragma once

#include <windows.h>
#include <mmdeviceapi.h>
#include <audioclient.h>
#include <vector>
#include <functional>
#include <atomic>
#include <thread>
#include <mutex>
#include <cstdint>

/**
 * @brief High-performance, low-latency Windows WASAPI Audio Capture.
 * Captures microphone input, resamples/converts to 16kHz 16-bit Mono PCM,
 * and calculates RMS audio amplitude for visualizer/mascot lip-sync.
 */
class WasapiAudioCapture {
public:
    using AudioDataCallback = std::function<void(const int16_t* pcm16, size_t sampleCount)>;
    using AudioLevelCallback = std::function<void(float level)>;

    WasapiAudioCapture();
    ~WasapiAudioCapture();

    bool initialize(int targetSampleRate = 16000);
    bool start();
    void stop();
    void cleanup();

    bool isCapturing() const { return m_isCapturing.load(); }

    void setAudioDataCallback(AudioDataCallback cb) { m_dataCallback = cb; }
    void setAudioLevelCallback(AudioLevelCallback cb) { m_levelCallback = cb; }

private:
    void captureLoop();
    void processAudioBuffer(BYTE* pData, UINT32 numFramesAvailable, const WAVEFORMATEX* pwfx);

    int m_targetSampleRate = 16000;
    std::atomic<bool> m_isCapturing{false};
    std::atomic<bool> m_stopRequested{false};
    std::thread m_captureThread;

    IMMDeviceEnumerator* m_pEnumerator = nullptr;
    IMMDevice* m_pDevice = nullptr;
    IAudioClient* m_pAudioClient = nullptr;
    IAudioCaptureClient* m_pCaptureClient = nullptr;
    WAVEFORMATEX* m_pwfx = nullptr;

    AudioDataCallback m_dataCallback;
    AudioLevelCallback m_levelCallback;

    std::vector<int16_t> m_conversionBuffer;
    int m_levelCounter = 0;
};

