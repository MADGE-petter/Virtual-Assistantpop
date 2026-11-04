#include "audio_capture_wasapi.h"
#include <cmath>
#include <iostream>

#pragma comment(lib, "ole32.lib")

const CLSID CLSID_MMDeviceEnumerator = __uuidof(MMDeviceEnumerator);
const IID IID_IMMDeviceEnumerator = __uuidof(IMMDeviceEnumerator);
const IID IID_IAudioClient = __uuidof(IAudioClient);
const IID IID_IAudioCaptureClient = __uuidof(IAudioCaptureClient);

WasapiAudioCapture::WasapiAudioCapture() {}

WasapiAudioCapture::~WasapiAudioCapture() {
    stop();
    cleanup();
}

bool WasapiAudioCapture::initialize(int targetSampleRate) {
    m_targetSampleRate = targetSampleRate;
    HRESULT hr = CoInitializeEx(nullptr, COINIT_MULTITHREADED);
    
    hr = CoCreateInstance(
        CLSID_MMDeviceEnumerator, nullptr,
        CLSCTX_ALL, IID_IMMDeviceEnumerator,
        (void**)&m_pEnumerator
    );
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] CoCreateInstance failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    hr = m_pEnumerator->GetDefaultAudioEndpoint(eCapture, eConsole, &m_pDevice);
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] GetDefaultAudioEndpoint failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    hr = m_pDevice->Activate(IID_IAudioClient, CLSCTX_ALL, nullptr, (void**)&m_pAudioClient);
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] Activate AudioClient failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    hr = m_pAudioClient->GetMixFormat(&m_pwfx);
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] GetMixFormat failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    // 100ms buffer duration
    REFERENCE_TIME hnsBufferDuration = 1000000;
    hr = m_pAudioClient->Initialize(
        AUDCLNT_SHAREMODE_SHARED,
        0,
        hnsBufferDuration,
        0,
        m_pwfx,
        nullptr
    );
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] AudioClient Initialize failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    hr = m_pAudioClient->GetService(IID_IAudioCaptureClient, (void**)&m_pCaptureClient);
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] GetService CaptureClient failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    return true;
}

bool WasapiAudioCapture::start() {
    if (m_isCapturing.load()) return true;
    if (!m_pAudioClient) {
        if (!initialize()) return false;
    }

    HRESULT hr = m_pAudioClient->Start();
    if (FAILED(hr)) {
        std::cerr << "[WASAPI] Start capture failed: 0x" << std::hex << hr << std::endl;
        return false;
    }

    m_isCapturing.store(true);
    m_stopRequested.store(false);
    m_captureThread = std::thread(&WasapiAudioCapture::captureLoop, this);
    return true;
}

void WasapiAudioCapture::stop() {
    if (!m_isCapturing.load()) return;
    m_stopRequested.store(true);
    if (m_captureThread.joinable()) {
        m_captureThread.join();
    }
    if (m_pAudioClient) {
        m_pAudioClient->Stop();
    }
    m_isCapturing.store(false);
}

void WasapiAudioCapture::cleanup() {
    if (m_pwfx) {
        CoTaskMemFree(m_pwfx);
        m_pwfx = nullptr;
    }
    if (m_pCaptureClient) {
        m_pCaptureClient->Release();
        m_pCaptureClient = nullptr;
    }
    if (m_pAudioClient) {
        m_pAudioClient->Release();
        m_pAudioClient = nullptr;
    }
    if (m_pDevice) {
        m_pDevice->Release();
        m_pDevice = nullptr;
    }
    if (m_pEnumerator) {
        m_pEnumerator->Release();
        m_pEnumerator = nullptr;
    }
}

void WasapiAudioCapture::captureLoop() {
    while (!m_stopRequested.load()) {
        UINT32 packetLength = 0;
        HRESULT hr = m_pCaptureClient->GetNextPacketSize(&packetLength);
        if (FAILED(hr)) {
            std::this_thread::sleep_for(std::chrono::milliseconds(5));
            continue;
        }

        while (packetLength > 0 && !m_stopRequested.load()) {
            BYTE* pData = nullptr;
            UINT32 numFramesAvailable = 0;
            DWORD flags = 0;

            hr = m_pCaptureClient->GetBuffer(&pData, &numFramesAvailable, &flags, nullptr, nullptr);
            if (SUCCEEDED(hr)) {
                if (!(flags & AUDCLNT_BUFFERFLAGS_SILENT)) {
                    processAudioBuffer(pData, numFramesAvailable, m_pwfx);
                } else {
                    // Silent frame
                    std::vector<int16_t> silence(numFramesAvailable * m_targetSampleRate / m_pwfx->nSamplesPerSec, 0);
                    if (m_dataCallback && !silence.empty()) {
                        m_dataCallback(silence.data(), silence.size());
                    }
                    if (m_levelCallback) {
                        m_levelCallback(0.0f);
                    }
                }
                m_pCaptureClient->ReleaseBuffer(numFramesAvailable);
            }

            hr = m_pCaptureClient->GetNextPacketSize(&packetLength);
            if (FAILED(hr)) break;
        }

        std::this_thread::sleep_for(std::chrono::milliseconds(10));
    }
}

void WasapiAudioCapture::processAudioBuffer(BYTE* pData, UINT32 numFramesAvailable, const WAVEFORMATEX* pwfx) {
    if (!pData || numFramesAvailable == 0 || !pwfx) return;

    int channels = pwfx->nChannels;
    int srcRate = pwfx->nSamplesPerSec;
    bool isFloat = (pwfx->wFormatTag == WAVE_FORMAT_IEEE_FLOAT) ||
        (pwfx->wFormatTag == WAVE_FORMAT_EXTENSIBLE &&
         reinterpret_cast<const WAVEFORMATEXTENSIBLE*>(pwfx)->SubFormat == KSDATAFORMAT_SUBTYPE_IEEE_FLOAT);

    // Step 1: Convert input buffer to normalized mono float samples [-1.0, 1.0]
    std::vector<float> monoFloat(numFramesAvailable);
    double sumSquares = 0.0;

    if (isFloat && pwfx->wBitsPerSample == 32) {
        const float* fData = reinterpret_cast<const float*>(pData);
        for (UINT32 i = 0; i < numFramesAvailable; ++i) {
            float mono = 0.0f;
            for (int ch = 0; ch < channels; ++ch) {
                mono += fData[i * channels + ch];
            }
            mono /= channels;
            monoFloat[i] = mono;
            sumSquares += mono * mono;
        }
    } else if (pwfx->wBitsPerSample == 16) {
        const int16_t* sData = reinterpret_cast<const int16_t*>(pData);
        for (UINT32 i = 0; i < numFramesAvailable; ++i) {
            float mono = 0.0f;
            for (int ch = 0; ch < channels; ++ch) {
                mono += sData[i * channels + ch] / 32768.0f;
            }
            mono /= channels;
            monoFloat[i] = mono;
            sumSquares += mono * mono;
        }
    } else {
        return; // Unsupported bit depth
    }

    // RMS Level computation (emitted ~20-30 times per sec)
    m_levelCounter++;
    if (m_levelCounter % 3 == 0 && m_levelCallback) {
        float rms = static_cast<float>(std::sqrt(sumSquares / numFramesAvailable));
        // Scale and clamp [0.0, 1.0]
        float scaled = std::min(1.0f, rms * 4.0f);
        m_levelCallback(scaled);
    }

    // Step 2: Resample to 16kHz if needed (linear interpolation)
    size_t outSamples = (size_t)(numFramesAvailable * (double)m_targetSampleRate / srcRate);
    if (outSamples == 0) return;

    m_conversionBuffer.resize(outSamples);
    double step = (double)numFramesAvailable / outSamples;

    for (size_t i = 0; i < outSamples; ++i) {
        double srcIdx = i * step;
        size_t idx0 = (size_t)srcIdx;
        size_t idx1 = std::min(idx0 + 1, (size_t)(numFramesAvailable - 1));
        double frac = srcIdx - idx0;

        float val = static_cast<float>((1.0 - frac) * monoFloat[idx0] + frac * monoFloat[idx1]);
        // Clamp and convert to int16
        val = std::max(-1.0f, std::min(1.0f, val));
        m_conversionBuffer[i] = static_cast<int16_t>(val * 32767.0f);
    }

    if (m_dataCallback && !m_conversionBuffer.empty()) {
        m_dataCallback(m_conversionBuffer.data(), m_conversionBuffer.size());
    }
}

