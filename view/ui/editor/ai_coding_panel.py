"""AI Coding Assistant Panel - Sleek conversational coding assistant
styled identically to POP Assistant's main chat interface with glowing
capsule input bar, chat bubbles, quick suggestion chips, and 1-click code application.
"""
import os
import re
import html
from typing import Optional
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QObject, QTimer
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QFrame, QScrollArea, QApplication,
    QProgressBar, QMessageBox, QSizePolicy, QGridLayout
)
from PyQt6.QtGui import QFont, QColor, QKeyEvent

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_pixmap, create_vector_icon
from service.llm_service import LLMService


class AICodingWorker(QObject):
    """Background worker thread to run LLM inference without blocking UI."""
    responseReady = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, prompt: str, system_prompt: str):
        super().__init__()
        self.prompt = prompt
        self.system_prompt = system_prompt

    def run(self):
        try:
            llm = LLMService()
            messages = [{"role": "user", "content": self.prompt}]
            reply = llm.chat(
                messages=messages,
                system_prompt=self.system_prompt,
                max_tokens=1500,
                temperature=0.3
            )
            self.responseReady.emit(reply)
        except Exception as e:
            self.errorOccurred.emit(str(e))
        finally:
            self.finished.emit()


class AgentInputEdit(QTextEdit):
    """Auto-adjusting text edit that sends message on Enter (Shift+Enter for newline)."""
    returnPressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("""
            QTextEdit {
                background: transparent;
                color: #FFFFFF;
                border: none;
                font-size: 13px;
                padding: 4px 6px;
            }
        """)

    def keyPressEvent(self, e: Optional[QKeyEvent]):
        if e and e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and not (e.modifiers() & Qt.KeyboardModifier.ShiftModifier):
            self.returnPressed.emit()
            e.accept()
        elif e is not None:
            super().keyPressEvent(e)


class AICodingPanel(QWidget):
    """Conversational AI Coding Panel styled like POP Assistant's main chat."""

    applyToEditor = pyqtSignal(str)
    insertAtCursor = pyqtSignal(str)
    statusMessage = pyqtSignal(str)

    SYSTEM_PROMPT = (
        "Bạn là POP AI Coding Assistant - chuyên gia lập trình cao cấp được tích hợp trong POP Assistant IDE. "
        "Nhiệm vụ của bạn là hỗ trợ lập trình viên viết code sạch, tối ưu, bảo mật, và giải thích chi tiết. "
        "Khi đưa ra code sửa đổi hoặc đoạn code hoàn chỉnh, hãy luôn đặt trong khối markdown ```ngôn_ngữ ... ``` rõ ràng. "
        "Trả lời ngắn gọn, súc tích và giải thích cụ thể bằng tiếng Việt."
    )

    def __init__(self, parent=None):
        super().__init__(parent)
        self.active_file_path: str = ""
        self.active_code_snippet: str = ""
        self.active_selection: str = ""
        self._thread: Optional[QThread] = None
        self._worker: Optional[AICodingWorker] = None
        self._last_ai_code: str = ""

        self._setup_ui()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 8, 10, 8)
        main_layout.setSpacing(8)

        # ----------------------------------------------------
        # 1. HEADER (Title & Context Chip)
        # ----------------------------------------------------
        header_row = QHBoxLayout()
        header_row.setContentsMargins(4, 2, 4, 2)
        header_row.setSpacing(8)

        title_lbl = QLabel("POP Coding Agent")
        title_lbl.setStyleSheet(f"font-size: 13px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT}; letter-spacing: 0.5px;")

        self.context_chip = QLabel("Chưa mở file")
        self.context_chip.setStyleSheet(
            f"font-size: 11px; color: {DesignTokens.TEXT_SECONDARY}; "
            f"background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.06); "
            f"border-radius: 12px; padding: 2px 10px;"
        )
        self.context_chip.setMaximumWidth(180)

        header_row.addWidget(title_lbl)
        header_row.addStretch()
        header_row.addWidget(self.context_chip)
        main_layout.addLayout(header_row)

        # ----------------------------------------------------
        # 2. SUGGESTION PILLS (Chips matching chat UI)
        # ----------------------------------------------------
        pills_layout = QGridLayout()
        pills_layout.setContentsMargins(0, 0, 0, 0)
        pills_layout.setHorizontalSpacing(6)
        pills_layout.setVerticalSpacing(6)

        pill_style = (
            f"QPushButton {{ background: rgba(255, 255, 255, 0.03); color: {DesignTokens.TEXT_SECONDARY}; "
            f"border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 12px; "
            f"padding: 5px 8px; font-size: 11px; font-weight: 500; text-align: center; }}"
            f"QPushButton:hover {{ background: rgba(0, 255, 170, 0.12); border-color: {DesignTokens.CYAN_ACCENT}; color: #FFFFFF; }}"
        )

        self.btn_chip_explain = QPushButton("Giải thích code")
        self.btn_chip_explain.setStyleSheet(pill_style)
        self.btn_chip_explain.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chip_explain.clicked.connect(self._on_explain_clicked)

        self.btn_chip_fix = QPushButton("Tìm & Sửa lỗi")
        self.btn_chip_fix.setStyleSheet(pill_style)
        self.btn_chip_fix.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chip_fix.clicked.connect(self._on_fix_clicked)

        self.btn_chip_refactor = QPushButton("Tối ưu hoá")
        self.btn_chip_refactor.setStyleSheet(pill_style)
        self.btn_chip_refactor.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chip_refactor.clicked.connect(self._on_refactor_clicked)

        self.btn_chip_test = QPushButton("Unit Test")
        self.btn_chip_test.setStyleSheet(pill_style)
        self.btn_chip_test.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_chip_test.clicked.connect(self._on_test_clicked)

        pills_layout.addWidget(self.btn_chip_explain, 0, 0)
        pills_layout.addWidget(self.btn_chip_fix, 0, 1)
        pills_layout.addWidget(self.btn_chip_refactor, 1, 0)
        pills_layout.addWidget(self.btn_chip_test, 1, 1)
        main_layout.addLayout(pills_layout)

        # Subtle progress indicator
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(2)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar { background: transparent; border: none; }
            QProgressBar::chunk { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #008EFF, stop:1 #00FFAA); }
        """)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # ----------------------------------------------------
        # 3. CHAT STREAM / MESSAGE SCROLL AREA
        # ----------------------------------------------------
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.chat_container = QWidget()
        self.chat_container.setStyleSheet("background: transparent;")
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setContentsMargins(2, 4, 2, 4)
        self.chat_layout.setSpacing(10)
        self.chat_layout.addStretch(1)

        self.scroll_area.setWidget(self.chat_container)
        main_layout.addWidget(self.scroll_area, stretch=1)

        # Initial greeting from POP Agent
        self._add_bot_bubble(
            "Xin chào! Tôi là trợ lý code của bạn. Bạn có thể chọn đoạn code cần giải thích, "
            "nhấn các gợi ý nhanh phía trên, hoặc gửi yêu cầu cụ thể ngay tại khung bên dưới."
        )

        # ----------------------------------------------------
        # 4. GLOWING CAPSULE INPUT BAR (Style identical to main chat)
        # ----------------------------------------------------
        input_wrapper = QVBoxLayout()
        input_wrapper.setContentsMargins(0, 4, 0, 0)
        input_wrapper.setSpacing(3)

        self.input_frame = QFrame()
        self.input_frame.setObjectName("agentInputFrame")
        self.input_frame.setStyleSheet(f"""
            QFrame#agentInputFrame {{
                background: rgba(12, 19, 34, 0.85);
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 20px;
            }}
            QFrame#agentInputFrame:hover {{
                border-color: {DesignTokens.BORDER_GRADIENT_HOVER};
                background: rgba(14, 22, 38, 0.95);
            }}
        """)
        frame_layout = QHBoxLayout(self.input_frame)
        frame_layout.setContentsMargins(10, 4, 6, 4)
        frame_layout.setSpacing(6)

        # Attachment / Context Button (+)
        self.btn_attach = QPushButton()
        self.btn_attach.setIcon(create_vector_icon("plus", DesignTokens.TEXT_MUTED, 14))
        self.btn_attach.setFixedSize(26, 26)
        self.btn_attach.setToolTip("Đính kèm ngữ cảnh file/code hiện tại")
        self.btn_attach.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_attach.setStyleSheet("""
            QPushButton { border: none; background: transparent; border-radius: 13px; }
            QPushButton:hover { background: rgba(255, 255, 255, 0.08); }
        """)
        self.btn_attach.clicked.connect(self._on_attach_clicked)
        frame_layout.addWidget(self.btn_attach)

        # Multiline Input Edit
        self.input_edit = AgentInputEdit()
        self.input_edit.setPlaceholderText("Nhập tin nhắn cho POP AI...")
        self.input_edit.returnPressed.connect(self._on_send_clicked)
        frame_layout.addWidget(self.input_edit, stretch=1)

        # Send Button (Glowing circular pill with paper airplane)
        self.send_btn = QPushButton()
        self.send_btn.setIcon(create_vector_icon("send", "#FFFFFF", 13))
        self.send_btn.setFixedSize(28, 28)
        self.send_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                border: none;
                border-radius: 14px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #00B4FF, stop:1 #33FFBE);
            }}
            QPushButton:disabled {{
                background: rgba(255, 255, 255, 0.08);
            }}
        """)
        self.send_btn.clicked.connect(self._on_send_clicked)
        frame_layout.addWidget(self.send_btn)

        input_wrapper.addWidget(self.input_frame)

        # Subtitle hint
        hint_lbl = QLabel("Enter để gửi • Shift + Enter để xuống dòng")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint_lbl.setStyleSheet("color: #64748B; font-size: 10px;")
        input_wrapper.addWidget(hint_lbl)

        main_layout.addLayout(input_wrapper)

    # ----------------------------------------------------
    # BUBBLE RENDERING (Matches Main Chat View)
    # ----------------------------------------------------
    def _add_user_bubble(self, text: str):
        row = QHBoxLayout()
        row.setContentsMargins(10, 2, 0, 2)
        row.addStretch(1)

        card = QFrame()
        card.setMaximumWidth(320)
        card.setStyleSheet(f"""
            QFrame {{
                background-color: rgba(14, 22, 38, 0.95);
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 14px;
                border-top-right-radius: 3px;
                padding: 8px 12px;
            }}
            QLabel {{ color: #FFFFFF; font-size: 12px; line-height: 1.4; }}
        """)
        cl = QVBoxLayout(card)
        cl.setContentsMargins(0, 0, 0, 0)
        lbl = QLabel(text)
        lbl.setWordWrap(True)
        cl.addWidget(lbl)

        row.addWidget(card)
        # Insert before stretch
        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)
        self._scroll_to_bottom()

    def _add_bot_bubble(self, reply_text: str):
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame#botCard {{
                background-color: rgba(10, 16, 28, 0.88);
                border: 1px solid;
                border-color: {DesignTokens.BORDER_GRADIENT};
                border-radius: 14px;
                border-top-left-radius: 3px;
                padding: 10px 12px;
            }}
        """)
        card.setObjectName("botCard")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(4, 4, 4, 4)
        cl.setSpacing(6)

        # Header Row (Avatar + Label)
        h_row = QHBoxLayout()
        h_row.setSpacing(6)
        avatar = QLabel()
        avatar.setPixmap(get_pop_logo_pixmap(20))
        avatar.setFixedSize(20, 20)
        lbl_name = QLabel("POP Agent")
        lbl_name.setStyleSheet(f"font-size: 11px; font-weight: 700; color: {DesignTokens.CYAN_ACCENT};")
        h_row.addWidget(avatar)
        h_row.addWidget(lbl_name)
        h_row.addStretch()
        cl.addLayout(h_row)

        # Message Text
        msg_lbl = QLabel()
        msg_lbl.setWordWrap(True)
        msg_lbl.setStyleSheet("color: #E2E8F0; font-size: 12px; line-height: 1.45;")
        formatted_html = self._format_markdown_html(reply_text)
        msg_lbl.setText(formatted_html)
        msg_lbl.setTextFormat(Qt.TextFormat.RichText)
        msg_lbl.setOpenExternalLinks(True)
        cl.addWidget(msg_lbl)

        # If Code Block Exists -> Add Action Bar for Code
        code_block = self._extract_code_block(reply_text)
        if code_block:
            self._last_ai_code = code_block
            act_bar = QHBoxLayout()
            act_bar.setContentsMargins(0, 4, 0, 0)
            act_bar.setSpacing(6)

            btn_apply = QPushButton("Áp dụng vào Editor")
            btn_apply.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_apply.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 255, 170, 0.12);
                    color: #00FFAA;
                    font-weight: 700;
                    font-size: 11px;
                    border: 1px solid rgba(0, 255, 170, 0.35);
                    border-radius: 6px;
                    padding: 4px 10px;
                }
                QPushButton:hover {
                    background: rgba(0, 255, 170, 0.22);
                    color: #FFFFFF;
                    border-color: #00FFAA;
                }
            """)
            btn_apply.clicked.connect(lambda _, c=code_block: self._emit_apply(c))

            btn_copy = QPushButton("Sao chép")
            btn_copy.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_copy.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    color: #94A3B8;
                    font-size: 11px;
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 6px;
                    padding: 4px 8px;
                }
                QPushButton:hover { background: rgba(255, 255, 255, 0.08); color: #FFFFFF; }
            """)
            btn_copy.clicked.connect(lambda _, c=code_block: self._copy_code(c))

            act_bar.addWidget(btn_apply)
            act_bar.addWidget(btn_copy)
            act_bar.addStretch()
            cl.addLayout(act_bar)

        row = QHBoxLayout()
        row.setContentsMargins(0, 2, 10, 2)
        row.addWidget(card)
        row.addStretch(1)

        self.chat_layout.insertLayout(self.chat_layout.count() - 1, row)
        self._scroll_to_bottom()

    def _scroll_to_bottom(self):
        def _do_scroll():
            vsb = self.scroll_area.verticalScrollBar()
            if vsb is not None:
                vsb.setValue(vsb.maximum())
        QTimer.singleShot(50, _do_scroll)

    def _emit_apply(self, code: str):
        self.applyToEditor.emit(code)
        self.statusMessage.emit("Đã áp dụng code của AI vào Editor")

    def _copy_code(self, code: str):
        cb = QApplication.clipboard()
        if cb is not None:
            cb.setText(code)
        self.statusMessage.emit("Đã sao chép vào Clipboard")

    # ----------------------------------------------------
    # CONTEXT & INFERENCE
    # ----------------------------------------------------
    def set_context(self, file_path: str, code: str, selection: str = ""):
        self.active_file_path = file_path
        self.active_code_snippet = code
        self.active_selection = selection

        if file_path:
            name = os.path.basename(file_path)
            lines = len(code.splitlines())
            if selection:
                sel_lines = len(selection.splitlines())
                self.context_chip.setText(f"{name} • {sel_lines}d chọn")
                self.context_chip.setToolTip(f"File: {name} ({lines} dòng) | Đang chọn {sel_lines} dòng")
            else:
                self.context_chip.setText(f"{name} • {lines}d")
                self.context_chip.setToolTip(f"File: {name} ({lines} dòng)")
        else:
            self.context_chip.setText("Chưa mở file")
            self.context_chip.setToolTip("")

    def _get_target_code(self) -> str:
        return self.active_selection.strip() if self.active_selection.strip() else self.active_code_snippet

    def _execute_query(self, user_display_text: str, full_prompt: str):
        if self._thread and self._thread.isRunning():
            QMessageBox.information(self, "AI đang bận", "AI đang xử lý yêu cầu trước đó, vui lòng đợi giây lát.")
            return

        self._add_user_bubble(user_display_text)
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(True)
        self.send_btn.setEnabled(False)

        self._thread = QThread()
        self._worker = AICodingWorker(full_prompt, self.SYSTEM_PROMPT)
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(self._worker.run)
        self._worker.responseReady.connect(self._on_response_ready)
        self._worker.errorOccurred.connect(self._on_error_occurred)
        self._worker.finished.connect(self._on_worker_finished)

        self._thread.start()

    def _on_response_ready(self, reply: str):
        self._add_bot_bubble(reply)
        self.statusMessage.emit("AI đã trả lời xong.")

    def _on_error_occurred(self, err: str):
        self._add_bot_bubble(f"<b>Lỗi xử lý:</b> {err}\n\nHãy kiểm tra cài đặt Model trong mục Cài đặt.")

    def _on_worker_finished(self):
        self.progress_bar.setVisible(False)
        self.send_btn.setEnabled(True)
        if self._thread:
            self._thread.quit()
            self._thread.wait()
            self._thread = None
            self._worker = None

    # ----------------------------------------------------
    # QUICK ACTION CLICKS
    # ----------------------------------------------------
    def _on_explain_clicked(self):
        target = self._get_target_code()
        if not target:
            QMessageBox.warning(self, "Chưa có code", "Vui lòng mở file hoặc chọn đoạn code cần giải thích.")
            return
        prompt = f"Hãy giải thích chi tiết cấu trúc, luồng hoạt động và mục đích của đoạn code sau đây trong file {os.path.basename(self.active_file_path)}:\n\n```\n{target}\n```"
        self._execute_query("Giải thích đoạn code hiện tại", prompt)

    def _on_fix_clicked(self):
        target = self._get_target_code()
        if not target:
            QMessageBox.warning(self, "Chưa có code", "Vui lòng mở file hoặc chọn đoạn code cần tìm lỗi.")
            return
        prompt = f"Hãy rà soát kỹ lưỡng đoạn code sau để tìm các lỗi tiềm ẩn (syntax error, logic bug, security issue, memory leak). Chỉ ra từng lỗi và cung cấp bản code sửa hoàn chỉnh chuẩn xác trong khối ```code```:\n\n```\n{target}\n```"
        self._execute_query("Tìm lỗi & sửa bug cho code này", prompt)

    def _on_refactor_clicked(self):
        target = self._get_target_code()
        if not target:
            QMessageBox.warning(self, "Chưa có code", "Vui lòng mở file hoặc chọn đoạn code cần tối ưu.")
            return
        prompt = f"Hãy tái cấu trúc (refactor) đoạn code sau để tăng hiệu năng, dễ đọc, tuân thủ Clean Code và Best Practices. Cung cấp code đã refactor trong khối ```code``` và giải thích các điểm cải tiến:\n\n```\n{target}\n```"
        self._execute_query("Tối ưu hoá (Refactor) code này", prompt)

    def _on_test_clicked(self):
        target = self._get_target_code()
        if not target:
            QMessageBox.warning(self, "Chưa có code", "Vui lòng mở file hoặc chọn đoạn code cần tạo unit test.")
            return
        prompt = f"Hãy viết bộ Unit Tests hoàn chỉnh (dùng pytest/unittest nếu là Python hoặc test runner phù hợp với ngôn ngữ) cho đoạn code sau, bao gồm cả edge cases:\n\n```\n{target}\n```"
        self._execute_query("Tạo bộ Unit Test cho code này", prompt)

    def _on_attach_clicked(self):
        target = self._get_target_code()
        if target:
            name = os.path.basename(self.active_file_path) or "snippet"
            cur = self.input_edit.toPlainText()
            self.input_edit.setPlainText(f"{cur}\n[Đính kèm: {name}]\n")
            self.statusMessage.emit(f"Đã đính kèm ngữ cảnh {name}")
        else:
            self.statusMessage.emit("Chưa có file/code nào để đính kèm")

    def _on_send_clicked(self):
        text = self.input_edit.toPlainText().strip()
        if not text:
            return
        self.input_edit.clear()

        target = self._get_target_code()
        prompt = text
        if target:
            prompt += f"\n\nNgữ cảnh code ({os.path.basename(self.active_file_path)}):\n```\n{target}\n```"

        self._execute_query(text, prompt)

    # ----------------------------------------------------
    # FORMATTING UTILS
    # ----------------------------------------------------
    def _format_markdown_html(self, text: str) -> str:
        escaped = html.escape(text)

        pattern = r"```([a-zA-Z0-9_-]*)\r?\n(.*?)```"
        def replace_code(m):
            lang = m.group(1) or "CODE"
            code_content = m.group(2)
            return (
                f"<div style='background: #03060C; border: 1px solid rgba(255,255,255,0.08); border-radius: 6px; margin: 6px 0; padding: 8px;'>"
                f"<div style='color: #00FFAA; font-size: 10px; font-weight: bold; margin-bottom: 4px;'>{lang.upper()}</div>"
                f"<pre style='color: #38BDF8; font-family: Consolas, monospace; font-size: 11px; margin: 0; white-space: pre-wrap;'>{code_content}</pre>"
                f"</div>"
            )

        formatted = re.sub(pattern, replace_code, escaped, flags=re.DOTALL)
        formatted = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", formatted)
        formatted = re.sub(r"### (.*?)\n", r"<h4 style='color: #00CCFF; margin: 6px 0 2px 0;'>\1</h4>", formatted)
        formatted = re.sub(r"## (.*?)\n", r"<h3 style='color: #00FFAA; margin: 8px 0 2px 0;'>\1</h3>", formatted)
        formatted = formatted.replace("\n", "<br>")
        return formatted

    def _extract_code_block(self, text: str) -> str:
        matches = re.findall(r"```(?:[a-zA-Z0-9_-]*)\r?\n(.*?)```", text, re.DOTALL)
        if matches:
            longest_code = max(matches, key=lambda s: len(s))
            return str(longest_code).strip()
        return ""
