"""
Mascot Model - State, configuration, and data structures for Desktop Mini Mascot.
Follows MVC architecture: encapsulates all state, animation timers, idle sleep tracking,
and screen edge cling state.
"""

import math
import random
import time
from typing import Optional, List, Dict, Any
from PyQt6.QtCore import QPoint, QSettings
from model.voice_state_model import VoiceState


class MascotModel:
    """Encapsulates all state, timers, particles, and configuration for the Mascot."""

    def __init__(self):
        self.voice_state: VoiceState = VoiceState.READY
        self.settings = QSettings("PopAI", "MiniMascot")

        # Animation & Breathing Physics
        self.pulse_phase: float = 0.0

        # Mouse Dragging State
        self.drag_start_pos: QPoint = QPoint()
        self.is_dragging: bool = False
        self.drag_distance: float = 0.0
        self.dizzy_end_time: float = 0.0

        # Screen Edge Clinging System (Left, Right, Top, Bottom)
        self.cling_edge: Optional[str] = None  # None, "left", "right", "top", "bottom"
        self.cling_ratio: float = 0.0          # 0.0 = free floating, 1.0 = fully clinging
        saved_cling = self.settings.value("cling_edge", None)
        if saved_cling and isinstance(saved_cling, str) and saved_cling in ("left", "right", "top", "bottom"):
            self.cling_edge = saved_cling
            self.cling_ratio = 1.0

        # Eye Tracking & Blinking State
        self.current_eye_x: float = 0.0
        self.current_eye_y: float = 0.0
        self.blink_phase: float = 0.0  # 0.0 = open, 1.0 = fully closed
        self.is_blinking: bool = False
        self.next_blink_time: float = time.time() + random.uniform(2.5, 4.5)

        # Mouth Lip-sync & Ear Wiggle
        self.mouth_open: float = 0.0
        self.ear_wiggle_angle: float = 0.0

        # Autonomous Idle & Sleep System
        self.last_user_activity: float = time.time()
        self.last_cursor_pos: QPoint = QPoint()
        self.is_sleeping: bool = False
        self.is_drowsy: bool = False
        self.drowsy_ratio: float = 0.0
        self.wake_up_until: float = 0.0

        # Cute Sleep Peeking (hé mở 1 mắt liếc nhìn rồi ngủ tiếp)
        self.peek_eye: int = 0  # 0: none, 1: left eye, 2: right eye
        self.next_peek_time: float = time.time() + random.uniform(4.5, 7.5)
        self.peek_end_time: float = 0.0

        # Floating zZz Particle Bubbles
        self.zzz_particles: List[Dict[str, Any]] = []
        self.next_zzz_time: float = 0.0

        # Eco Power Saving Mode State
        self.is_power_saving: bool = False
        self.sleep_timeout_minutes: float = 3.0
        self.sleep_timeout_sec: float = 180.0
        self.drowsy_timeout_sec: float = 155.0

        self.reload_settings()

    def reload_settings(self):
        """Reload sleep timeout settings from user configuration & QSettings."""
        try:
            from view.ui.settings.settings_config import load_user_settings
            cfg = load_user_settings()
            minutes = float(self.settings.value("sleep_timeout_minutes", cfg.get("mascot_sleep_timeout_minutes", 3)))
        except Exception:
            minutes = 3.0

        self.sleep_timeout_minutes = max(0.5, minutes)
        self.sleep_timeout_sec = self.sleep_timeout_minutes * 60.0
        if self.sleep_timeout_sec > 60.0:
            self.drowsy_timeout_sec = self.sleep_timeout_sec - 25.0
        else:
            self.drowsy_timeout_sec = self.sleep_timeout_sec * 0.75

    def trigger_wake_up(self):
        """Immediately wake up mascot from sleep or drowsiness."""
        now = time.time()
        if self.is_sleeping or self.is_drowsy:
            self.wake_up_until = now + 1.2
            self.is_sleeping = False
            self.is_drowsy = False
            self.drowsy_ratio = 0.0
            self.peek_eye = 0
            self.zzz_particles.clear()

        self.last_user_activity = now

    def save_position(self, pos: QPoint):
        """Save desktop position and clinging state."""
        self.settings.setValue("position", pos)
        self.settings.setValue("cling_edge", self.cling_edge or "")

    def load_saved_position(self) -> Optional[QPoint]:
        """Load saved desktop position."""
        pos = self.settings.value("position", None)
        if pos and isinstance(pos, QPoint):
            return pos
        return None
