"""
POP InputBarWidget - Giao diện thanh nhập liệu trò chuyện phát sáng (View Layer).
Tuân thủ nghiêm ngặt mô hình MVC:
- Chịu trách nhiệm hiển thị UI, bố cục các nút và thẻ preview tệp.
- Bắt sự kiện người dùng và phát tín hiệu cho InputBarController xử lý.
- Cung cấp các phương thức công khai để Controller cập nhật dữ liệu hiển thị.
"""

import os
from typing import Optional, List
from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from view.ui.widgets.input_bar.message_text_edit import MessageTextEdit
from view.ui.widgets.input_bar.model_combo_box import ModelComboBox, ModelItemDelegate
from view.ui.widgets.input_bar.attached_file_square import AttachedFileSquare


class InputBarWidget(QWidget):
    """
    Thanh nhập tin nhắn phát sáng (Annotation #11).
    Đóng vai trò thuần túy là View trong kiến trúc MVC.
    """

    # Public signals kết nối với bên ngoài (ChatAreaWidget / PopView)
    sendMessage = pyqtSignal(str)
    voiceToggle = pyqtSignal()
    attachmentClicked = pyqtSignal()
    switchModel = pyqtSignal(str)

    # Internal signals gửi tới Controller
    sendActionRequested = pyqtSignal(str)
    attachFileRequested = pyqtSignal()
    removeFileRequested = pyqtSignal(str)
    modelChangeRequested = pyqtSignal(str)
    openModelHubRequested = pyqtSignal()
    voiceToggleRequested = pyqtSignal()

    def __init__(self, parent=None, controller=None):
        super().__init__(parent)
        self._selected_model_index = 0
        self._setup_ui()

        # Khởi tạo hoặc gắn Controller (đảm bảo tính tương thích và độc lập MVC)
        if controller is not None:
            self.set_controller(controller)
        else:
            from controller.input_bar_controller import InputBarController
            self.set_controller(InputBarController(view=self))

    def set_controller(self, controller):
        """Thiết lập Controller và đồng bộ hóa các signals."""
        self.controller = controller
        if self.controller.view != self:
            self.controller.set_view(self)

        # Kết nối các tín hiệu chuyển tiếp ra ngoài
        self.controller.sendMessage.connect(self.sendMessage.emit)
        self.controller.voiceToggle.connect(self.voiceToggle.emit)
        self.controller.switchModel.connect(self.switchModel.emit)
        self.controller.attachmentClicked.connect(self.attachmentClicked.emit)

        # Nạp dữ liệu ban đầu
        self.controller.load_local_models()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 4, 16, 10)
        main_layout.setSpacing(6)

        # ----------------------------------------------------
        # GLOWING INPUT CONTAINER
        # ----------------------------------------------------
        self.input_frame = QFrame()
        self.input_frame.setObjectName("inputFrame")
        self.input_frame.setMaximumWidth(820)
        self.input_frame.setStyleSheet(
            f"QFrame#inputFrame {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 22px; }}"
            f"QFrame#inputFrame:hover {{ border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; background: rgba(255, 255, 255, 0.03); }}"
        )
        frame_layout = QVBoxLayout(self.input_frame)
        frame_layout.setContentsMargins(14, 6, 10, 6)
        frame_layout.setSpacing(4)

        # ----------------------------------------------------
        # ATTACHMENT SQUARES ROW (Cards preview 3x3)
        # ----------------------------------------------------
        self.attachment_box = QWidget()
        self.attachment_box.setStyleSheet("background: transparent; border: none;")
        self.attach_cards_layout = QHBoxLayout(self.attachment_box)
        self.attach_cards_layout.setContentsMargins(4, 2, 4, 4)
        self.attach_cards_layout.setSpacing(8)

        self.attachment_box.hide()
        frame_layout.addWidget(self.attachment_box)

        # ----------------------------------------------------
        # INPUT CONTROLS ROW
        # ----------------------------------------------------
        box_layout = QHBoxLayout()
        box_layout.setContentsMargins(0, 0, 0, 0)
        box_layout.setSpacing(8)

        # Attachment Button (Dấu cộng)
        self.attach_btn = QPushButton()
        self.attach_btn.setIcon(create_vector_icon("plus", DesignTokens.TEXT_SECONDARY, 18))
        self.attach_btn.setIconSize(QSize(18, 18))
        self.attach_btn.setFixedSize(36, 36)
        self.attach_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.attach_btn.setToolTip("Đính kèm tệp tin")
        self.attach_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.10); border-radius: 18px; }"
        )
        self.attach_btn.clicked.connect(lambda: self.attachFileRequested.emit())

        # Text Input Area
        self.text_edit = MessageTextEdit()
        self.text_edit.sendRequested.connect(self._handle_send_action)

        # Model selector dropdown
        self.model_combo = ModelComboBox()
        self.model_combo.setStyleSheet(
            f"QComboBox {{ background: transparent; color: {DesignTokens.TEXT_MUTED}; "
            f"font-size: 12px; font-weight: 600; border: none; padding: 2px 4px; }}"
            f"QComboBox:hover {{ color: {DesignTokens.TEXT_MAIN}; }}"
            f"QComboBox::drop-down {{ border: none; width: 12px; }}"
            f"QComboBox QAbstractItemView {{ "
            f"background-color: rgba(12, 18, 32, 0.65); "
            f"border: 1px solid rgba(255, 255, 255, 0.15); "
            f"border-radius: 12px; padding: 4px 2px; outline: none; "
            f"selection-background-color: transparent; }}"
        )
        self.model_combo.currentIndexChanged.connect(self._on_combo_index_changed)

        # Voice Microphone Button
        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(create_vector_icon("mic", DesignTokens.TEXT_SECONDARY, 18))
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("Bật/tắt micro")
        self.mic_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0, 255, 170, 0.12); border-radius: 18px; }")
        self.mic_btn.clicked.connect(lambda: self.voiceToggleRequested.emit())

        # Send Button
        self.send_btn = QPushButton()
        self.send_btn.setIcon(create_vector_icon("send", "#FFFFFF", 20))
        self.send_btn.setIconSize(QSize(20, 20))
        self.send_btn.setFixedSize(36, 36)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setToolTip("Gửi tin nhắn")
        self.send_btn.setStyleSheet(
            "QPushButton { "
            "background: transparent; "
            "border: none; "
            "border-radius: 18px; "
            "} "
            "QPushButton:hover { "
            "background: rgba(255, 255, 255, 0.12); "
            "border: none; "
            "} "
            "QPushButton:pressed { "
            "background: rgba(255, 255, 255, 0.22); "
            "border: none; "
            "}"
        )
        self.send_btn.clicked.connect(self._handle_send_action)

        box_layout.addWidget(self.attach_btn)
        box_layout.addWidget(self.text_edit, stretch=1)
        box_layout.addWidget(self.model_combo)
        box_layout.addWidget(self.send_btn)

        frame_layout.addLayout(box_layout)

        # Center input frame container
        frame_wrapper = QHBoxLayout()
        frame_wrapper.setContentsMargins(0, 0, 0, 0)
        frame_wrapper.addStretch()
        frame_wrapper.addWidget(self.input_frame, stretch=10)
        frame_wrapper.addStretch()

        main_layout.addLayout(frame_wrapper)

        # ----------------------------------------------------
        # INPUT HINT
        # ----------------------------------------------------
        self.sub_text_lbl = QLabel("Enter để gửi • Shift + Enter để xuống dòng")
        self.sub_text_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sub_text_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 11px;")
        main_layout.addWidget(self.sub_text_lbl)

    # ----------------------------------------------------
    # VIEW INTERFACES & METHODS (Được Controller gọi)
    # ----------------------------------------------------

    def set_models(self, models: List[str]):
        """Cập nhật danh sách các mô hình trên ComboBox."""
        previous_signal_state = self.model_combo.blockSignals(True)
        self.model_combo.clear()

        # Item 0: Auto
        self.model_combo.addItem("Auto")
        self.model_combo.setItemData(0, "Tự động chọn mô hình phù hợp", Qt.ItemDataRole.ToolTipRole)

        # Local model items
        for i, m in enumerate(models, 1):
            self.model_combo.addItem(m)
            self.model_combo.setItemData(i, m, Qt.ItemDataRole.ToolTipRole)

        # Hub item: Model++
        hub_idx = self.model_combo.count()
        self.model_combo.addItem(
            create_vector_icon("download", DesignTokens.TEXT_SECONDARY, 14),
            "Model++",
            "__model_hub__",
        )
        self.model_combo.setItemData(hub_idx, "Mở kho mô hình để tải thêm mô hình AI", Qt.ItemDataRole.ToolTipRole)

        self.model_combo.setCurrentIndex(0)
        self._selected_model_index = 0
        self.model_combo.blockSignals(previous_signal_state)

    def render_attached_files(self, file_paths: List[str]):
        """Hiển thị các thẻ tệp đính kèm trên giao diện."""
        # Xóa các card cũ trong layout
        while self.attach_cards_layout.count() > 0:
            item = self.attach_cards_layout.takeAt(0)
            if item is not None:
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()

        if not file_paths:
            self.attachment_box.hide()
            self.text_edit.setPlaceholderText("Nhập tin nhắn cho POP...")
            return

        for path in file_paths:
            card = AttachedFileSquare(path)
            card.removeRequested.connect(lambda p: self.removeFileRequested.emit(p))
            self.attach_cards_layout.addWidget(card)

        self.attach_cards_layout.addStretch()
        self.attachment_box.show()

        count = len(file_paths)
        if count == 1:
            fname = os.path.basename(file_paths[0])
            self.text_edit.setPlaceholderText(f"Nhập câu hỏi về {fname} hoặc bấm Enter / Gửi để phân tích...")
        else:
            self.text_edit.setPlaceholderText(f"Nhập câu hỏi về {count} tệp đính kèm hoặc bấm Enter / Gửi...")

    def clear_input(self):
        """Xóa văn bản trong ô nhập liệu."""
        self.text_edit.clear()

    def get_text(self) -> str:
        """Lấy văn bản đang có trong ô nhập liệu."""
        return self.text_edit.toPlainText()

    def set_listening(self, is_listening: bool):
        """Cập nhật trạng thái lắng nghe giọng nói (nếu cần)."""
        pass

    # ----------------------------------------------------
    # TƯƠNG THÍCH NGƯỢC (BACKWARD COMPATIBILITY HELPERS)
    # ----------------------------------------------------

    def _load_local_models(self):
        """Phương thức hỗ trợ tương thích ngược với pop_view."""
        if hasattr(self, "controller") and self.controller:
            self.controller.load_local_models()

    def add_attached_files(self, file_paths: List[str]):
        if hasattr(self, "controller") and self.controller:
            self.controller.add_attached_files(file_paths)

    def set_attached_file(self, file_path: str):
        self.add_attached_files([file_path])

    def remove_attached_file(self, file_path: str):
        if hasattr(self, "controller") and self.controller:
            self.controller.handle_remove_file(file_path)

    def clear_attached_files(self):
        if hasattr(self, "controller") and self.controller:
            self.controller.clear_attached_files()

    def clear_attached_file(self):
        self.clear_attached_files()

    # ----------------------------------------------------
    # XỬ LÝ SỰ KIỆN NỘI BỘ (VIEW EVENT HANDLERS)
    # ----------------------------------------------------

    def _handle_send_action(self):
        text = self.text_edit.toPlainText()
        self.sendActionRequested.emit(text)

    def _on_combo_index_changed(self, index: int):
        text = self.model_combo.currentText()
        if not text:
            return

        if self.model_combo.itemData(index, Qt.ItemDataRole.UserRole) == "__model_hub__":
            # Khôi phục lại index trước đó trên dropdown để không bị chọn nhầm Model++
            self.model_combo.blockSignals(True)
            self.model_combo.setCurrentIndex(self._selected_model_index)
            self.model_combo.blockSignals(False)
            self.openModelHubRequested.emit()
            return

        self._selected_model_index = index
        self.modelChangeRequested.emit(text)
