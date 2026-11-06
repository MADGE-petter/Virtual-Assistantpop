"""Editor Tab Widget - Manages multiple open code tabs with
dirty indicators, tab closing, file reading, and saving.
"""
import os
from typing import Dict, Optional
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel, QMessageBox
)
from PyQt6.QtGui import QKeySequence, QShortcut

from view.ui.editor.code_editor_widget import CodeEditorWidget


class EditorTabWidget(QWidget):
    """Multi-tab code editor manager."""

    activeFileChanged = pyqtSignal(str)
    fileSaved = pyqtSignal(str)
    statusMessage = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._editors: Dict[str, CodeEditorWidget] = {}  # full_path -> CodeEditorWidget

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Tab Widget
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabsClosable(True)
        self.tab_widget.setMovable(True)
        self.tab_widget.setDocumentMode(True)
        self.tab_widget.tabCloseRequested.connect(self.close_tab)
        self.tab_widget.currentChanged.connect(self._on_tab_changed)

        # PopView Transparent Glass styling for tabs
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: rgba(255, 255, 255, 0.03);
                color: #8E9BAE;
                padding: 7px 16px;
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-bottom: none;
                border-top-left-radius: 6px;
                border-top-right-radius: 6px;
                margin-right: 2px;
                font-size: 12px;
                min-width: 80px;
            }
            QTabBar::tab:selected {
                background: rgba(0, 255, 170, 0.08);
                color: #00FFAA;
                border: 1px solid rgba(0, 255, 170, 0.35);
                border-bottom: 2px solid #00FFAA;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background: rgba(255, 255, 255, 0.06);
                color: #F8FAFC;
            }
            QTabBar::close-button {
                image: none;
                subcontrol-position: right;
                margin-left: 6px;
            }
        """)

        # Empty State Placeholder (Clean minimalist 2D, NO emoji)
        self.empty_placeholder = QWidget()
        self.empty_placeholder.setStyleSheet("background: transparent;")
        empty_layout = QVBoxLayout(self.empty_placeholder)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(10)

        from view.ui.icons import create_vector_icon
        logo_lbl = QLabel()
        logo_lbl.setPixmap(create_vector_icon("code", "#475569", 36).pixmap(36, 36))
        logo_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_lbl = QLabel("POP Code Studio")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 700; color: #E2E8F0; letter-spacing: 0.5px;")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        hint_lbl = QLabel("Chọn file từ cây thư mục bên trái để bắt đầu lập trình\nHoặc nhấn [Mở Thư Mục] trên thanh công cụ.")
        hint_lbl.setStyleSheet("font-size: 12px; color: #64748B; line-height: 1.6;")
        hint_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_layout.addWidget(logo_lbl)
        empty_layout.addWidget(title_lbl)
        empty_layout.addWidget(hint_lbl)

        layout.addWidget(self.tab_widget)
        layout.addWidget(self.empty_placeholder)

        self._update_visibility()

        # Save shortcut (Ctrl+S)
        self.save_shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        self.save_shortcut.activated.connect(self.save_current_file)

        # Close tab shortcut (Ctrl+W)
        self.close_shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        self.close_shortcut.activated.connect(self._close_current_tab)

    def _update_visibility(self):
        has_tabs = self.tab_widget.count() > 0
        self.tab_widget.setVisible(has_tabs)
        self.empty_placeholder.setVisible(not has_tabs)

    def open_file(self, file_path: str) -> Optional[CodeEditorWidget]:
        """Open a file into a tab or activate it if already open."""
        norm_path = os.path.abspath(file_path)

        # Check if already open
        if norm_path in self._editors:
            idx = self._find_tab_index(norm_path)
            if idx >= 0:
                self.tab_widget.setCurrentIndex(idx)
                return self._editors[norm_path]

        # Read file content safely
        try:
            with open(norm_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(norm_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                QMessageBox.warning(self, "Lỗi mở file", f"Không thể đọc file: {e}")
                return None
        except Exception as e:
            QMessageBox.warning(self, "Lỗi mở file", f"Không thể mở file: {e}")
            return None

        editor = CodeEditorWidget(self, file_path=norm_path)
        editor.setPlainText(content)
        editor.mark_saved()

        # Bind modification signal to update tab title with dot •
        editor.modificationChanged.connect(lambda modified, p=norm_path: self._on_modification_changed(p, modified))

        file_name = os.path.basename(norm_path)
        tab_idx = self.tab_widget.addTab(editor, file_name)
        self.tab_widget.setTabToolTip(tab_idx, norm_path)
        self.tab_widget.setCurrentIndex(tab_idx)

        self._editors[norm_path] = editor
        self._update_visibility()
        self.activeFileChanged.emit(norm_path)
        self.statusMessage.emit(f"Đã mở {file_name}")
        return editor

    def get_current_editor(self) -> Optional[CodeEditorWidget]:
        return self.tab_widget.currentWidget()

    def get_current_file_path(self) -> str:
        editor = self.get_current_editor()
        return editor.file_path if editor else ""

    def save_current_file(self) -> bool:
        editor = self.get_current_editor()
        if not editor:
            return False
        return self.save_file(editor.file_path)

    def save_file(self, file_path: str) -> bool:
        norm_path = os.path.abspath(file_path)
        if norm_path not in self._editors:
            return False

        editor = self._editors[norm_path]
        try:
            with open(norm_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            editor.mark_saved()
            self._on_modification_changed(norm_path, False)
            self.fileSaved.emit(norm_path)
            self.statusMessage.emit(f"✓ Đã lưu {os.path.basename(norm_path)}")
            return True
        except Exception as e:
            QMessageBox.critical(self, "Lỗi lưu file", f"Không thể lưu file: {e}")
            return False

    def close_tab(self, index: int):
        editor: CodeEditorWidget = self.tab_widget.widget(index)
        if not editor:
            return

        if editor.is_dirty():
            res = QMessageBox.question(
                self, "Lưu thay đổi?",
                f"File '{os.path.basename(editor.file_path)}' có thay đổi chưa lưu. Bạn có muốn lưu trước khi đóng không?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            if res == QMessageBox.StandardButton.Save:
                if not self.save_file(editor.file_path):
                    return
            elif res == QMessageBox.StandardButton.Cancel:
                return

        path = editor.file_path
        self.tab_widget.removeTab(index)
        if path in self._editors:
            del self._editors[path]

        self._update_visibility()
        current = self.get_current_file_path()
        self.activeFileChanged.emit(current)

    def _close_current_tab(self):
        idx = self.tab_widget.currentIndex()
        if idx >= 0:
            self.close_tab(idx)

    def _on_modification_changed(self, file_path: str, is_modified: bool):
        idx = self._find_tab_index(file_path)
        if idx >= 0:
            name = os.path.basename(file_path)
            title = f"{name} •" if is_modified else name
            self.tab_widget.setTabText(idx, title)

    def _find_tab_index(self, file_path: str) -> int:
        norm = os.path.abspath(file_path)
        for i in range(self.tab_widget.count()):
            w: CodeEditorWidget = self.tab_widget.widget(i)
            if w and os.path.abspath(w.file_path) == norm:
                return i
        return -1

    def _on_tab_changed(self, index: int):
        if index >= 0:
            w: CodeEditorWidget = self.tab_widget.widget(index)
            if w:
                self.activeFileChanged.emit(w.file_path)
        else:
            self.activeFileChanged.emit("")
