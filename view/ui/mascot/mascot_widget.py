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
    openCollectionRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        # MVC Components
        self.model = MascotModel()
        self.painter = MascotPainter()
        self.controller = MascotController(self.model, self)
        self._collection_dialog = None

        # Load equipped character skin
        try:
            from service.collection import get_collection_service
            self._collection_service = get_collection_service()
            self.painter.set_character(self._collection_service.equipped())
            self._collection_service.on_equip_changed(self.set_character)
        except Exception as e:
            self._collection_service = None
            print(f"[MiniMascotWidget] Collection init: {e}")

        # Widget Dimensions & Window Flags
        self.setFixedSize(120, 120)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("POP AI Chibi Mascot\n• Click đơn: Bật/Tắt Micro\n• Chuột phải: Mở Bộ Sưu Tập Mascot (Gacha / Đổi Skin)\n• Kéo thả: Di chuyển & Bám viền màn hình\n• Bấm đúp: Mở/Ẩn cửa sổ Chat chính")

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

    def showEvent(self, a0):
        super().showEvent(a0)
        if not self.timer.isActive():
            self.timer.start(22)

    def hideEvent(self, a0):
        super().hideEvent(a0)
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

    def mousePressEvent(self, a0: QMouseEvent | None):
        if not a0:
            return
        self.controller.handle_mouse_press(a0)

    def mouseMoveEvent(self, a0: QMouseEvent | None):
        if not a0:
            return
        geom = self._get_screen_geometry()
        self.controller.handle_mouse_move(a0, geom)

    def mouseReleaseEvent(self, a0: QMouseEvent | None):
        if not a0:
            return
        geom = self._get_screen_geometry()
        action = self.controller.handle_mouse_release(a0, geom)
        if action == "toggle_voice":
            self.toggleVoiceRequested.emit()

    def mouseDoubleClickEvent(self, a0: QMouseEvent | None):
        if not a0:
            return
        if self.controller.handle_mouse_double_click(a0):
            self.toggleMainWindowRequested.emit()

    def contextMenuEvent(self, a0):
        from PyQt6.QtCore import Qt
        from PyQt6.QtGui import QGuiApplication

        # Nếu giữ Shift hoặc Ctrl: hiển thị menu tính năng mở rộng
        modifiers = QGuiApplication.keyboardModifiers()
        if modifiers & (Qt.KeyboardModifier.ShiftModifier | Qt.KeyboardModifier.ControlModifier):
            self._show_extended_menu(a0)
            return

        # Chuột phải thông thường: Mở ngay Bộ Sưu Tập Mascot
        self.open_collection_dialog()
        if a0:
            a0.accept()

    def _show_extended_menu(self, a0):
        from PyQt6.QtWidgets import QMenu
        from PyQt6.QtGui import QAction

        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #0F172A;
                color: #FFFFFF;
                border: 1px solid rgba(0, 255, 170, 0.4);
                border-radius: 8px;
                padding: 6px;
                font-family: Arial, sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background: rgba(0, 255, 170, 0.2);
                color: #00FFAA;
            }
            QMenu::separator {
                height: 1px;
                background: rgba(255, 255, 255, 0.1);
                margin: 4px 6px;
            }
        """)

        act_coll = menu.addAction("Bộ Sưu Tập Mascot")
        if act_coll:
            act_coll.triggered.connect(self.open_collection_dialog)

        menu.addSeparator()

        act_chat = menu.addAction("Mở Cửa Sổ Trò Chuyện")
        if act_chat:
            act_chat.triggered.connect(lambda: self.toggleMainWindowRequested.emit())

        act_mic = menu.addAction("Bật / Tắt Micro")
        if act_mic:
            act_mic.triggered.connect(lambda: self.toggleVoiceRequested.emit())

        if self.model.is_sleeping:
            act_sleep = menu.addAction("Đánh Thức Mascot")
            if act_sleep:
                act_sleep.triggered.connect(self.wake_up)
        else:
            act_sleep = menu.addAction("Cho Mascot Đi Ngủ")
            if act_sleep:
                act_sleep.triggered.connect(lambda: self.set_voice_state(VoiceState.SLEEPING))

        menu.addSeparator()

        act_hide = menu.addAction("Ẩn Mascot")
        if act_hide:
            act_hide.triggered.connect(self.hide)

        if a0:
            menu.exec(a0.globalPos())
            a0.accept()

    def set_character(self, char_def):
        """Update active character skin."""
        self.painter.set_character(char_def)
        self.update()

    def open_collection_dialog(self):
        """Open the Collection Dialog modal window."""
        from view.ui.collection import CollectionDialog
        user_key = getattr(self._collection_service, 'user_key', None) if self._collection_service else None
        if not self._collection_dialog:
            self._collection_dialog = CollectionDialog(user_key=user_key, parent=None)
            self._collection_dialog.characterEquipped.connect(self.set_character)
        self._collection_dialog.refresh_wallet()
        self._collection_dialog.show()
        self._collection_dialog.raise_()
        self._collection_dialog.activateWindow()

    # ============================================================
    # PAINT EVENT (DELEGATED TO PAINTER)
    # ============================================================

    def paintEvent(self, a0):
        painter = QPainter(self)
        try:
            self.painter.paint(painter, self.width(), self.height(), self.model)
        finally:
            painter.end()
