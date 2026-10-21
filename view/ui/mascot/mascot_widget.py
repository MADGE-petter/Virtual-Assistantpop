"""
POP Mini Floating Mascot Widget - Interactive Desktop Chibi Cyber-Pet.
Follows MVC architecture:
- Model: view.ui.mascot.mascot_model.MascotModel
- View: view.ui.mascot.mascot_painter.MascotPainter
- Controller: view.ui.mascot.mascot_controller.MascotController
"""

from PyQt6.QtCore import Qt, QPoint, QTimer, pyqtSignal, QRect
from PyQt6.QtGui import QPainter, QMouseEvent, QCursor, QGuiApplication
from PyQt6.QtWidgets import QWidget

from model.voice_state_model import VoiceState
from view.ui.mascot.mascot_model import MascotModel
from view.ui.mascot.mascot_painter import MascotPainter
from view.ui.mascot.mascot_controller import MascotController


class MiniMascotWidget(QWidget):
    """
    Always-On-Top Interactive Chibi Desktop Mascot with MVC Architecture.
    - 4 Limbs & Wagging Mecha Tail
    - Cyber Heart Arc Reactor
    - 360° Cursor Tracking & Gaze Following
    - Screen Edge Clinging & Hanging (Left, Right, Top, Bottom)
    - Autonomous Idle Sleep & Power Saving Eco Mode
    """

    toggleMainWindowRequested = pyqtSignal()
    toggleVoiceRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # MVC Components
        self.model = MascotModel()
        self.painter = MascotPainter()
        self.controller = MascotController(self.model, self)

        # Widget Dimensions & Window Flags
        self.setFixedSize(120, 120)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("POP AI Chibi Mascot\n• Click đơn: Bật/Tắt Micro\n• Kéo thả: Di chuyển & Bám viền màn hình\n• Bấm đúp: Mở/Ẩn cửa sổ Chat chính")

        # Load saved desktop position & screen edge snap
        saved_pos = self.model.load_saved_position()
        if saved_pos:
            self.move(saved_pos)
            self._snap_to_edge_if_near()

        # 45 FPS Animation Timer (Auto drops to 10 FPS during sleep to save resources)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)

    # ============================================================
    # COMPATIBILITY ACCESSORS
    # ============================================================

    @property
    def voice_state(self) -> VoiceState:
        return self.model.voice_state

    @voice_state.setter
    def voice_state(self, state: VoiceState):
        self.set_voice_state(state)

    @property
    def _settings(self):
        return self.model.settings

    @property
    def _is_sleeping(self) -> bool:
        return self.model.is_sleeping

    @property
    def _is_drowsy(self) -> bool:
        return self.model.is_drowsy

    @property
    def _cling_edge(self):
        return self.model.cling_edge

    # ============================================================
    # LIFECYCLE & SETTINGS
    # ============================================================

    def reload_settings(self):
        """Reload configuration from user settings."""
        self.model.reload_settings()

    def showEvent(self, event):
        super().showEvent(event)
        if not self.timer.isActive():
            self.timer.start(22)

    def hideEvent(self, event):
        super().hideEvent(event)
        if self.timer.isActive():
            self.timer.stop()

    def set_voice_state(self, state: VoiceState):
        """Update voice state and sync sleep/active triggers."""
        self.model.voice_state = state
        if state == VoiceState.SLEEPING:
            self.model.is_sleeping = True
            self.model.is_drowsy = False
            self.model.drowsy_ratio = 1.0
            self.model.zzz_particles.clear()
        elif state in (VoiceState.SPEAKING, VoiceState.THINKING):
            self.wake_up()
        self.update()

    def wake_up(self):
        """Wake up mascot and restore full 45 FPS performance."""
        self.model.trigger_wake_up()
        if self.model.is_power_saving:
            self.model.is_power_saving = False
            self.timer.setInterval(22)
        self.update()

    # ============================================================
    # ANIMATION TICK
    # ============================================================

    def _animate(self):
        if not self.isVisible():
            if self.timer.isActive():
                self.timer.stop()
            return

        cursor_pos = QCursor.pos()
        widget_center = self.mapToGlobal(QPoint(int(self.width() / 2), int(self.height() / 2)))

        fps_update, new_interval = self.controller.update_tick(cursor_pos, widget_center)
        if fps_update:
            self.timer.setInterval(new_interval)

        self.update()

    # ============================================================
    # SCREEN GEOMETRY HELPER
    # ============================================================

    def _get_screen_geometry(self) -> QRect:
        screen = self.screen() or QGuiApplication.primaryScreen()
        if screen:
            return screen.availableGeometry()
        return QRect(0, 0, 1920, 1080)

    def _snap_to_edge_if_near(self):
        geom = self._get_screen_geometry()
        self.controller.snap_to_edge_if_near(geom)

    # ============================================================
    # MOUSE EVENTS (DELEGATED TO CONTROLLER)
    # ============================================================

    def mousePressEvent(self, event: QMouseEvent):
        self.controller.handle_mouse_press(event)

    def mouseMoveEvent(self, event: QMouseEvent):
        geom = self._get_screen_geometry()
        self.controller.handle_mouse_move(event, geom)

    def mouseReleaseEvent(self, event: QMouseEvent):
        geom = self._get_screen_geometry()
        action = self.controller.handle_mouse_release(event, geom)
        if action == "toggle_voice":
            self.toggleVoiceRequested.emit()

    def mouseDoubleClickEvent(self, event: QMouseEvent):
        if self.controller.handle_mouse_double_click(event):
            self.toggleMainWindowRequested.emit()

    # ============================================================
    # PAINT EVENT (DELEGATED TO PAINTER)
    # ============================================================

    def paintEvent(self, event):
        painter = QPainter(self)
        try:
            self.painter.paint(painter, self.width(), self.height(), self.model)
        finally:
            painter.end()
