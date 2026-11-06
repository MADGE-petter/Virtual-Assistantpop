"""Embedded Terminal Widget - Integrated PowerShell / CMD console
with asynchronous QProcess execution, command history, and one-click script runner.
"""
import os
import sys
from PyQt6.QtCore import Qt, QProcess, pyqtSignal
from PyQt6.QtGui import QFont, QTextCursor, QColor
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPlainTextEdit, QLineEdit,
    QPushButton, QLabel
)


class EmbeddedTerminalWidget(QWidget):
    """Integrated command-line terminal running powershell or cmd asynchronously."""

    closeRequested = pyqtSignal()

    def __init__(self, parent=None, working_dir: str = ""):
        super().__init__(parent)
        self.working_dir = working_dir or os.getcwd()
        self.history = []
        self.history_index = -1

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 8)
        layout.setSpacing(6)

        # Header Bar (clean 2D, NO emoji)
        header = QHBoxLayout()
        header.setContentsMargins(0, 0, 0, 0)
        header.setSpacing(6)

        title = QLabel("TERMINAL")
        title.setStyleSheet("color: #00FFAA; font-weight: 700; font-size: 11px; letter-spacing: 0.5px;")
        header.addWidget(title, stretch=1)

        self.btn_run = QPushButton("Run File")
        self.btn_run.setToolTip("Chạy file code hiện tại bằng Python")
        self.btn_run.setFixedHeight(22)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setToolTip("Xóa màn hình console")
        self.btn_clear.setFixedHeight(22)
        self.btn_clear.clicked.connect(self.clear_console)

        self.btn_kill = QPushButton("Kill")
        self.btn_kill.setToolTip("Dừng tiến trình đang chạy")
        self.btn_kill.setFixedHeight(22)
        self.btn_kill.clicked.connect(self.kill_process)

        self.btn_close = QPushButton("✕")
        self.btn_close.setToolTip("Ẩn Terminal")
        self.btn_close.setFixedSize(22, 22)
        self.btn_close.clicked.connect(self.closeRequested.emit)

        btn_style = """
            QPushButton {
                background: rgba(255, 255, 255, 0.04);
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 4px;
                color: #CBD5E1;
                font-size: 11px;
                padding: 0 8px;
            }
            QPushButton:hover {
                background: rgba(0, 255, 170, 0.15);
                border-color: #00FFAA;
                color: #00FFAA;
            }
        """
        for b in (self.btn_run, self.btn_clear, self.btn_kill, self.btn_close):
            b.setStyleSheet(btn_style)
            b.setCursor(Qt.CursorShape.PointingHandCursor)
            header.addWidget(b)

        layout.addLayout(header)

        # Output Console Text Edit
        self.console = QPlainTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumBlockCount(2500)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.console.setFont(font)
        self.console.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(4, 7, 14, 0.55);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 6px;
            }
        """)
        layout.addWidget(self.console, stretch=1)

        # Command Input Line
        input_row = QHBoxLayout()
        input_row.setContentsMargins(0, 0, 0, 0)
        input_row.setSpacing(6)

        prompt_lbl = QLabel("PS >")
        prompt_lbl.setStyleSheet("color: #00FFAA; font-weight: 700; font-family: Consolas; font-size: 11px;")
        input_row.addWidget(prompt_lbl)

        self.cmd_input = QLineEdit()
        self.cmd_input.setFont(font)
        self.cmd_input.setPlaceholderText("Nhập lệnh (ví dụ: python main.py, pip list, git status)...")
        self.cmd_input.setStyleSheet("""
            QLineEdit {
                background-color: rgba(255, 255, 255, 0.03);
                color: #FFFFFF;
                border: 1px solid rgba(255, 255, 255, 0.08);
                border-radius: 6px;
                padding: 4px 10px;
            }
            QLineEdit:focus {
                border-color: #00FFAA;
                background-color: rgba(0, 255, 170, 0.04);
            }
        """)
        self.cmd_input.returnPressed.connect(self._send_user_command)
        input_row.addWidget(self.cmd_input, stretch=1)

        layout.addLayout(input_row)

        # QProcess for Shell
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.process.readyRead.connect(self._on_ready_read)
        self.process.finished.connect(self._on_process_finished)

        self._start_shell()

    def set_working_dir(self, directory: str):
        if os.path.exists(directory):
            self.working_dir = directory
            self.kill_process()
            self._start_shell()

    def _start_shell(self):
        self.process.setWorkingDirectory(self.working_dir)
        shell = "powershell.exe" if sys.platform == "win32" else "bash"
        args = ["-NoLogo", "-NoProfile"] if sys.platform == "win32" else []
        self.process.start(shell, args)
        self.append_text(f"--- POP Terminal Started [{self.working_dir}] ---\n", "#00FFAA")

    def _on_ready_read(self):
        data = self.process.readAll().data()
        try:
            text = data.decode('utf-8')
        except UnicodeDecodeError:
            try:
                text = data.decode('cp1252', errors='replace')
            except Exception:
                text = data.decode('latin-1', errors='replace')
        self.append_text(text)

    def _on_process_finished(self, exit_code, exit_status):
        self.append_text(f"\n[Tiến trình kết thúc với mã {exit_code}]\n", "#64748B")

    def append_text(self, text: str, color: str = ""):
        cursor = self.console.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.console.setTextCursor(cursor)
        if color:
            fmt = cursor.charFormat()
            fmt.setForeground(QColor(color))
            cursor.setCharFormat(fmt)
            cursor.insertText(text)
            fmt.setForeground(QColor("#E2E8F0"))
            cursor.setCharFormat(fmt)
        else:
            self.console.insertPlainText(text)
        self.console.ensureCursorVisible()

    def _send_user_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return

        self.history.append(cmd)
        self.history_index = len(self.history)
        self.cmd_input.clear()

        self.execute_command(cmd)

    def set_working_dir(self, path: str):
        self.working_dir = path
        if os.path.exists(path):
            self.execute_command(f'cd "{path}"')

    def execute_command(self, cmd: str):
        if self.process.state() != QProcess.ProcessState.Running:
            self._start_shell()

        self.append_text(f"\n> {cmd}\n", "#00CCFF")
        self.process.write((cmd + "\n").encode('utf-8'))

    def run_file(self, file_path: str):
        if not file_path or not os.path.exists(file_path):
            self.append_text("\n[Lỗi: Không tìm thấy file để chạy]\n", "#EF4444")
            return

        ext = file_path.split('.')[-1].lower() if '.' in file_path else ""
        if ext == "py":
            cmd = f'python "{file_path}"'
        elif ext == "js":
            cmd = f'node "{file_path}"'
        elif ext == "sh":
            cmd = f'bash "{file_path}"'
        elif ext == "ps1":
            cmd = f'powershell -ExecutionPolicy Bypass -File "{file_path}"'
        else:
            cmd = f'"{file_path}"'

        self.execute_command(cmd)

    def clear_console(self):
        self.console.clear()

    def kill_process(self):
        if self.process.state() == QProcess.ProcessState.Running:
            self.process.kill()
            self.process.waitForFinished(1000)
            self.append_text("\n[Tiến trình đã bị dừng]\n", "#F59E0B")
