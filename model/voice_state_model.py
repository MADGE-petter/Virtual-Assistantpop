"""
Voice State Model - Tracks voice states and waveform visualizer data matching annotation #13 in po spec.
"""

from enum import Enum
from typing import List
import math
import random


class VoiceState(str, Enum):
    READY = "READY"
    LISTENING = "LISTENING"
    THINKING = "THINKING"
    SPEAKING = "SPEAKING"
    SLEEPING = "SLEEPING"


class VoiceStateModel:
    """Model tracking voice status and generating dynamic audio visualization frames."""

    STATE_LABELS = {
        VoiceState.READY: "READY",
        VoiceState.LISTENING: "LISTENING",
        VoiceState.THINKING: "THINKING",
        VoiceState.SPEAKING: "SPEAKING",
        VoiceState.SLEEPING: "SLEEPING"
    }

    STATE_SUBTITLES = {
        VoiceState.READY: "Sẵn sàng nhận lệnh",
        VoiceState.LISTENING: "Đang nghe...",
        VoiceState.THINKING: "Đang suy nghĩ...",
        VoiceState.SPEAKING: "Đang trả lời...",
        VoiceState.SLEEPING: "Ngủ zzz"
    }

    def __init__(self):
        self.current_state = VoiceState.READY
        self.bar_count = 28
        self._phase = 0.0

    def set_state(self, state: VoiceState):
        self.current_state = state

    def generate_waveform(self) -> List[float]:
        """Generate normalized amplitude heights (0.0 to 1.0) for audio visualizer."""
        self._phase += 0.2
        amplitudes = []

        for i in range(self.bar_count):
            norm_i = i / float(self.bar_count)

            if self.current_state == VoiceState.READY:
                # Gentle ambient breathing wave
                val = 0.25 + 0.15 * math.sin(self._phase * 1.5 + norm_i * 6.28)
            elif self.current_state == VoiceState.LISTENING:
                # Dynamic reactive mic pulses
                val = 0.2 + 0.7 * abs(math.sin(self._phase * 3.0 + norm_i * 12.0) * math.cos(self._phase * 2.0))
                val += random.uniform(-0.05, 0.1)
            elif self.current_state == VoiceState.THINKING:
                # Flowing rhythmic sine pulse moving across center
                center_dist = abs(norm_i - 0.5)
                val = 0.15 + (1.0 - center_dist * 1.8) * 0.6 * (0.5 + 0.5 * math.sin(self._phase * 4.0 - norm_i * 10.0))
            elif self.current_state == VoiceState.SPEAKING:
                # Active multi-frequency voice speech wave
                val = 0.3 + 0.65 * abs(math.sin(self._phase * 5.0 + norm_i * 15.0) * math.sin(self._phase * 2.5))
                val += random.uniform(-0.08, 0.08)
            else:  # SLEEPING
                # Flat minimal resting line
                val = 0.08 + 0.04 * math.sin(self._phase * 0.5 + norm_i * 3.0)

            amplitudes.append(max(0.05, min(1.0, val)))

        return amplitudes
