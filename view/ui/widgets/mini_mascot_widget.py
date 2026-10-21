"""
POP Mini Floating Mascot Widget - Interactive Desktop Chibi Cyber-Pet.
Features:
- Procedural Vector Chibi Cat-Robot Art with Neon Cyberpunk Aesthetics
- Full 4 Limbs & Cyber Tail (2 Arms/Paws, 2 Legs/Feet, Wagging Mecha Tail)
- Cyber Heart Core Arc Reactor pulsating with life
- Smooth 360° Cursor Tracking (eyes organically look toward cursor position)
- Natural Periodic Eye Blinking
- Autonomous Idle Sleep & Play System:
  * Fast, responsive sleep transitions: Drowsy at 3.0s of idle, Deep Sleep at 6.0s
  * True sliding armor eyelid animation for heavy droopy eyes (lim dim)
  * Head nodding & bobbing physics while dozing off
  * Peaceful curved sleeping eyes with cute lashes & floating zZz neon bubbles
  * Periodic cute one-eye peeking while asleep
  * Startled cheerful wake-up reaction on mouse proximity or click
- Interactive Voice State Expressions (Listening, Thinking, Speaking, Ready, Sleeping)
- Drag Physics & Expressions (Shocked / Dizzy '> <' while dragging, Relieved bounce on drop)
- Lip-sync Mouth Animation when Speaking
"""

import math
import random
import time
from typing import Optional
from PyQt6.QtCore import Qt, QPoint, QPointF, QTimer, pyqtSignal, QRectF, QSettings
from PyQt6.QtGui import (
    QPainter, QColor, QBrush, QPen, QRadialGradient, QLinearGradient,
    QMouseEvent, QCursor, QPainterPath, QPolygonF, QFont, QGuiApplication
)
from PyQt6.QtWidgets import QWidget

from model.voice_state_model import VoiceState


class MiniMascotWidget(QWidget):
    """Always-On-Top Interactive Chibi Desktop Mascot with Full Limbs & Autonomous Sleep/Play System."""

    toggleMainWindowRequested = pyqtSignal()
    toggleVoiceRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.voice_state = VoiceState.READY
        self._settings = QSettings("PopAI", "MiniMascot")

        # Widget Dimensions: 120x120 for generous chibi proportions with full limbs & zZz particles
        self.setFixedSize(120, 120)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("POP AI Chibi Mascot\n• Click đơn: Bật/Tắt Micro\n• Kéo thả: Di chuyển & Bám viền màn hình\n• Bấm đúp: Mở/Ẩn cửa sổ Chat chính")

        # Physics & Animation State
        self._pulse_phase: float = 0.0
        self._drag_start_pos: QPoint = QPoint()
        self._is_dragging: bool = False
        self._drag_distance: float = 0.0
        self._dizzy_end_time: float = 0.0

        # Screen Edge Clinging System (Left, Right, Top, Bottom)
        self._cling_edge: Optional[str] = None  # None, "left", "right", "top", "bottom"
        self._cling_ratio: float = 0.0  # 0.0 = free floating, 1.0 = fully clinging
        saved_cling = self._settings.value("cling_edge", None)
        if saved_cling and isinstance(saved_cling, str) and saved_cling in ("left", "right", "top", "bottom"):
            self._cling_edge = saved_cling
            self._cling_ratio = 1.0

        # Eye Tracking & Blinking State
        self._current_eye_x: float = 0.0
        self._current_eye_y: float = 0.0
        self._blink_phase: float = 0.0  # 0.0 = open, 1.0 = fully closed
        self._is_blinking: bool = False
        self._next_blink_time: float = time.time() + random.uniform(2.5, 4.5)

        # Mouth Lip-sync & Ear Wiggle
        self._mouth_open: float = 0.0
        self._ear_wiggle_angle: float = 0.0

        # Autonomous Idle & Sleep System
        self._last_user_activity: float = time.time()
        self._last_cursor_pos: QPoint = QCursor.pos()
        self._is_sleeping: bool = False
        self._is_drowsy: bool = False
        self._drowsy_ratio: float = 0.0
        self._wake_up_until: float = 0.0

        # Cute Sleep Peeking (hé mở 1 mắt liếc nhìn rồi ngủ tiếp)
        self._peek_eye: int = 0  # 0: none, 1: left eye, 2: right eye
        self._next_peek_time: float = time.time() + random.uniform(4.5, 7.5)
        self._peek_end_time: float = 0.0

        # Floating zZz Particle Bubbles
        self._zzz_particles: list = []
        self._next_zzz_time: float = 0.0

        # Eco Power Saving Mode State
        self._is_power_saving: bool = False
        self._sleep_timeout_minutes: float = 3.0
        self._sleep_timeout_sec: float = 180.0
        self._drowsy_timeout_sec: float = 155.0
        self.reload_settings()

        # Load saved desktop position
        saved_pos = self._settings.value("position", None)
        if saved_pos and isinstance(saved_pos, QPoint):
            self.move(saved_pos)
            self._snap_to_edge_if_near()

        # 45 FPS Animation Timer (Auto drops to 10 FPS during sleep to save resources)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)

    def reload_settings(self):
        """Reload sleep timeout settings from user configuration & QSettings."""
        try:
            from view.ui.settings.settings_config import load_user_settings
            cfg = load_user_settings()
            minutes = float(self._settings.value("sleep_timeout_minutes", cfg.get("mascot_sleep_timeout_minutes", 3)))
        except Exception:
            minutes = 3.0

        self._sleep_timeout_minutes = max(0.5, minutes)
        self._sleep_timeout_sec = self._sleep_timeout_minutes * 60.0
        # Lim dim (drowsy) starts ~25 seconds before deep sleep (or at 75% for short timeouts)
        if self._sleep_timeout_sec > 60.0:
            self._drowsy_timeout_sec = self._sleep_timeout_sec - 25.0
        else:
            self._drowsy_timeout_sec = self._sleep_timeout_sec * 0.75

    def showEvent(self, event):
        super().showEvent(event)
        if not self.timer.isActive():
            self.timer.start(22)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.timer.isActive():
            self.timer.stop()

    def set_voice_state(self, state: VoiceState):
        self.voice_state = state
        if state == VoiceState.SLEEPING:
            self._is_sleeping = True
            self._is_drowsy = False
            self._drowsy_ratio = 1.0
            self._zzz_particles.clear()
        elif state in (VoiceState.SPEAKING, VoiceState.THINKING):
            # Only wake up when AI is actively responding/thinking
            self._trigger_wake_up()
        # Note: Background ambient LISTENING or READY does NOT force wake up!
        self.update()

    def wake_up(self):
        """Public wake up method (called when user says wake word 'Pop ơi' or triggers wake action)."""
        self._trigger_wake_up()

    def _trigger_wake_up(self):
        """Immediately wake up from sleep/drowsiness with max performance mode."""
        now = time.time()
        if self._is_sleeping or self._is_drowsy:
            self._wake_up_until = now + 1.2
            self._is_sleeping = False
            self._is_drowsy = False
            self._drowsy_ratio = 0.0
            self._peek_eye = 0
            self._zzz_particles.clear()

        # Restore max performance (45 FPS)
        if self._is_power_saving:
            self._is_power_saving = False
            self.timer.setInterval(22)

        self._last_user_activity = now

    # ============================================================
    # ANIMATION LOOP & PHYSICS
    # ============================================================

    def _animate(self):
        if not self.isVisible():
            if self.timer.isActive():
                self.timer.stop()
            return

        now = time.time()

        # 1. Cursor Activity Tracking
        cursor_pos = QCursor.pos()
        cursor_moved = math.hypot(cursor_pos.x() - self._last_cursor_pos.x(), cursor_pos.y() - self._last_cursor_pos.y())
        self._last_cursor_pos = cursor_pos

        widget_center = self.mapToGlobal(QPoint(int(self.width() / 2), int(self.height() / 2)))
        dx = cursor_pos.x() - widget_center.x()
        dy = cursor_pos.y() - widget_center.y()
        dist_to_cursor = math.hypot(dx, dy)

        # Active interaction detection:
        # 1. Click/drag on mascot (mousePressEvent / _is_dragging)
        # 2. Mouse moving near the mascot (< 85px from center and moving > 2.0px)
        # 3. AI bot actively speaking or thinking
        is_bot_active = self.voice_state in (VoiceState.SPEAKING, VoiceState.THINKING)
        is_cursor_moving_near = (dist_to_cursor < 85.0 and cursor_moved > 2.0)
        is_interacting = self._is_dragging or is_bot_active or is_cursor_moving_near

        if is_interacting:
            if self._is_sleeping or self._is_drowsy:
                # WAKE UP: When clicked, or when mouse moves near it, or when bot speaks!
                self._trigger_wake_up()
            else:
                self._last_user_activity = now

        # 2. Idle & Sleep State Machine
        idle_time = now - self._last_user_activity
        is_waking_up = now < self._wake_up_until

        if self.voice_state == VoiceState.SLEEPING:
            self._is_sleeping = True
            self._is_drowsy = False
            self._drowsy_ratio = 1.0
        elif is_waking_up or is_interacting:
            self._is_sleeping = False
            self._is_drowsy = False
            self._drowsy_ratio = max(0.0, self._drowsy_ratio - 0.2)
        elif idle_time >= self._sleep_timeout_sec:
            # Deep Sleep after configured timeout (default: 3 minutes = 180s)
            self._is_sleeping = True
            self._is_drowsy = False
            self._drowsy_ratio = 1.0
        elif idle_time >= self._drowsy_timeout_sec:
            # Drowsy / Lim dim before deep sleep
            self._is_drowsy = True
            self._is_sleeping = False
            window = max(1.0, self._sleep_timeout_sec - self._drowsy_timeout_sec)
            self._drowsy_ratio = min(1.0, (idle_time - self._drowsy_timeout_sec) / window)
        else:
            self._is_sleeping = False
            self._is_drowsy = False
            self._drowsy_ratio = 0.0

        # Eco Power Saving Mode Management:
        # Sleeping -> 10 FPS (100ms interval, saves ~80% CPU/GPU resources)
        # Awake -> 45 FPS (22ms interval, max performance and fluid responsiveness)
        if self._is_sleeping and not self._is_power_saving:
            self._is_power_saving = True
            self.timer.setInterval(100)
        elif not self._is_sleeping and self._is_power_saving:
            self._is_power_saving = False
            self.timer.setInterval(22)

        # Smoothly interpolate edge clinging ratio
        target_cling = 1.0 if self._cling_edge else 0.0
        self._cling_ratio += (target_cling - self._cling_ratio) * 0.18

        # Adjust breathing speed based on state
        if self._is_sleeping:
            self._pulse_phase += 0.026  # Slow, deep relaxed breath
        elif self._is_drowsy:
            self._pulse_phase += 0.035
        else:
            self._pulse_phase += 0.052

        # 3. Cute Sleep Peeking Logic (hé mở 1 mắt liếc nhìn rồi ngủ tiếp)
        if self._is_sleeping:
            if self._peek_eye != 0:
                if now >= self._peek_end_time:
                    self._peek_eye = 0
                    self._next_peek_time = now + random.uniform(4.5, 7.5)
            else:
                if now >= self._next_peek_time:
                    self._peek_eye = random.choice([1, 2])
                    self._peek_end_time = now + random.uniform(1.3, 1.9)
        else:
            self._peek_eye = 0

        # 4. Floating zZz Particles Logic (Spawns while deep asleep)
        if self._is_sleeping:
            if now >= self._next_zzz_time:
                self._next_zzz_time = now + random.uniform(1.2, 1.8)
                head_cx = self.width() / 2.0
                head_cy = (self.height() / 2.0) - 8.0

                vx = random.uniform(0.35, 0.7)
                vy = random.uniform(-0.65, -1.0)
                spawn_x = head_cx + random.uniform(6.0, 15.0)
                spawn_y = head_cy - 12.0

                # Direct particles inwards when clinging to screen border
                if self._cling_edge == "left":
                    vx = random.uniform(0.7, 1.2)
                    vy = random.uniform(-0.35, -0.7)
                    spawn_x = head_cx + 10.0
                elif self._cling_edge == "right":
                    vx = random.uniform(-1.2, -0.7)
                    vy = random.uniform(-0.35, -0.7)
                    spawn_x = head_cx - 10.0
                elif self._cling_edge == "top":
                    vx = random.uniform(-0.25, 0.25)
                    vy = random.uniform(0.5, 0.9)
                    spawn_y = head_cy + 8.0

                self._zzz_particles.append({
                    "x": spawn_x,
                    "y": spawn_y,
                    "alpha": 230,
                    "char": random.choice(["z", "Z"]),
                    "size": random.uniform(11.0, 15.0),
                    "vx": vx,
                    "vy": vy
                })

        # Update zZz particles
        surviving_particles = []
        for p in self._zzz_particles:
            p["x"] += p["vx"] + math.sin(p["y"] * 0.08) * 0.25
            p["y"] += p["vy"]
            p["alpha"] -= 2.2
            if p["alpha"] > 0:
                surviving_particles.append(p)
        self._zzz_particles = surviving_particles

        # 5. Natural Blinking Logic (only when fully awake)
        if not self._is_sleeping and not self._is_drowsy:
            if not self._is_blinking and now >= self._next_blink_time:
                self._is_blinking = True
                self._blink_phase = 0.0

            if self._is_blinking:
                self._blink_phase += 0.22
                if self._blink_phase >= math.pi:
                    self._is_blinking = False
                    self._blink_phase = 0.0
                    self._next_blink_time = now + random.uniform(2.5, 5.0)

        # 6. Smooth Eye Tracking toward Global Mouse Cursor (Skipped in sleep mode to save CPU)
        if not self._is_sleeping:
            try:
                angle = math.atan2(dy, dx)
                max_offset = 4.2
                sensitivity = 45.0
                target_x = math.cos(angle) * min(max_offset, dist_to_cursor / sensitivity)
                target_y = math.sin(angle) * min(max_offset, dist_to_cursor / sensitivity)

                # Add edge cling gaze bias so mascot looks naturally inward into the workspace
                if self._cling_edge == "left":
                    target_x = max(target_x, 1.0)
                elif self._cling_edge == "right":
                    target_x = min(target_x, -1.0)
                elif self._cling_edge == "top":
                    target_y = max(target_y, 1.0)
                elif self._cling_edge == "bottom":
                    target_y = min(target_y, -0.6)

                # Slower pupil tracking when drowsy
                lerp_speed = 0.06 if self._is_drowsy else 0.22
                self._current_eye_x += (target_x - self._current_eye_x) * lerp_speed
                self._current_eye_y += (target_y - self._current_eye_y) * lerp_speed
            except Exception:
                pass

        # 7. Dynamic Mouth & Ear State
        if self.voice_state == VoiceState.SPEAKING:
            self._mouth_open = (math.sin(self._pulse_phase * 3.5) + 1.0) / 2.0
            self._ear_wiggle_angle = math.sin(self._pulse_phase * 2.0) * 3.0
        elif self.voice_state == VoiceState.LISTENING:
            self._mouth_open = 0.1
            self._ear_wiggle_angle = math.sin(self._pulse_phase * 3.0) * 4.5
        elif self.voice_state == VoiceState.THINKING:
            self._mouth_open = 0.0
            self._ear_wiggle_angle = math.sin(self._pulse_phase * 1.5) * 2.0
        elif self._is_sleeping:
            self._mouth_open = 0.0
            self._ear_wiggle_angle = -7.0  # Ears folded back cute in deep sleep
        elif self._is_drowsy:
            self._mouth_open = 0.0
            self._ear_wiggle_angle = -4.0 * self._drowsy_ratio
        else:
            self._mouth_open = 0.0
            self._ear_wiggle_angle = math.sin(self._pulse_phase * 0.8) * 1.5

        self.update()

    # ============================================================
    # MOUSE EVENTS & DRAGGING
    # ============================================================

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_start_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            self._is_dragging = False
            self._drag_distance = 0.0
            self._trigger_wake_up()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self._drag_start_pos
            delta = (new_pos - self.pos()).manhattanLength()
            self._drag_distance += delta
            if self._drag_distance > 5:
                self._is_dragging = True

            # If currently clinging, check if user dragged mascot away from that edge
            if self._cling_edge:
                screen = self.screen() or QGuiApplication.primaryScreen()
                if screen:
                    geom = screen.availableGeometry()
                    pulled_away = False
                    if self._cling_edge == "left" and new_pos.x() - geom.left() > 45:
                        pulled_away = True
                    elif self._cling_edge == "right" and (geom.x() + geom.width()) - (new_pos.x() + self.width()) > 45:
                        pulled_away = True
                    elif self._cling_edge == "top" and new_pos.y() - geom.top() > 45:
                        pulled_away = True
                    elif self._cling_edge == "bottom" and (geom.y() + geom.height()) - (new_pos.y() + self.height()) > 45:
                        pulled_away = True

                    if pulled_away:
                        self._cling_edge = None

            self.move(new_pos)
            self._trigger_wake_up()
            event.accept()

    def mouseReleaseEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._is_dragging:
                self._dizzy_end_time = time.time() + 1.2
                self._is_dragging = False
                self._snap_to_edge_if_near()
                self._settings.setValue("position", self.pos())
                self._settings.setValue("cling_edge", self._cling_edge or "")
            elif self._drag_distance <= 5:
                self.toggleVoiceRequested.emit()
            self._trigger_wake_up()
            event.accept()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.toggleMainWindowRequested.emit()
            self._trigger_wake_up()
            event.accept()

    def _snap_to_edge_if_near(self):
        """Snap to nearest screen boundary if within snap margin, activating cling mode."""
        screen = self.screen() or QGuiApplication.primaryScreen()
        if not screen:
            return

        geom = screen.availableGeometry()
        cur_x = self.x()
        cur_y = self.y()
        w = self.width()
        h = self.height()

        dist_left = abs(cur_x - geom.left())
        dist_right = abs((geom.x() + geom.width()) - (cur_x + w))
        dist_top = abs(cur_y - geom.top())
        dist_bottom = abs((geom.y() + geom.height()) - (cur_y + h))

        SNAP_THRESHOLD = 50
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

        if min_dist <= SNAP_THRESHOLD:
            if min_dist == dist_left:
                self._cling_edge = "left"
                target_x = geom.left()
                target_y = max(geom.top(), min(geom.y() + geom.height() - h, cur_y))
            elif min_dist == dist_right:
                self._cling_edge = "right"
                target_x = geom.x() + geom.width() - w
                target_y = max(geom.top(), min(geom.y() + geom.height() - h, cur_y))
            elif min_dist == dist_top:
                self._cling_edge = "top"
                target_x = max(geom.left(), min(geom.x() + geom.width() - w, cur_x))
                target_y = geom.top()
            else:
                self._cling_edge = "bottom"
                target_x = max(geom.left(), min(geom.x() + geom.width() - w, cur_x))
                target_y = geom.y() + geom.height() - h

            self.move(target_x, target_y)
        else:
            self._cling_edge = None

    # ============================================================
    # PROCEDURAL CHIBI VECTOR RENDERING
    # ============================================================

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)

        w = self.width()
        h = self.height()
        base_cx = w / 2.0

        # Cling offsets & rotations
        cling_dx = 0.0
        cling_dy = 0.0
        cling_rot = 0.0

        if self._cling_edge == "left":
            cling_dx = -12.0 * self._cling_ratio
            cling_rot = -7.0 * self._cling_ratio
        elif self._cling_edge == "right":
            cling_dx = 12.0 * self._cling_ratio
            cling_rot = 7.0 * self._cling_ratio
        elif self._cling_edge == "top":
            cling_dy = -14.0 * self._cling_ratio
            pendulum = math.sin(self._pulse_phase * 1.3) * 4.5
            cling_rot = pendulum * self._cling_ratio
        elif self._cling_edge == "bottom":
            cling_dy = 8.0 * self._cling_ratio

        # Hover float breath offset (sin wave floating - dampened when clinging)
        if self._cling_edge in ("left", "right", "bottom"):
            float_speed = 0.4 if self._is_sleeping else 0.8
            float_y = math.sin(self._pulse_phase) * float_speed
        else:
            float_speed = 1.0 if self._is_sleeping else 2.2
            float_y = math.sin(self._pulse_phase) * float_speed

        cx = base_cx + cling_dx
        cy = (h / 2.0) + float_y + cling_dy

        # Apply cling posture rotation
        painter.save()
        if abs(cling_rot) > 0.01:
            painter.translate(cx, cy)
            painter.rotate(cling_rot)
            painter.translate(-cx, -cy)

        now = time.time()
        is_dizzy = now < self._dizzy_end_time
        is_waking_up = now < self._wake_up_until

        # Theme Colors based on Voice State
        if self.voice_state == VoiceState.READY:
            neon_primary = QColor(0, 255, 170)    # Emerald Neon
            neon_secondary = QColor(0, 142, 255)  # Cyan Blue
        elif self.voice_state == VoiceState.LISTENING:
            neon_primary = QColor(0, 229, 255)    # Electric Cyan
            neon_secondary = QColor(56, 189, 248) # Sky Glow
        elif self.voice_state == VoiceState.THINKING:
            neon_primary = QColor(245, 158, 11)   # Amber Gold
            neon_secondary = QColor(249, 115, 22)  # Orange
        elif self.voice_state == VoiceState.SPEAKING:
            neon_primary = QColor(168, 85, 247)   # Electric Violet
            neon_secondary = QColor(236, 72, 153) # Pink Magenta
        else:
            neon_primary = QColor(100, 116, 139)  # Slate Muted
            neon_secondary = QColor(51, 65, 85)

        # Muted colors during deep sleep
        if self._is_sleeping:
            neon_primary = QColor(int(neon_primary.red() * 0.75), int(neon_primary.green() * 0.75 + 30), int(neon_primary.blue() * 0.85 + 30))

        # --------------------------------------------------------
        # Head Position & Realistic Nodding / Bobbing Offset
        # --------------------------------------------------------
        if self._is_sleeping:
            # Steady gentle sleep nod
            head_nod = math.sin(self._pulse_phase * 0.9) * 3.0
        elif self._is_drowsy:
            # Drowsy bobbing (drooping down slowly, bobbing up)
            bob = (math.sin(self._pulse_phase * 1.1) + 1.0) / 2.0
            head_nod = bob * 4.2 * self._drowsy_ratio
        else:
            head_nod = 0.0

        head_cx = cx
        head_cy = cy - 8.0 + head_nod

        # --------------------------------------------------------
        # 1. Cyber Tail (Wagging behind torso)
        # --------------------------------------------------------
        self._draw_cyber_tail(painter, head_cx, head_cy, neon_primary)

        # --------------------------------------------------------
        # 2. Cyber Cat Ears (Mecha Chibi Ears)
        # --------------------------------------------------------
        ear_wiggle = self._ear_wiggle_angle
        if self._is_dragging:
            ear_wiggle = -8.0
        elif is_waking_up:
            ear_wiggle = 5.0 + math.sin(self._pulse_phase * 4.0) * 3.0

        self._draw_cyber_ear(painter, head_cx - 20, head_cy - 16, is_left=True, wiggle=ear_wiggle, primary=neon_primary)
        self._draw_cyber_ear(painter, head_cx + 20, head_cy - 16, is_left=False, wiggle=-ear_wiggle, primary=neon_primary)

        # --------------------------------------------------------
        # 3. Chibi Legs / Feet (Bottom Limbs with Cling Adaptation)
        # --------------------------------------------------------
        if self._cling_edge == "left":
            # Left foot braced against left wall, right foot dangling
            foot_l_x = head_cx - 16
            foot_l_y = head_cy + 30
            foot_r_x = head_cx - 2
            foot_r_y = head_cy + 34
            self._draw_cyber_foot(painter, foot_l_x, foot_l_y, neon_primary)
            self._draw_cyber_foot(painter, foot_r_x, foot_r_y, neon_primary)
            self._draw_magnetic_grip(painter, foot_l_x - 3.5, foot_l_y, neon_primary)
        elif self._cling_edge == "right":
            # Right foot braced against right wall, left foot dangling
            foot_r_x = head_cx + 16
            foot_r_y = head_cy + 30
            foot_l_x = head_cx + 2
            foot_l_y = head_cy + 34
            self._draw_cyber_foot(painter, foot_l_x, foot_l_y, neon_primary)
            self._draw_cyber_foot(painter, foot_r_x, foot_r_y, neon_primary)
            self._draw_magnetic_grip(painter, foot_r_x + 3.5, foot_r_y, neon_primary)
        elif self._cling_edge == "top":
            # Feet dangling and swinging playfully
            foot_sway = math.sin(self._pulse_phase * 1.8) * 1.8
            self._draw_cyber_foot(painter, head_cx - 9 + foot_sway, head_cy + 33, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 9 - foot_sway, head_cy + 33, neon_primary)
        elif self._cling_edge == "bottom":
            # Standing firm on taskbar
            self._draw_cyber_foot(painter, head_cx - 12, head_cy + 33, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 12, head_cy + 33, neon_primary)
        else:
            leg_l_sway = 0.0
            leg_r_sway = 0.0
            if not self._is_sleeping:
                leg_l_sway = math.sin(self._pulse_phase * 1.8) * 1.6
                leg_r_sway = math.sin(self._pulse_phase * 1.8 + math.pi) * 1.6
            if self._is_dragging:
                leg_l_sway = 2.5
                leg_r_sway = 2.5

            self._draw_cyber_foot(painter, head_cx - 10, head_cy + 33 + leg_l_sway, neon_primary)
            self._draw_cyber_foot(painter, head_cx + 10, head_cy + 33 + leg_r_sway, neon_primary)

        # --------------------------------------------------------
        # 4. Chibi Mecha Torso / Body & Cyber Heart
        # --------------------------------------------------------
        self._draw_cyber_body(painter, head_cx, head_cy, neon_primary, neon_secondary)

        # --------------------------------------------------------
        # 5. Chibi Head (Rounded Cyber Helmet)
        # --------------------------------------------------------
        head_w = 54.0
        head_h = 44.0
        head_rect = QRectF(head_cx - head_w / 2.0, head_cy - head_h / 2.0, head_w, head_h)

        # Helmet Body Gradient (Deep metallic charcoal with blue sheen)
        helmet_grad = QLinearGradient(head_cx, head_rect.top(), head_cx, head_rect.bottom())
        helmet_grad.setColorAt(0.0, QColor(24, 34, 54))
        helmet_grad.setColorAt(0.6, QColor(14, 20, 34))
        helmet_grad.setColorAt(1.0, QColor(8, 12, 22))
        painter.setBrush(QBrush(helmet_grad))
        painter.setPen(QPen(QColor(neon_primary.red(), neon_primary.green(), neon_primary.blue(), 180), 1.8))
        painter.drawRoundedRect(head_rect, 22.0, 20.0)

        # Glass Visor Arc Highlight (top glossy reflection)
        highlight_path = QPainterPath()
        highlight_path.moveTo(head_cx - 18, head_cy - 15)
        highlight_path.quadTo(head_cx, head_cy - 21, head_cx + 18, head_cy - 15)
        painter.setPen(QPen(QColor(255, 255, 255, 75), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(highlight_path)

        # --------------------------------------------------------
        # 6. Cheeks (Soft Neon Blush Ovals)
        # --------------------------------------------------------
        blush_color = QColor(255, 95, 140, 70 if self._is_sleeping else 110)
        painter.setBrush(QBrush(blush_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(head_cx - 20, head_cy + 4, 8.0, 4.0))
        painter.drawEllipse(QRectF(head_cx + 12, head_cy + 4, 8.0, 4.0))

        # --------------------------------------------------------
        # 7. Animated Eyes (Expression & Sleep & Tracking)
        # --------------------------------------------------------
        blink_ratio = math.sin(self._blink_phase) if self._is_blinking else 0.0
        eye_spacing = 13.0
        left_eye_center = QPointF(head_cx - eye_spacing, head_cy - 2)
        right_eye_center = QPointF(head_cx + eye_spacing, head_cy - 2)

        if self._is_dragging:
            # Dragging: Shocked/dizzy squeeze '> <'
            self._draw_shocked_eyes(painter, left_eye_center, right_eye_center, neon_primary)
        elif is_dizzy or is_waking_up:
            # Wake up / Post-drop: Relieved happy eyes '^ ^'
            self._draw_happy_eyes(painter, left_eye_center, right_eye_center, neon_primary)
        elif self.voice_state == VoiceState.SPEAKING:
            # Speaking: Cheerful crescent eyes '^ ^'
            self._draw_happy_eyes(painter, left_eye_center, right_eye_center, neon_primary)
        elif self._is_sleeping:
            # Sleep state with optional one-eye peek!
            if self._peek_eye == 1:
                # Left eye peeks at user!
                self._draw_anime_eye(painter, left_eye_center, 0.0, neon_primary)
                self._draw_sleeping_eye(painter, right_eye_center, neon_primary)
            elif self._peek_eye == 2:
                # Right eye peeks at user!
                self._draw_sleeping_eye(painter, left_eye_center, neon_primary)
                self._draw_anime_eye(painter, right_eye_center, 0.0, neon_primary)
            else:
                # Both eyes peacefully asleep
                self._draw_sleeping_eye(painter, left_eye_center, neon_primary)
                self._draw_sleeping_eye(painter, right_eye_center, neon_primary)
        elif self._is_drowsy:
            # Drowsy state: heavy droopy sliding eyelids (lim dim)
            self._draw_drowsy_eye(painter, left_eye_center, self._drowsy_ratio, neon_primary)
            self._draw_drowsy_eye(painter, right_eye_center, self._drowsy_ratio, neon_primary)
        else:
            # Normal / Listening / Thinking: Anime Eyes with Gaze Tracking
            self._draw_anime_eye(painter, left_eye_center, blink_ratio, neon_primary)
            self._draw_anime_eye(painter, right_eye_center, blink_ratio, neon_primary)

        # --------------------------------------------------------
        # 8. Cute Animated Mouth
        # --------------------------------------------------------
        self._draw_mouth(painter, head_cx, head_cy + 8, is_dizzy or is_waking_up, neon_primary)

        # --------------------------------------------------------
        # 9. Chibi Arms / Front Paws
        # --------------------------------------------------------
        self._draw_cyber_arms(painter, head_cx, head_cy, neon_primary, is_waking_up)

        # --------------------------------------------------------
        # 10. Floating zZz Particles (When Sleeping)
        # --------------------------------------------------------
        if self._is_sleeping and self._zzz_particles:
            self._draw_zzz_particles(painter, neon_primary)

        painter.restore()

    # ============================================================
    # SUB-COMPONENT RENDERERS
    # ============================================================

    def _draw_magnetic_grip(self, painter: QPainter, gx: float, gy: float, primary: QColor):
        """Draw small magnetic clamp glow with arc sparks at wall contact points."""
        pulse = (math.sin(self._pulse_phase * 3.5) + 1.0) / 2.0
        alpha = int(140 + pulse * 110)

        # Outer glow ring
        glow_color = QColor(primary.red(), primary.green(), primary.blue(), int(alpha * 0.45))
        painter.setBrush(QBrush(glow_color))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(gx - 3.5, gy - 3.5, 7.0, 7.0))

        # Core glowing spark
        spark_color = QColor(primary.red(), primary.green(), primary.blue(), alpha)
        painter.setBrush(QBrush(spark_color))
        painter.drawEllipse(QRectF(gx - 2.0, gy - 2.0, 4.0, 4.0))

        # White hot center
        painter.setBrush(QBrush(QColor(255, 255, 255, alpha)))
        painter.drawEllipse(QRectF(gx - 1.0, gy - 1.0, 2.0, 2.0))

    def _draw_cyber_tail(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor):
        """Draw mecha tail with smooth S-curve wagging and glowing tip."""
        sway_speed = 0.8 if self._is_sleeping else 1.8
        sway_amp = 3.5 if self._is_sleeping else 8.0
        tail_sway = math.sin(self._pulse_phase * sway_speed) * sway_amp

        if self._cling_edge == "left":
            # Tail curves inwards into desktop to the right
            start_pt = QPointF(head_cx + 4, head_cy + 26)
            ctrl1 = QPointF(head_cx + 16, head_cy + 30 + tail_sway * 0.4)
            ctrl2 = QPointF(head_cx + 24 + tail_sway * 0.7, head_cy + 18)
            tip_pt = QPointF(head_cx + 18 + tail_sway, head_cy + 6)
        elif self._cling_edge == "right":
            # Tail curves inwards into desktop to the left
            start_pt = QPointF(head_cx - 4, head_cy + 26)
            ctrl1 = QPointF(head_cx - 16, head_cy + 30 + tail_sway * 0.4)
            ctrl2 = QPointF(head_cx - 24 + tail_sway * 0.7, head_cy + 18)
            tip_pt = QPointF(head_cx - 18 + tail_sway, head_cy + 6)
        elif self._cling_edge == "top":
            # Tail hangs straight down swinging
            start_pt = QPointF(head_cx, head_cy + 28)
            ctrl1 = QPointF(head_cx + tail_sway * 0.5, head_cy + 36)
            ctrl2 = QPointF(head_cx + tail_sway * 0.9, head_cy + 42)
            tip_pt = QPointF(head_cx + tail_sway * 1.2, head_cy + 48)
        else:
            # Default behind torso
            start_pt = QPointF(head_cx - 8, head_cy + 28)
            ctrl1 = QPointF(head_cx - 20 + tail_sway * 0.7, head_cy + 30)
            ctrl2 = QPointF(head_cx - 28 + tail_sway * 1.3, head_cy + 18)
            tip_pt = QPointF(head_cx - 22 + tail_sway, head_cy + 8)

        tail_path = QPainterPath()
        tail_path.moveTo(start_pt)
        tail_path.cubicTo(ctrl1, ctrl2, tip_pt)

        # Tail Mecha Armor Line
        tail_pen = QPen(QColor(18, 26, 42), 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(tail_pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawPath(tail_path)

        # Neon Glow Stripe
        neon_pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), 180), 1.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(neon_pen)
        painter.drawPath(tail_path)

        # Glowing Neon Tip Orb
        painter.setBrush(QBrush(primary))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(tip_pt.x() - 3.2, tip_pt.y() - 3.2, 6.4, 6.4))

    def _draw_cyber_body(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor, secondary: QColor):
        """Draw chibi mecha torso with glowing Cyber Heart reactor."""
        torso_w = 34.0
        torso_h = 24.0
        torso_rect = QRectF(head_cx - torso_w / 2.0, head_cy + 14.0, torso_w, torso_h)

        # Torso metallic gradient
        body_grad = QLinearGradient(head_cx, torso_rect.top(), head_cx, torso_rect.bottom())
        body_grad.setColorAt(0.0, QColor(20, 28, 46))
        body_grad.setColorAt(1.0, QColor(10, 16, 28))
        painter.setBrush(QBrush(body_grad))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 140), 1.5))
        painter.drawRoundedRect(torso_rect, 11.0, 10.0)

        # Cyber Heart Core Arc Reactor (Ngực phát sáng)
        core_cx = head_cx
        core_cy = head_cy + 24.0
        core_r = 3.8
        core_pulse = (math.sin(self._pulse_phase * 2.0) + 1.0) / 2.0
        core_alpha = int(120 + core_pulse * 130)

        # Core outer aura
        core_glow = QColor(primary.red(), primary.green(), primary.blue(), int(core_alpha * 0.4))
        painter.setBrush(QBrush(core_glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QRectF(core_cx - core_r - 2.5, core_cy - core_r - 2.5, (core_r + 2.5) * 2, (core_r + 2.5) * 2))

        # Core central light
        core_color = QColor(primary.red(), primary.green(), primary.blue(), core_alpha)
        painter.setBrush(QBrush(core_color))
        painter.drawEllipse(QRectF(core_cx - core_r, core_cy - core_r, core_r * 2, core_r * 2))

    def _draw_cyber_foot(self, painter: QPainter, foot_cx: float, foot_cy: float, primary: QColor):
        """Draw cute rounded chibi mecha foot."""
        foot_w = 11.0
        foot_h = 8.0
        foot_rect = QRectF(foot_cx - foot_w / 2.0, foot_cy - foot_h / 2.0, foot_w, foot_h)

        painter.setBrush(QBrush(QColor(16, 24, 38)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 160), 1.2))
        painter.drawRoundedRect(foot_rect, 4.0, 4.0)

    def _draw_cyber_arms(self, painter: QPainter, head_cx: float, head_cy: float, primary: QColor, is_waking_up: bool):
        """Draw mecha arms/paws according to state (clinging, dragging, sleeping, speaking, ready)."""
        paw_color = QColor(18, 26, 42)
        paw_border = QPen(primary, 1.2)
        painter.setBrush(QBrush(paw_color))
        painter.setPen(paw_border)

        paw_w = 9.5
        paw_h = 7.5

        if self._is_dragging:
            # Arms raised in panic \ > < /
            l_y = head_cy + 2.0 + math.sin(self._pulse_phase * 6.0) * 3.0
            r_y = head_cy + 2.0 - math.sin(self._pulse_phase * 6.0) * 3.0
            painter.drawEllipse(QRectF(head_cx - 24 - paw_w / 2.0, l_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 24 - paw_w / 2.0, r_y - paw_h / 2.0, paw_w, paw_h))
        elif is_waking_up:
            # Arms raised cheerful greeting
            painter.drawEllipse(QRectF(head_cx - 21 - paw_w / 2.0, head_cy + 10 - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 21 - paw_w / 2.0, head_cy + 10 - paw_h / 2.0, paw_w, paw_h))
        elif self._cling_edge == "left":
            # Clinging to Left Screen Edge: Both paws grip the left wall!
            l_grip_x = head_cx - 28
            l_grip_y = head_cy + 8 + math.sin(self._pulse_phase * 2.0) * 1.5
            r_grip_x = head_cx - 22
            r_grip_y = head_cy + 22 - math.sin(self._pulse_phase * 2.0) * 1.5
            painter.drawEllipse(QRectF(l_grip_x - paw_w / 2.0, l_grip_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(r_grip_x - paw_w / 2.0, r_grip_y - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, l_grip_x - 3.5, l_grip_y, primary)
            self._draw_magnetic_grip(painter, r_grip_x - 3.5, r_grip_y, primary)
        elif self._cling_edge == "right":
            # Clinging to Right Screen Edge: Both paws grip the right wall!
            r_grip_x = head_cx + 28
            r_grip_y = head_cy + 8 + math.sin(self._pulse_phase * 2.0) * 1.5
            l_grip_x = head_cx + 22
            l_grip_y = head_cy + 22 - math.sin(self._pulse_phase * 2.0) * 1.5
            painter.drawEllipse(QRectF(r_grip_x - paw_w / 2.0, r_grip_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(l_grip_x - paw_w / 2.0, l_grip_y - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, r_grip_x + 3.5, r_grip_y, primary)
            self._draw_magnetic_grip(painter, l_grip_x + 3.5, l_grip_y, primary)
        elif self._cling_edge == "top":
            # Hanging from Top Ceiling: Arms reach up gripping the screen top!
            l_paw_x = head_cx - 15
            r_paw_x = head_cx + 15
            grip_y = head_cy - 18
            painter.drawEllipse(QRectF(l_paw_x - paw_w / 2.0, grip_y - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(r_paw_x - paw_w / 2.0, grip_y - paw_h / 2.0, paw_w, paw_h))
            self._draw_magnetic_grip(painter, l_paw_x, grip_y - 2.5, primary)
            self._draw_magnetic_grip(painter, r_paw_x, grip_y - 2.5, primary)
        elif self._cling_edge == "bottom":
            # Resting on Taskbar / Bottom Edge
            paw_bob = math.sin(self._pulse_phase * 1.2) * 0.8
            painter.drawEllipse(QRectF(head_cx - 15 - paw_w / 2.0, head_cy + 24 + paw_bob - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 15 - paw_w / 2.0, head_cy + 24 + paw_bob - paw_h / 2.0, paw_w, paw_h))
        elif self._is_sleeping:
            # Paws folded gently over belly/core
            painter.drawEllipse(QRectF(head_cx - 8 - paw_w / 2.0, head_cy + 25 - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 8 - paw_w / 2.0, head_cy + 25 - paw_h / 2.0, paw_w, paw_h))
        elif self.voice_state == VoiceState.SPEAKING:
            # Paws gesturing with voice
            l_off = math.sin(self._pulse_phase * 3.0) * 2.5
            r_off = -math.sin(self._pulse_phase * 3.0) * 2.5
            painter.drawEllipse(QRectF(head_cx - 17 - paw_w / 2.0, head_cy + 22 + l_off - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 17 - paw_w / 2.0, head_cy + 22 + r_off - paw_h / 2.0, paw_w, paw_h))
        else:
            # Default comfortable floating paws
            float_paw = math.sin(self._pulse_phase * 1.5) * 1.2
            painter.drawEllipse(QRectF(head_cx - 17 - paw_w / 2.0, head_cy + 22 + float_paw - paw_h / 2.0, paw_w, paw_h))
            painter.drawEllipse(QRectF(head_cx + 17 - paw_w / 2.0, head_cy + 22 - float_paw - paw_h / 2.0, paw_w, paw_h))

    def _draw_cyber_ear(self, painter: QPainter, base_x: float, base_y: float, is_left: bool, wiggle: float, primary: QColor):
        """Draw mecha cat ear with inner glowing polygon."""
        painter.save()
        painter.translate(base_x, base_y)
        painter.rotate(wiggle if is_left else -wiggle)

        ear_w = 14.0
        ear_h = 18.0
        sign = -1.0 if is_left else 1.0

        # Outer Armor Plate (charcoal dark mecha)
        outer_ear = QPolygonF([
            QPointF(0, 0),
            QPointF(sign * (ear_w * 0.9), -ear_h),
            QPointF(sign * (ear_w * 1.2), 2)
        ])
        painter.setBrush(QBrush(QColor(18, 25, 40)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 190), 1.4))
        painter.drawPolygon(outer_ear)

        # Inner Neon Glow Plate
        inner_ear = QPolygonF([
            QPointF(sign * 2.5, -1),
            QPointF(sign * (ear_w * 0.85), -ear_h + 4.5),
            QPointF(sign * (ear_w * 0.95), 0)
        ])
        c_inner = QColor(primary)
        c_inner.setAlpha(170)
        painter.setBrush(QBrush(c_inner))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawPolygon(inner_ear)

        painter.restore()

    def _draw_anime_eye(self, painter: QPainter, center: QPointF, blink_ratio: float, primary: QColor):
        """Draw sparkling large anime chibi eye with cursor tracking pupil & highlight glints."""
        eye_w = 11.5
        eye_h = max(1.2, 16.0 * (1.0 - blink_ratio))

        # Eyelid fully closed during blink -> Draw simple curved closed lash
        if blink_ratio > 0.85:
            painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            painter.drawLine(QPointF(center.x() - 5, center.y()), QPointF(center.x() + 5, center.y()))
            return

        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)

        # 1. Dark Eye Sclera / Base
        painter.setBrush(QBrush(QColor(6, 10, 18)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 140), 1.0))
        painter.drawEllipse(eye_rect)

        # 2. Glowing Iris with Cursor Tracking Offset
        pupil_w = 8.5
        pupil_h = max(1.0, 12.0 * (1.0 - blink_ratio))
        pupil_cx = center.x() + self._current_eye_x
        pupil_cy = center.y() + (self._current_eye_y * (1.0 - blink_ratio))

        pupil_grad = QLinearGradient(pupil_cx, pupil_cy - pupil_h / 2.0, pupil_cx, pupil_cy + pupil_h / 2.0)
        pupil_grad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 255))
        pupil_grad.setColorAt(0.7, QColor(0, 142, 255, 230))
        pupil_grad.setColorAt(1.0, QColor(2, 40, 80, 200))

        painter.setBrush(QBrush(pupil_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        pupil_rect = QRectF(pupil_cx - pupil_w / 2.0, pupil_cy - pupil_h / 2.0, pupil_w, pupil_h)
        painter.drawEllipse(pupil_rect)

        # 3. Big Anime Light Highlights (Sparkle Reflections)
        if blink_ratio < 0.6:
            painter.setBrush(QBrush(QColor(255, 255, 255, 240)))
            # Primary Top-Left Glint
            painter.drawEllipse(QRectF(pupil_cx - 2.8, pupil_cy - 4.2, 3.2, 3.8))
            # Secondary Bottom-Right Glint
            painter.setBrush(QBrush(QColor(255, 255, 255, 160)))
            painter.drawEllipse(QRectF(pupil_cx + 1.2, pupil_cy + 1.2, 1.8, 1.8))

    def _draw_drowsy_eye(self, painter: QPainter, center: QPointF, drowsy_ratio: float, primary: QColor):
        """Draw clearly visible half-closed droopy eye with sliding armor eyelid (lim dim)."""
        eye_w = 11.5
        eye_h = 16.0
        eye_rect = QRectF(center.x() - eye_w / 2.0, center.y() - eye_h / 2.0, eye_w, eye_h)

        # 1. Dark Sclera
        painter.setBrush(QBrush(QColor(6, 10, 18)))
        painter.setPen(QPen(QColor(primary.red(), primary.green(), primary.blue(), 130), 1.0))
        painter.drawEllipse(eye_rect)

        # 2. Glowing Iris (sinking slightly downward when drowsy)
        pupil_w = 8.5
        pupil_h = 11.0
        pupil_cx = center.x() + self._current_eye_x * 0.4
        pupil_cy = center.y() + 2.0 + (self._current_eye_y * 0.3)
        pupil_rect = QRectF(pupil_cx - pupil_w / 2.0, pupil_cy - pupil_h / 2.0, pupil_w, pupil_h)

        pupil_grad = QLinearGradient(pupil_cx, pupil_cy - pupil_h / 2.0, pupil_cx, pupil_cy + pupil_h / 2.0)
        pupil_grad.setColorAt(0.0, QColor(primary.red(), primary.green(), primary.blue(), 230))
        pupil_grad.setColorAt(1.0, QColor(0, 142, 255, 180))
        painter.setBrush(QBrush(pupil_grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(pupil_rect)

        # 3. Soft Highlight glint
        painter.setBrush(QBrush(QColor(255, 255, 255, 170)))
        painter.drawEllipse(QRectF(pupil_cx - 1.6, pupil_cy - 0.5, 2.0, 2.2))

        # 4. Heavy Drooping Helmet Armor Eyelid sliding down from top
        # drowsy_ratio goes from 0.0 to 1.0: covers from 35% up to 80% of the eye
        drop_fraction = 0.35 + 0.45 * drowsy_ratio
        lid_drop = eye_h * drop_fraction
        lid_y = (center.y() - eye_h / 2.0) + lid_drop

        painter.save()
        painter.setClipRect(eye_rect)
        painter.setBrush(QBrush(QColor(18, 26, 42)))
        painter.setPen(Qt.PenStyle.NoPen)
        # Cover top portion of eye with eyelid
        painter.drawRect(QRectF(center.x() - eye_w, center.y() - eye_h, eye_w * 2, (eye_h / 2.0) + lid_drop))
        painter.restore()

        # Eyelash line along bottom rim of drooping eyelid
        lash_pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.0, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(lash_pen)
        painter.drawLine(QPointF(center.x() - 6.0, lid_y), QPointF(center.x() + 6.0, lid_y + 0.6))

    def _draw_sleeping_eye(self, painter: QPainter, center: QPointF, primary: QColor):
        """Draw peacefully closed sleeping eye curve '‿ ‿' with cute eyelashes."""
        pen = QPen(QColor(primary.red(), primary.green(), primary.blue(), 230), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        path = QPainterPath()
        path.moveTo(center.x() - 6.0, center.y() - 1.0)
        path.quadTo(center.x(), center.y() + 3.5, center.x() + 6.0, center.y() - 1.0)
        painter.drawPath(path)

        # Tiny cute sleep eyelash at outer edge
        painter.drawLine(QPointF(center.x() + 5.5, center.y() - 0.5), QPointF(center.x() + 7.5, center.y() - 3.0))

    def _draw_shocked_eyes(self, painter: QPainter, left: QPointF, right: QPointF, color: QColor):
        """Draw cute anime squeeze/dizzy '> <' eyes when dragging."""
        pen = QPen(color, 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Left Eye '>'
        p_left = QPainterPath()
        p_left.moveTo(left.x() - 4.5, left.y() - 4.5)
        p_left.lineTo(left.x() + 2.5, left.y())
        p_left.lineTo(left.x() - 4.5, left.y() + 4.5)
        painter.drawPath(p_left)

        # Right Eye '<'
        p_right = QPainterPath()
        p_right.moveTo(right.x() + 4.5, right.y() - 4.5)
        p_right.lineTo(right.x() - 2.5, right.y())
        p_right.lineTo(right.x() + 4.5, right.y() + 4.5)
        painter.drawPath(p_right)

    def _draw_happy_eyes(self, painter: QPainter, left: QPointF, right: QPointF, color: QColor):
        """Draw cheerful crescent smiling anime eyes '^ ^'."""
        pen = QPen(color, 2.4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for pt in [left, right]:
            path = QPainterPath()
            path.moveTo(pt.x() - 5.5, pt.y() + 1.5)
            path.quadTo(pt.x(), pt.y() - 5.0, pt.x() + 5.5, pt.y() + 1.5)
            painter.drawPath(path)

    def _draw_mouth(self, painter: QPainter, cx: float, cy: float, is_happy: bool, color: QColor):
        """Draw cute animated mouth (smile / lip-sync open / small circle / sleeping)."""
        pen = QPen(color, 1.6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)

        if self._is_dragging:
            # Small cute surprised circle 'o'
            painter.setBrush(QBrush(QColor(10, 16, 28)))
            painter.drawEllipse(QRectF(cx - 3.0, cy - 1.5, 6.0, 5.5))
        elif is_happy:
            # Relieved wide smile
            path = QPainterPath()
            path.moveTo(cx - 4.5, cy - 1.0)
            path.quadTo(cx, cy + 3.0, cx + 4.5, cy - 1.0)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        elif self.voice_state == VoiceState.SPEAKING:
            # Animated open mouth for speaking
            h = 2.0 + self._mouth_open * 4.5
            painter.setBrush(QBrush(QColor(255, 95, 140, 180)))
            painter.drawEllipse(QRectF(cx - 3.5, cy - 1.0, 7.0, h))
        elif self._is_sleeping:
            # Tiny peaceful sleeping smile '◡'
            path = QPainterPath()
            path.moveTo(cx - 3.0, cy)
            path.quadTo(cx, cy + 2.0, cx + 3.0, cy)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)
        else:
            # Subtle cute cat mouth 'ω' or gentle smile
            path = QPainterPath()
            path.moveTo(cx - 4.0, cy - 0.5)
            path.quadTo(cx - 2.0, cy + 2.0, cx, cy + 0.5)
            path.quadTo(cx + 2.0, cy + 2.0, cx + 4.0, cy - 0.5)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

    def _draw_zzz_particles(self, painter: QPainter, primary: QColor):
        """Draw glowing floating zZz bubbles when sleeping."""
        painter.save()
        font = QFont("Arial", 11, QFont.Weight.Bold)
        painter.setFont(font)

        for p in self._zzz_particles:
            alpha = max(0, min(255, int(p["alpha"])))
            z_color = QColor(primary.red(), primary.green(), primary.blue(), alpha)
            painter.setPen(z_color)
            painter.drawText(QPointF(p["x"], p["y"]), p["char"])

        painter.restore()
