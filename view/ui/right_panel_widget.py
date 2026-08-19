"""
POP Right Panel Widget - Voice Visualizer, System Telemetry Monitor, and Activity Log matching po spec (#12, #13, #14, #15).
"""

from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QRectF
from PyQt6.QtGui import QPainter, QColor, QBrush, QLinearGradient, QPen
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QProgressBar, QScrollArea, QSizePolicy
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from model.voice_state_model import VoiceStateModel, VoiceState
from model.system_monitor_model import SystemMonitorModel, SystemMetrics
from model.activity_log_model import ActivityLogModel


class AudioWaveformWidget(QWidget):
    """Animated Waveform Visualizer Bar Component (po #13)."""

    def __init__(self, voice_model: VoiceStateModel, parent=None):
        super().__init__(parent)
        self.voice_model = voice_model
        self.setFixedHeight(50)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(40)  # ~25 FPS

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        amplitudes = self.voice_model.generate_waveform()

        bar_count = len(amplitudes)
        gap = 3
        bw = max(2.0, (w - (bar_count - 1) * gap) / float(bar_count))

        gradient = QLinearGradient(0, h, 0, 0)
        gradient.setColorAt(0.0, QColor(0, 142, 255))
        gradient.setColorAt(0.6, QColor(0, 255, 255))
        gradient.setColorAt(1.0, QColor(0, 255, 170))

        painter.setBrush(QBrush(gradient))
        painter.setPen(Qt.PenStyle.NoPen)

        for i, amp in enumerate(amplitudes):
            bx = i * (bw + gap)
            bh = max(4.0, h * amp)
            by = (h - bh) / 2.0
            painter.drawRoundedRect(QRectF(bx, by, bw, bh), bw / 2.0, bw / 2.0)


class MetricBarWidget(QWidget):
    """Hardware Metric Bar Widget with Percentage (po #14)."""

    def __init__(self, label: str, icon_str: str = "⚙", parent=None):
        super().__init__(parent)
        self.label_str = label
        self._setup_ui(icon_str)

    def _setup_ui(self, icon_str: str):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 3, 0, 3)
        layout.setSpacing(8)

        self.name_lbl = QLabel(f"{icon_str} {self.label_str}")
        self.name_lbl.setFixedWidth(75)
        self.name_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_SECONDARY}; font-size: 11px; font-weight: 500;")

        self.progress = QProgressBar()
        self.progress.setFixedHeight(8)
        self.progress.setTextVisible(False)
        self.progress.setStyleSheet(
            f"QProgressBar {{ background-color: {DesignTokens.SURFACE_3}; border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); border-radius: 4px; }}"
        )

        self.val_lbl = QLabel("0%")
        self.val_lbl.setFixedWidth(40)
        self.val_lbl.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.val_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 11px; font-weight: 600;")

        layout.addWidget(self.name_lbl)
        layout.addWidget(self.progress, stretch=1)
        layout.addWidget(self.val_lbl)

    def set_value(self, val_float: float, suffix: str = "%"):
        val_int = max(0, min(100, int(val_float)))
        self.progress.setValue(val_int)
        self.val_lbl.setText(f"{int(val_float)}{suffix}")


class RightPanelWidget(QWidget):
    """Right Control & Telemetry Panel Widget (po #12, #13, #14, #15)."""

    closeRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumWidth(260)
        self.setMaximumWidth(260)
        self.setObjectName("rightPanel")

        self.voice_model = VoiceStateModel()
        self.monitor_model = SystemMonitorModel()
        self.activity_model = ActivityLogModel()

        self._setup_ui()

        # Monitor refresh timer (1 second)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh_telemetry)
        self.timer.start(1000)

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 14, 12, 14)
        main_layout.setSpacing(14)

        # ----------------------------------------------------
        # 12. PANEL TOGGLE HEADER
        # ----------------------------------------------------
        toggle_layout = QHBoxLayout()
        toggle_layout.setSpacing(6)

        header_lbl = QLabel("PANEL TOGGLE")
        header_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1px;")

        toggle_btns = QHBoxLayout()
        toggle_btns.setSpacing(4)
        for icon_name in ["panel_toggle", "dots", "settings"]:
            btn = QPushButton()
            btn.setIcon(create_vector_icon(icon_name, "#557088", 14))
            btn.setFixedSize(24, 24)
            btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 4px; }")
            toggle_btns.addWidget(btn)

        toggle_layout.addWidget(header_lbl, stretch=1)
        toggle_layout.addLayout(toggle_btns)
        main_layout.addLayout(toggle_layout)

        # ----------------------------------------------------
        # 13. VOICE STATUS & VISUALIZER CARD
        # ----------------------------------------------------
        voice_card = QFrame()
        voice_card.setStyleSheet(f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 12px; }}")
        vc_layout = QVBoxLayout(voice_card)
        vc_layout.setContentsMargins(12, 10, 12, 10)
        vc_layout.setSpacing(8)

        vc_title = QLabel("VOICE STATUS")
        vc_title.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")

        self.waveform_widget = AudioWaveformWidget(self.voice_model)

        status_box = QHBoxLayout()
        status_box.setSpacing(6)
        self.status_dot = QLabel("🟢")
        self.status_dot.setStyleSheet("font-size: 10px;")

        self.status_state_lbl = QLabel("READY")
        self.status_state_lbl.setStyleSheet(f"color: {DesignTokens.CYAN_ACCENT}; font-size: 12px; font-weight: 700;")

        status_box.addWidget(self.status_dot)
        status_box.addWidget(self.status_state_lbl, stretch=1)

        self.status_sub_lbl = QLabel("Sẵn sàng nhận lệnh")
        self.status_sub_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")

        vc_layout.addWidget(vc_title)
        vc_layout.addWidget(self.waveform_widget)
        vc_layout.addLayout(status_box)
        vc_layout.addWidget(self.status_sub_lbl)

        main_layout.addWidget(voice_card)

        # ----------------------------------------------------
        # 14. SYSTEM MONITOR CARD
        # ----------------------------------------------------
        sys_card = QFrame()
        sys_card.setStyleSheet(f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 12px; }}")
        sc_layout = QVBoxLayout(sys_card)
        sc_layout.setContentsMargins(12, 10, 12, 10)
        sc_layout.setSpacing(6)

        sc_title = QLabel("SYSTEM MONITOR")
        sc_title.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        sc_layout.addWidget(sc_title)

        self.cpu_bar = MetricBarWidget("CPU", "⚡")
        self.ram_bar = MetricBarWidget("RAM", "💾")
        self.gpu_bar = MetricBarWidget("GPU", "🎮")
        self.vram_bar = MetricBarWidget("VRAM", "📼")
        self.temp_bar = MetricBarWidget("TEMP", "🌡")

        sc_layout.addWidget(self.cpu_bar)
        sc_layout.addWidget(self.ram_bar)
        sc_layout.addWidget(self.gpu_bar)
        sc_layout.addWidget(self.vram_bar)
        sc_layout.addWidget(self.temp_bar)

        main_layout.addWidget(sys_card)

        # ----------------------------------------------------
        # 15. ACTIVITY LOG CARD
        # ----------------------------------------------------
        act_card = QFrame()
        act_card.setStyleSheet(f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 12px; }}")
        ac_layout = QVBoxLayout(act_card)
        ac_layout.setContentsMargins(12, 10, 12, 10)
        ac_layout.setSpacing(8)

        ac_title = QLabel("ACTIVITY LOG")
        ac_title.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px; font-weight: 700; letter-spacing: 1px;")
        ac_layout.addWidget(ac_title)

        self.log_container = QWidget()
        self.log_layout = QVBoxLayout(self.log_container)
        self.log_layout.setContentsMargins(0, 0, 0, 0)
        self.log_layout.setSpacing(4)

        log_scroll = QScrollArea()
        log_scroll.setWidgetResizable(True)
        log_scroll.setFrameShape(QFrame.Shape.NoFrame)
        log_scroll.setFixedHeight(110)
        log_scroll.setWidget(self.log_container)

        ac_layout.addWidget(log_scroll)
        main_layout.addWidget(act_card, stretch=1)

        # Initial data render
        self._refresh_telemetry()
        self._render_activity_logs()

    def _refresh_telemetry(self):
        m = self.monitor_model.update_metrics()
        self.cpu_bar.set_value(m.cpu_percent)
        self.ram_bar.set_value(m.ram_percent)
        self.gpu_bar.set_value(m.gpu_percent)
        self.vram_bar.set_value(m.vram_percent)
        self.temp_bar.set_value(m.temp_celsius, "°C")

    def _render_activity_logs(self):
        while self.log_layout.count():
            item = self.log_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        for item in self.activity_model.get_logs()[:6]:
            row = QHBoxLayout()
            row.setSpacing(6)

            t_lbl = QLabel(item.timestamp)
            t_lbl.setFixedWidth(54)
            t_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 10px;")

            e_lbl = QLabel(item.event)
            e_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 11px;")

            row.addWidget(t_lbl)
            row.addWidget(e_lbl, stretch=1)

            w = QWidget()
            w.setLayout(row)
            self.log_layout.addWidget(w)

    def set_voice_state(self, state: VoiceState):
        self.voice_model.set_state(state)
        self.status_state_lbl.setText(self.voice_model.STATE_LABELS[state])
        self.status_sub_lbl.setText(self.voice_model.STATE_SUBTITLES[state])
        dots = {
            VoiceState.READY: "🟢",
            VoiceState.LISTENING: "🔵",
            VoiceState.THINKING: "🟡",
            VoiceState.SPEAKING: "🟣",
            VoiceState.SLEEPING: "🌙",
        }
        self.status_dot.setText(dots.get(state, "🟢"))

    def add_activity_log(self, event: str, category: str = "info"):
        self.activity_model.add_log(event, category)
        self._render_activity_logs()
