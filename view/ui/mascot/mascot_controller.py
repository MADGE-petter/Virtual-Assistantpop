"""
Mascot Controller - Interaction, Physics & State Controller for Desktop Mini Mascot.
Follows MVC architecture: encapsulates mouse input handling, drag physics,
screen edge snapping & clinging, cursor tracking physics, and animation updates.
"""

import math
import random
import time
from typing import Optional, Tuple
from PyQt6.QtCore import Qt, QPoint, QRect
from PyQt6.QtGui import QMouseEvent
from model.voice_state_model import VoiceState
from view.ui.mascot.mascot_model import MascotModel


class MascotController:
    """Handles interactions, edge detection, physics calculations, and animation updates."""

    def __init__(self, model: MascotModel, widget):
        self.model = model
        self.widget = widget

    # ============================================================
    # MOUSE INTERACTION & DRAG
    # ============================================================

    def handle_mouse_press(self, event: QMouseEvent):
        if event.button() == Qt.MouseButton.LeftButton:
            self.model.drag_start_pos = event.globalPosition().toPoint() - self.widget.frameGeometry().topLeft()
            self.model.is_dragging = False
            self.model.drag_distance = 0.0
            self.model.was_sleeping_on_press = self.model.is_sleeping
            if self.model.is_sleeping:
                self.model.trigger_wake_up(pop_bubble=True)
                if self.model.voice_state == VoiceState.SLEEPING:
                    self.model.voice_state = VoiceState.READY
                if hasattr(self.widget, "play_character_sfx"):
                    self.widget.play_character_sfx()
            else:
                self.model.trigger_wake_up()
            event.accept()

    def handle_mouse_move(self, event: QMouseEvent, screen_geom: Optional[QRect]):
        if event.buttons() == Qt.MouseButton.LeftButton:
            new_pos = event.globalPosition().toPoint() - self.model.drag_start_pos
            delta = (new_pos - self.widget.pos()).manhattanLength()
            self.model.drag_distance += delta
            if self.model.drag_distance > 5:
                self.model.is_dragging = True

            # If currently clinging, check if user dragged mascot away from that edge
            if self.model.cling_edge and screen_geom:
                w = self.widget.width()
                h = self.widget.height()
                pulled_away = False
                if self.model.cling_edge == "left" and new_pos.x() - screen_geom.left() > 45:
                    pulled_away = True
                elif self.model.cling_edge == "right" and (screen_geom.x() + screen_geom.width()) - (new_pos.x() + w) > 45:
                    pulled_away = True
                elif self.model.cling_edge == "top" and new_pos.y() - screen_geom.top() > 45:
                    pulled_away = True
                elif self.model.cling_edge == "bottom" and (screen_geom.y() + screen_geom.height()) - (new_pos.y() + h) > 45:
                    pulled_away = True

                if pulled_away:
                    self.model.cling_edge = None

            self.widget.move(new_pos)
            self.model.trigger_wake_up()
            event.accept()

    def handle_mouse_release(self, event: QMouseEvent, screen_geom: Optional[QRect]) -> Optional[str]:
        """
        Handles mouse release.
        Returns:
            "toggle_voice": if it was a quick click to toggle mic (and wasn't just waking up from sleep)
            None: otherwise
        """
        result = None
        if event.button() == Qt.MouseButton.LeftButton:
            if self.model.is_dragging:
                self.model.dizzy_end_time = time.time() + 1.2
                self.model.is_dragging = False
                self.snap_to_edge_if_near(screen_geom)
                self.model.save_position(self.widget.pos())
            elif self.model.drag_distance <= 5:
                if not self.model.was_sleeping_on_press:
                    result = "toggle_voice"

            self.model.was_sleeping_on_press = False
            self.model.trigger_wake_up()
            event.accept()
        return result

    def handle_mouse_double_click(self, event: QMouseEvent) -> bool:
        """Returns True if double click action should be triggered."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.model.trigger_wake_up()
            event.accept()
            return True
        return False

    # ============================================================
    # SCREEN EDGE SNAPPING & CLINGING
    # ============================================================

    def snap_to_edge_if_near(self, screen_geom: Optional[QRect]):
        """Snap to nearest screen boundary if within snap margin, activating cling mode."""
        if not screen_geom:
            return

        cur_x = self.widget.x()
        cur_y = self.widget.y()
        w = self.widget.width()
        h = self.widget.height()

        dist_left = abs(cur_x - screen_geom.left())
        dist_right = abs((screen_geom.x() + screen_geom.width()) - (cur_x + w))
        dist_top = abs(cur_y - screen_geom.top())
        dist_bottom = abs((screen_geom.y() + screen_geom.height()) - (cur_y + h))

        SNAP_THRESHOLD = 50
        min_dist = min(dist_left, dist_right, dist_top, dist_bottom)

        if min_dist <= SNAP_THRESHOLD:
            if min_dist == dist_left:
                self.model.cling_edge = "left"
                target_x = screen_geom.left()
                target_y = max(screen_geom.top(), min(screen_geom.y() + screen_geom.height() - h, cur_y))
            elif min_dist == dist_right:
                self.model.cling_edge = "right"
                target_x = screen_geom.x() + screen_geom.width() - w
                target_y = max(screen_geom.top(), min(screen_geom.y() + screen_geom.height() - h, cur_y))
            elif min_dist == dist_top:
                self.model.cling_edge = "top"
                target_x = max(screen_geom.left(), min(screen_geom.x() + screen_geom.width() - w, cur_x))
                target_y = screen_geom.top()
            else:
                self.model.cling_edge = "bottom"
                target_x = max(screen_geom.left(), min(screen_geom.x() + screen_geom.width() - w, cur_x))
                target_y = screen_geom.y() + screen_geom.height() - h

            self.widget.move(target_x, target_y)
        else:
            self.model.cling_edge = None

    # ============================================================
    # ANIMATION TICK & PHYSICS
    # ============================================================

    def update_tick(self, cursor_pos: QPoint, widget_center: QPoint) -> Tuple[bool, int]:
        """
        Updates physics, idle detection, eye tracking, and animation states.
        Returns:
            (needs_fps_update, new_interval_ms)
        """
        now = time.time()
        model = self.model

        # 1. Cursor Activity Tracking
        cursor_moved = math.hypot(
            cursor_pos.x() - model.last_cursor_pos.x(),
            cursor_pos.y() - model.last_cursor_pos.y()
        )
        model.last_cursor_pos = cursor_pos

        dx = cursor_pos.x() - widget_center.x()
        dy = cursor_pos.y() - widget_center.y()
        dist_to_cursor = math.hypot(dx, dy)

        is_bot_active = model.voice_state in (VoiceState.SPEAKING, VoiceState.THINKING)
        is_cursor_moving_near = (dist_to_cursor < 85.0 and cursor_moved > 2.0) and not model.is_sleeping
        is_interacting = model.is_dragging or is_bot_active or is_cursor_moving_near

        if is_interacting:
            if model.is_sleeping or model.is_drowsy:
                model.trigger_wake_up()
            else:
                model.last_user_activity = now

        # 2. Idle & Sleep State Machine
        idle_time = now - model.last_user_activity
        is_waking_up = now < model.wake_up_until
        was_sleeping = model.is_sleeping

        if model.voice_state == VoiceState.SLEEPING:
            model.is_sleeping = True
            model.is_drowsy = False
            model.drowsy_ratio = 1.0
        elif is_waking_up or is_interacting:
            model.is_sleeping = False
            model.is_drowsy = False
            model.drowsy_ratio = max(0.0, model.drowsy_ratio - 0.2)
        elif idle_time >= model.sleep_timeout_sec:
            model.is_sleeping = True
            model.is_drowsy = False
            model.drowsy_ratio = 1.0
        elif idle_time >= model.drowsy_timeout_sec:
            model.is_drowsy = True
            model.is_sleeping = False
            window = max(1.0, model.sleep_timeout_sec - model.drowsy_timeout_sec)
            model.drowsy_ratio = min(1.0, (idle_time - model.drowsy_timeout_sec) / window)
        else:
            model.is_sleeping = False
            model.is_drowsy = False
            model.drowsy_ratio = 0.0

        if model.is_sleeping and not was_sleeping:
            model.sleep_enter_time = now

        # Eco Power Saving Mode Interval Calculation
        fps_update = False
        new_interval = 22
        if model.is_sleeping and not model.is_power_saving:
            model.is_power_saving = True
            fps_update = True
            new_interval = 100
        elif not model.is_sleeping and model.is_power_saving:
            model.is_power_saving = False
            fps_update = True
            new_interval = 22

        # Smoothly interpolate edge clinging ratio
        target_cling = 1.0 if model.cling_edge else 0.0
        model.cling_ratio += (target_cling - model.cling_ratio) * 0.18

        # Adjust breathing speed based on state
        if model.is_sleeping:
            model.pulse_phase += 0.026
        elif model.is_drowsy:
            model.pulse_phase += 0.035
        else:
            model.pulse_phase += 0.052

        # 3. Cute Sleep Peeking Logic
        if model.is_sleeping:
            if model.peek_eye != 0:
                if now >= model.peek_end_time:
                    model.peek_eye = 0
                    model.next_peek_time = now + random.uniform(4.5, 7.5)
            else:
                if now >= model.next_peek_time:
                    model.peek_eye = random.choice([1, 2])
                    model.peek_end_time = now + random.uniform(1.3, 1.9)
        else:
            model.peek_eye = 0

        # 4. Floating zZz Particles Logic
        if model.is_sleeping:
            if now >= model.next_zzz_time:
                model.next_zzz_time = now + random.uniform(1.2, 1.8)
                head_cx = self.widget.width() / 2.0
                head_cy = (self.widget.height() / 2.0) - 8.0

                vx = random.uniform(0.35, 0.7)
                vy = random.uniform(-0.65, -1.0)
                spawn_x = head_cx + random.uniform(6.0, 15.0)
                spawn_y = head_cy - 12.0

                if model.cling_edge == "left":
                    vx = random.uniform(0.7, 1.2)
                    vy = random.uniform(-0.35, -0.7)
                    spawn_x = head_cx + 10.0
                elif model.cling_edge == "right":
                    vx = random.uniform(-1.2, -0.7)
                    vy = random.uniform(-0.35, -0.7)
                    spawn_x = head_cx - 10.0
                elif model.cling_edge == "top":
                    vx = random.uniform(-0.25, 0.25)
                    vy = random.uniform(0.5, 0.9)
                    spawn_y = head_cy + 8.0

                model.zzz_particles.append({
                    "x": spawn_x,
                    "y": spawn_y,
                    "alpha": 230,
                    "char": random.choice(["z", "Z"]),
                    "size": random.uniform(11.0, 15.0),
                    "vx": vx,
                    "vy": vy
                })

        # Update zZz particles
        surviving = []
        for p in model.zzz_particles:
            p["x"] += p["vx"] + math.sin(p["y"] * 0.08) * 0.25
            p["y"] += p["vy"]
            p["alpha"] -= 2.2
            if p["alpha"] > 0:
                surviving.append(p)
        model.zzz_particles = surviving

        # Update snot bubble pop particles
        if model.bubble_pop_particles:
            surviving_pop = []
            for bp in model.bubble_pop_particles:
                bp["dx"] += bp["vx"]
                bp["dy"] += bp["vy"]
                bp["vy"] += 0.12  # gentle gravity
                bp["alpha"] -= 12.0
                if bp["alpha"] > 0:
                    surviving_pop.append(bp)
            model.bubble_pop_particles = surviving_pop

        # 5. Natural Blinking Logic
        if not model.is_sleeping and not model.is_drowsy:
            if not model.is_blinking and now >= model.next_blink_time:
                model.is_blinking = True
                model.blink_phase = 0.0

            if model.is_blinking:
                model.blink_phase += 0.22
                if model.blink_phase >= math.pi:
                    model.is_blinking = False
                    model.blink_phase = 0.0
                    model.next_blink_time = now + random.uniform(2.5, 5.0)

        # 6. Smooth Eye Tracking toward Global Mouse Cursor
        if not model.is_sleeping:
            try:
                angle = math.atan2(dy, dx)
                max_offset = 4.2
                sensitivity = 45.0
                target_x = math.cos(angle) * min(max_offset, dist_to_cursor / sensitivity)
                target_y = math.sin(angle) * min(max_offset, dist_to_cursor / sensitivity)

                # Add edge cling gaze bias
                if model.cling_edge == "left":
                    target_x = max(target_x, 1.0)
                elif model.cling_edge == "right":
                    target_x = min(target_x, -1.0)
                elif model.cling_edge == "top":
                    target_y = max(target_y, 1.0)
                elif model.cling_edge == "bottom":
                    target_y = min(target_y, -0.6)

                lerp_speed = 0.06 if model.is_drowsy else 0.22
                model.current_eye_x += (target_x - model.current_eye_x) * lerp_speed
                model.current_eye_y += (target_y - model.current_eye_y) * lerp_speed
            except Exception:
                pass

        # 7. Dynamic Mouth & Ear State
        if model.voice_state == VoiceState.SPEAKING:
            model.mouth_open = (math.sin(model.pulse_phase * 3.5) + 1.0) / 2.0
            model.ear_wiggle_angle = math.sin(model.pulse_phase * 2.0) * 3.0
        elif model.voice_state == VoiceState.LISTENING:
            model.mouth_open = 0.1
            model.ear_wiggle_angle = math.sin(model.pulse_phase * 3.0) * 4.5
        elif model.voice_state == VoiceState.THINKING:
            model.mouth_open = 0.0
            model.ear_wiggle_angle = math.sin(model.pulse_phase * 1.5) * 2.0
        elif model.is_sleeping:
            model.mouth_open = 0.0
            model.ear_wiggle_angle = -7.0
        elif model.is_drowsy:
            model.mouth_open = 0.0
            model.ear_wiggle_angle = -4.0 * model.drowsy_ratio
        else:
            model.mouth_open = 0.0
            model.ear_wiggle_angle = math.sin(model.pulse_phase * 0.8) * 1.5

        return (fps_update, new_interval)
