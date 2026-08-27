"""
POP Input Bar Widget - Glowing Chat Input Container matching po spec annotation #11.
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize
from PyQt6.QtGui import QKeyEvent, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame, QComboBox
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from view.ui.widgets.model_downloader_dialog import ModelDownloaderDialog


class MessageTextEdit(QTextEdit):
    """Custom Multi-line TextEdit with Shift+Enter / Enter key handler."""

    sendRequested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setPlaceholderText("Nhập tin nhắn cho POP...")
        self.setFixedHeight(38)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            "QTextEdit { border: none; background: transparent; font-size: 14px; color: #E6F4FF; padding: 4px 0; }"
        )

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                super().keyPressEvent(event)
            else:
                self.sendRequested.emit()
                event.accept()
        else:
            super().keyPressEvent(event)


class InputBarWidget(QWidget):
    """Bottom input box container matching annotation #11 with responsive layout scaling."""

    sendMessage = pyqtSignal(str)
    voiceToggle = pyqtSignal()
    attachmentClicked = pyqtSignal()
    switchModel = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 10)
        main_layout.setSpacing(6)

        # ----------------------------------------------------
        # GLOWING INPUT CONTAINER
        # ----------------------------------------------------
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setMaximumWidth(960)
        self.input_frame.setStyleSheet(
            f"QFrame#inputFrame {{ background-color: rgba(16, 22, 31, 0.9); border: 1px solid rgba(0, 255, 255, 0.3); border-radius: 24px; }}"
            f"QFrame#inputFrame:hover {{ border-color: rgba(0, 255, 255, 0.6); }}"
        )
        box_layout = QHBoxLayout(self.input_frame)
        box_layout.setContentsMargins(14, 6, 10, 6)
        box_layout.setSpacing(8)

        # Attachment Button (Paperclip)
        self.attach_btn = QPushButton()
        self.attach_btn.setIcon(create_vector_icon("attachment", "#96D7E9", 20))
        self.attach_btn.setFixedSize(36, 36)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip("Tải lên tệp / ảnh")
        self.attach_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(255,255,255,0.08); border-radius: 18px; }")
        self.attach_btn.clicked.connect(lambda: self.attachmentClicked.emit())

        # Text Input Area
        self.text_edit = MessageTextEdit()
        self.text_edit.sendRequested.connect(self._handle_send)

        # Model Selector Pill (Transparent, No Frame)
        self.model_combo = QComboBox()
        self.model_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self.model_combo.setStyleSheet(
            f"QComboBox {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; "
            f"font-size: 12px; font-weight: 600; border: none; padding: 2px 4px; }}"
            f"QComboBox:hover {{ color: {DesignTokens.TEXT_MAIN}; }}"
            f"QComboBox::drop-down {{ border: none; width: 12px; }}"
            f"QComboBox QAbstractItemView {{ background-color: {DesignTokens.SURFACE_2}; color: {DesignTokens.TEXT_MAIN}; selection-background-color: {DesignTokens.SURFACE_3}; border-radius: 8px; }}"
        )
        self._load_local_models()
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        # Voice Microphone Button
        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(create_vector_icon("mic", "#96D7E9", 20))
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("Bật/tắt micro")
        self.mic_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0,255,255,0.12); border-radius: 18px; }")
        self.mic_btn.clicked.connect(lambda: self.voiceToggle.emit())

        # Send Button (Cyan filled circle)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(create_vector_icon("send", "#03050B", 18))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Gửi tin nhắn")
        self.send_btn.setStyleSheet(
            f"QPushButton {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); border: none; border-radius: 18px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #00A6FF, stop:1 #33FFBC); }}"
        )
        self.send_btn.clicked.connect(self._handle_send)

        box_layout.addWidget(self.attach_btn)
        box_layout.addWidget(self.text_edit, stretch=1)
        box_layout.addWidget(self.model_combo)
        box_layout.addWidget(self.send_btn)

        # Center input frame container
        frame_wrapper = QHBoxLayout()
        frame_wrapper.setContentsMargins(0, 0, 0, 0)
        frame_wrapper.addStretch()
        frame_wrapper.addWidget(self.input_frame, stretch=10)
        frame_wrapper.addStretch()

        main_layout.addLayout(frame_wrapper)

        # ----------------------------------------------------
        # KEYBOARD SHORTCUT / DISCLAIMER CAPTION
        # ----------------------------------------------------
        self.sub_text_lbl = QLabel("Enter để gửi • Shift + Enter để xuống dòng")
        self.sub_text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")
        main_layout.addWidget(self.sub_text_lbl)

    def _handle_send(self):
        text = self.text_edit.toPlainText().strip()
        if text:
            self.sendMessage.emit(text)
            self.text_edit.clear()

    def _format_model_name(self, raw_name: str) -> str:
        name = raw_name
        # Xử lý định dạng cache folder của HuggingFace: models--Org--RepoName
        if name.startswith("models--"):
            parts = name.split("--")
            if len(parts) >= 3:
                name = parts[2]
            elif len(parts) == 2:
                name = parts[1]

        if name.endswith(".gguf"):
            name = name[:-5]
        if "/" in name:
            name = name.split("/")[-1]

        for sub in ["-Instruct", "-GGUF", "-gguf", "-Chat", "-chat"]:
            name = name.replace(sub, "")

        name = name.replace("_", " ").replace("-", " ").strip()

        if "LFM" in name and "LFM " not in name:
            name = name.replace("LFM", "LFM ")

        return name if name else raw_name

    def _load_local_models(self):
        from view.ui.settings import load_user_settings
        settings = load_user_settings()
        agent_dir = settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))

        self.model_combo.clear()
        models = []
        if os.path.exists(agent_dir):
            for item in os.listdir(agent_dir):
                if item.startswith('.'): continue
                if os.path.isdir(os.path.join(agent_dir, item)) or item.endswith(".gguf"):
                    models.append(self._format_model_name(item))
        if not models:
            models.append("LFM 2.5 2.6B")
        
        self.model_combo.addItems(models)
        self.model_combo.addItem("[ + Custom model... ]")
        self._last_selected_model = self.model_combo.currentText()

    def _on_model_changed(self, index):
        text = self.model_combo.currentText()
        if not text:
            return
        if text == "[ + Custom model... ]":
            self.model_combo.setCurrentText(self._last_selected_model)
            from view.ui.settings import SettingsDialog
            dialog = SettingsDialog(username="Tài khoản", initial_tab=1, parent=self)
            dialog.modelDownloaded.connect(self._load_local_models)
            dialog.exec()
        else:
            self._last_selected_model = text
            self.switchModel.emit(text)

    def set_listening(self, is_listening: bool):
        pass
