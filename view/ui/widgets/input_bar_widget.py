"""
POP Input Bar Widget - Glowing Chat Input Container matching po spec annotation #11.
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal, QEvent, QSize, QRect, QRectF
from PyQt6.QtGui import QKeyEvent, QColor, QPainter, QPen, QBrush, QIcon, QPixmap
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFrame,
    QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QStyle
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon


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


class ModelItemDelegate(QStyledItemDelegate):
    """Custom item delegate to render semi-transparent dropdown items,
    horizontal dividing lines between all rows, and distinct hover brightening."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = option.rect
        # Hovered or selected state
        is_hovered = bool(option.state & (QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_Selected))

        # 1. Background highlight on hover
        if is_hovered:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(255, 255, 255, 38)))
            painter.drawRoundedRect(QRectF(rect.adjusted(4, 2, -4, -2)), 6, 6)
        else:
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(QColor(0, 0, 0, 0)))
            painter.drawRect(rect)

        # 2. Icon (e.g. Model++ download icon)
        icon = index.data(Qt.ItemDataRole.DecorationRole)
        text_x = rect.left() + 14
        if isinstance(icon, QIcon) and not icon.isNull():
            icon_size = 14
            icon_y = rect.top() + (rect.height() - icon_size) // 2
            icon.paint(painter, text_x, icon_y, icon_size, icon_size)
            text_x += icon_size + 8

        # 3. Text rendering
        text = index.data(Qt.ItemDataRole.DisplayRole) or ""
        font = painter.font()
        font.setFamily("Arial")
        if is_hovered:
            font.setBold(True)
            painter.setFont(font)
            painter.setPen(QColor("#FFFFFF"))
        else:
            font.setBold(False)
            painter.setFont(font)
            painter.setPen(QColor("#8E9EB2"))

        text_rect = QRect(text_x, rect.top(), rect.right() - text_x - 10, rect.height())
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, text)

        # 4. Horizontal divider line at the bottom of each row
        # (user explicitly requested: "mỗi dòng đều có dấu kẻ ngang ngăn cách")
        divider_pen = QPen(QColor(255, 255, 255, 30), 1)
        painter.setPen(divider_pen)
        painter.drawLine(rect.left() + 8, rect.bottom(), rect.right() - 8, rect.bottom())

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index):
        return QSize(option.rect.width(), 36)


class ModelComboBox(QComboBox):
    """Custom ComboBox for Model selection with semi-transparent popup,
    dividers between rows, and smooth hover illumination."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumWidth(80)
        self.setMaximumWidth(220)
        self.setMaxVisibleItems(12)
        self.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)

        # Do not truncate model names in the dropdown list & enable transparency
        view = self.view()
        if view is not None:
            view.setTextElideMode(Qt.TextElideMode.ElideNone)
            view.setMouseTracking(True)
            view.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
            if view.viewport() is not None:
                view.viewport().setMouseTracking(True)
                view.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setItemDelegate(ModelItemDelegate(self))

    def showPopup(self):
        fm = self.fontMetrics()
        # Generous minimum width so Model++ and long names have plenty of room
        optimal_width = 240
        for i in range(self.count()):
            text = self.itemText(i)
            # Add margin for icon, checkmark, padding, and vertical scrollbar
            item_width = fm.horizontalAdvance(text) + 64
            if item_width > optimal_width:
                optimal_width = item_width

        optimal_width = min(optimal_width, 480)
        view = self.view()
        if view is not None:
            view.setMinimumWidth(optimal_width)

        super().showPopup()

        # Align popup to the right edge and ensure translucent container
        if view is not None:
            container = view.window()
            if isinstance(container, QWidget):
                container.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
                container.setWindowFlags(Qt.WindowType.Popup | Qt.WindowType.FramelessWindowHint | Qt.WindowType.NoDropShadowWindowHint)
                combo_right = self.mapToGlobal(self.rect().topRight()).x()
                new_x = combo_right - container.width()
                container.move(new_x, container.y())


class AttachedFileSquare(QFrame):
    """Compact square preview tile (hình vuông 3x3 ~ 58x58 px) matching modern AI chat specs."""

    removeRequested = pyqtSignal(str)

    def __init__(self, file_path: str = "", parent=None):
        super().__init__(parent)
        self.file_path = file_path
        self.setFixedSize(58, 58)
        self.setStyleSheet(
            "QFrame { "
            "background: rgba(255, 255, 255, 0.08); "
            "border: 1px solid rgba(255, 255, 255, 0.18); "
            "border-radius: 12px; "
            "} "
            "QFrame:hover { "
            "background: rgba(255, 255, 255, 0.14); "
            "border-color: rgba(0, 255, 170, 0.50); "
            "}"
        )
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 4, 4, 4)
        layout.setSpacing(2)

        # Top row: Extension badge & close button
        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        top_row.setSpacing(2)

        self.ext_badge = QLabel("FILE")
        self.ext_badge.setStyleSheet(
            "font-size: 9px; font-weight: 800; color: #00FFAA; border: none; background: transparent;"
        )
        top_row.addWidget(self.ext_badge)
        top_row.addStretch()

        self.remove_btn = QPushButton()
        self.remove_btn.setIcon(create_vector_icon("close", "#FFFFFF", 9))
        self.remove_btn.setIconSize(QSize(9, 9))
        self.remove_btn.setFixedSize(16, 16)
        self.remove_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.remove_btn.setToolTip("Gỡ tệp này")
        self.remove_btn.setStyleSheet(
            "QPushButton { "
            "border: none; "
            "background: rgba(255, 255, 255, 0.20); "
            "border-radius: 8px; "
            "padding: 0px; "
            "margin: 0px; "
            "} "
            "QPushButton:hover { "
            "background: #F43F5E; "
            "}"
        )
        self.remove_btn.clicked.connect(lambda: self.removeRequested.emit(self.file_path))
        top_row.addWidget(self.remove_btn)

        layout.addLayout(top_row)

        # Center: Document vector icon
        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setStyleSheet("border: none; background: transparent;")
        layout.addWidget(self.icon_lbl, stretch=1)

        if file_path:
            self.set_file(file_path)

    def set_file(self, file_path: str):
        self.file_path = file_path
        file_name = os.path.basename(file_path)
        ext = os.path.splitext(file_path)[1].lower().replace(".", "")
        if os.path.exists(file_path):
            size_kb = os.path.getsize(file_path) / 1024
            size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
        else:
            size_str = "0 KB"

        self.setToolTip(f"{file_name}\n({size_str})")
        ext_upper = ext.upper()[:4] if ext else "FILE"
        self.ext_badge.setText(ext_upper)

        is_image = ext in ["png", "jpg", "jpeg", "webp", "bmp", "gif"]
        if is_image:
            color = "#38BDF8"  # Sky Blue for images
            self.ext_badge.setStyleSheet(
                f"font-size: 9px; font-weight: 800; color: {color}; border: none; background: transparent;"
            )
            pix = QPixmap(file_path)
            if not pix.isNull():
                thumb = pix.scaled(
                    38, 30,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self.icon_lbl.setPixmap(thumb)
            else:
                self.icon_lbl.setPixmap(create_vector_icon("image", color, 22).pixmap(22, 22))
        else:
            if ext in ["pdf"]:
                color = "#F43F5E"  # Red / Coral
            elif ext in ["doc", "docx"]:
                color = "#008EFF"  # Blue
            elif ext in ["xls", "xlsx", "csv"]:
                color = "#00FFAA"  # Emerald Green
            elif ext in ["ppt", "pptx"]:
                color = "#F59E0B"  # Amber Orange
            elif ext in ["py", "js", "ts", "json", "html", "css", "cpp", "c", "java", "sql"]:
                color = "#A855F7"  # Purple for code
            else:
                color = "#94A3B8"  # Slate

            self.ext_badge.setStyleSheet(
                f"font-size: 9px; font-weight: 800; color: {color}; border: none; background: transparent;"
            )
            self.icon_lbl.setPixmap(create_vector_icon("file", color, 22).pixmap(22, 22))


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
        self._attached_files = []
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
        # ATTACHMENT SQUARES ROW (Supports multiple 3x3 cards)
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

        # Attachment Button (Modern Plus icon)
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
        self.attach_btn.clicked.connect(self._on_attach_clicked)

        # Text Input Area
        self.text_edit = MessageTextEdit()
        self.text_edit.sendRequested.connect(self._handle_send)

        # Model selector defaults to the configured model.
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
        self._load_local_models()
        self.model_combo.currentIndexChanged.connect(self._on_model_changed)

        # Voice Microphone Button
        self.mic_btn = QPushButton()
        self.mic_btn.setIcon(create_vector_icon("mic", DesignTokens.TEXT_SECONDARY, 18))
        self.mic_btn.setFixedSize(36, 36)
        self.mic_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mic_btn.setToolTip("Bật/tắt micro")
        self.mic_btn.setStyleSheet("QPushButton { border: none; background: transparent; } QPushButton:hover { background: rgba(0, 255, 170, 0.12); border-radius: 18px; }")
        self.mic_btn.clicked.connect(lambda: self.voiceToggle.emit())

        # Send Button (Border-free with pure white origami paper airplane icon)
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
        self.send_btn.clicked.connect(self._handle_send)

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

    def _on_attach_clicked(self):
        from PyQt6.QtWidgets import QFileDialog
        self.attachmentClicked.emit()
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Chọn các tệp để đính kèm (Hình ảnh, Word, Excel, PPT, PDF, Code, Văn bản...)",
            "",
            "Tất cả tệp hỗ trợ (*.png *.jpg *.jpeg *.webp *.bmp *.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.txt *.md *.py *.json *.csv *.xml *.html *.js *.ts *.cpp *.c *.java *.rs *.sql);;"
            "Hình ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
            "Microsoft Office & PDF (*.docx *.xlsx *.pptx *.pdf *.xls *.ppt);;"
            "Mã nguồn & Văn bản (*.txt *.md *.py *.json *.csv *.sql *.xml *.html);;"
            "Tất cả tệp (*.*)"
        )
        if file_paths:
            self.add_attached_files(file_paths)

    def add_attached_files(self, file_paths: list):
        new_added = False
        for path in file_paths:
            if not os.path.exists(path) or path in self._attached_files:
                continue
            self._attached_files.append(path)
            new_added = True

        if new_added:
            self._render_attached_files()

    def set_attached_file(self, file_path: str):
        """Backward compatible helper to attach a single file."""
        self.add_attached_files([file_path])

    def remove_attached_file(self, file_path: str):
        if file_path in self._attached_files:
            self._attached_files.remove(file_path)
            self._render_attached_files()

    def clear_attached_files(self):
        self._attached_files.clear()
        self._render_attached_files()

    def clear_attached_file(self):
        self.clear_attached_files()

    def _render_attached_files(self):
        # Clear existing cards from layout
        while self.attach_cards_layout.count() > 0:
            item = self.attach_cards_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        if not self._attached_files:
            self.attachment_box.hide()
            self.text_edit.setPlaceholderText("Nhập tin nhắn cho POP...")
            return

        for path in self._attached_files:
            card = AttachedFileSquare(path)
            card.removeRequested.connect(self.remove_attached_file)
            self.attach_cards_layout.addWidget(card)

        self.attach_cards_layout.addStretch()
        self.attachment_box.show()

        count = len(self._attached_files)
        if count == 1:
            fname = os.path.basename(self._attached_files[0])
            self.text_edit.setPlaceholderText(f"Nhập câu hỏi về {fname} hoặc bấm Enter / Gửi để phân tích...")
        else:
            self.text_edit.setPlaceholderText(f"Nhập câu hỏi về {count} tệp đính kèm hoặc bấm Enter / Gửi...")

    def _handle_send(self):
        user_text = self.text_edit.toPlainText().strip()
        attached_files = list(self._attached_files)

        if not user_text and not attached_files:
            return

        final_message = user_text
        if attached_files:
            from utils.document_reader import read_document_file

            file_sections = []
            file_names = []
            for idx, path in enumerate(attached_files, 1):
                file_name = os.path.basename(path)
                file_names.append(file_name)
                success, content, err = read_document_file(path)
                if success:
                    file_sections.append(
                        f"=== [Tệp {idx}: {file_name}] ===\n{content}\n=== [Hết tệp {idx}] ==="
                    )
                else:
                    file_sections.append(
                        f"=== [Tệp {idx}: {file_name} - Lỗi đọc: {err}] ==="
                    )

            prompt_header = user_text if user_text else "Hãy đọc, phân tích và so sánh / tổng hợp nội dung các tệp tin này giúp tôi."
            files_list_str = ", ".join(file_names)
            final_message = (
                f"📎 [Đính kèm {len(attached_files)} tệp: {files_list_str}]\n\n"
                + "\n\n".join(file_sections)
                + f"\n\n{prompt_header}"
            )

            self.clear_attached_files()

        if final_message:
            self.sendMessage.emit(final_message)
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

        previous_signal_state = self.model_combo.blockSignals(True)
        self.model_combo.clear()
        models = []
        MIN_MODEL_SIZE = 10 * 1024 * 1024  # At least 10MB to avoid 0MB or empty cache files
        if os.path.exists(agent_dir):
            for item in os.listdir(agent_dir):
                if item.startswith('.'):
                    continue
                item_path = os.path.join(agent_dir, item)
                if os.path.isdir(item_path):
                    # Check if directory contains at least one valid .gguf model file > 10MB
                    has_valid_gguf = False
                    for root, _, files in os.walk(item_path):
                        for f in files:
                            if f.endswith(".gguf"):
                                fp = os.path.join(root, f)
                                try:
                                    if os.path.getsize(fp) >= MIN_MODEL_SIZE:
                                        has_valid_gguf = True
                                        break
                                except OSError:
                                    pass
                        if has_valid_gguf:
                            break
                    if has_valid_gguf:
                        models.append(self._format_model_name(item))
                elif item.endswith(".gguf"):
                    try:
                        if os.path.getsize(item_path) >= MIN_MODEL_SIZE:
                            models.append(self._format_model_name(item))
                    except OSError:
                        pass

        self.model_combo.addItem("Auto")
        self.model_combo.setItemData(0, "Tự động chọn mô hình phù hợp", Qt.ItemDataRole.ToolTipRole)
        for i, m in enumerate(models, 1):
            self.model_combo.addItem(m)
            self.model_combo.setItemData(i, m, Qt.ItemDataRole.ToolTipRole)

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

    def _on_model_changed(self, index):
        text = self.model_combo.currentText()
        if not text:
            return
        if self.model_combo.itemData(index, Qt.ItemDataRole.UserRole) == "__model_hub__":
            self.model_combo.blockSignals(True)
            self.model_combo.setCurrentIndex(self._selected_model_index)
            self.model_combo.blockSignals(False)
            self._open_model_hub()
            return

        self._selected_model_index = index
        self.switchModel.emit("" if text == "Auto" else text)

    def _open_model_hub(self):
        win = self.window()
        if win and hasattr(win, "_open_settings_page"):
            getattr(win, "_open_settings_page")(2)
            return

        from view.ui.settings import SettingsDialog
        dialog = SettingsDialog(username="Tài khoản", initial_tab=2, parent=self)
        dialog.modelDownloaded.connect(self._load_local_models)
        dialog.exec()

    def set_listening(self, is_listening: bool):
        pass
