#pragma once

#include <string>
#include <functional>
#include <vector>
#include <regex>

/**
 * @brief Chunks LLM token stream into natural sentences in real time.
 * Allows TTS synthesis to begin immediately on the 1st sentence while LLM generates the 2nd.
 */
class SentenceStreamer {
public:
    using SentenceCallback = std::function<void(const std::string& sentence)>;

    explicit SentenceStreamer(SentenceCallback callback = nullptr)
        : m_callback(callback) {}

    void setCallback(SentenceCallback callback) {
        m_callback = callback;
    }

    void reset() {
        m_buffer.clear();
        m_sentenceIndex = 0;
    }

    /**
     * @brief Feed a new token from LLM into the streamer.
     */
    void feedToken(const std::string& token) {
        m_buffer += token;

        // Check if buffer contains sentence end marks
        size_t splitPos = findSentenceBoundary(m_buffer);
        while (splitPos != std::string::npos) {
            std::string sentence = m_buffer.substr(0, splitPos + 1);
            m_buffer = m_buffer.substr(splitPos + 1);

            cleanAndEmit(sentence);
            splitPos = findSentenceBoundary(m_buffer);
        }
    }

    /**
     * @brief Flush remaining text at the end of generation.
     */
    void flush() {
        if (!m_buffer.empty()) {
            cleanAndEmit(m_buffer);
            m_buffer.clear();
        }
    }

    int getSentenceCount() const { return m_sentenceIndex; }

private:
    size_t findSentenceBoundary(const std::string& text) {
        if (text.empty()) return std::string::npos;

        // Minimum character length before considering punctuation as sentence end
        // to avoid splitting abbreviations or very short phrases
        const size_t minLength = 20;

        for (size_t i = 0; i < text.size(); ++i) {
            char c = text[i];
            // Strong boundaries: period, exclamation, question mark, newline
            if (c == '.' || c == '!' || c == '?' || c == '\n') {
                // Ensure not ellipsis like "..."
                if (i + 1 < text.size() && text[i + 1] == '.') {
                    continue;
                }
                return i;
            }

            // Medium boundary: comma or colon only if length is already long enough
            if ((c == ',' || c == ':' || c == ';') && i >= 40) {
                return i;
            }
        }
        return std::string::npos;
    }

    void cleanAndEmit(std::string text) {
        // Strip markdown characters (*, #, _, `, [ ])
        static const std::regex mdRegex(R"([\*\#\_`\[\]\(\)])");
        text = std::regex_replace(text, mdRegex, "");

        // Trim leading/trailing whitespace
        size_t start = text.find_first_not_of(" \t\r\n");
        if (start == std::string::npos) return;
        size_t end = text.find_last_not_of(" \t\r\n");
        text = text.substr(start, end - start + 1);

        if (!text.empty()) {
            m_sentenceIndex++;
            if (m_callback) {
                m_callback(text);
            }
        }
    }

    SentenceCallback m_callback;
    std::string m_buffer;
    int m_sentenceIndex = 0;
};

