"""Code Editor Studio Widget & Window - Native IDE workspace for POP Assistant.
Combines File Explorer, Multi-tab Native Editor, Collapsible Terminal,
and Context-aware AI Assistant in a clean PopView glassmorphic interface.
No emojis used; only sleek 2D monochrome icons and typography.
"""
import os
from typing import Optional
from PyQt6.QtCore import Qt, QSize, pyqtSignal
from PyQt6.QtGui import QIcon, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QPushButton, QLabel, QFileDialog, QFrame, QMessageBox
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_pop_logo_icon, create_vector_icon
from view.ui.editor.project_explorer_widget import ProjectExplorerWidget
from view.ui.editor.editor_tab_widget import EditorTabWidget
from view.ui.editor.embedded_terminal_widget import EmbeddedTerminalWidget
from view.ui.editor.ai_coding_panel import AICodingPanel


class CodeEditorStudioWidget(QWidget):
    """Embedded POP Assistant Native Code Studio Widget."""

    windowHideToMascot = pyqtSignal()
    windowMinimize = pyqtSignal()
    windowMaximize = pyqtSignal()
    windowClose = pyqtSignal()

    def __init__(self, parent=None, initial_dir: str = ""):
        super().__init__(parent)
        self.workspace_dir = initial_dir or os.getcwd()

        self._setup_ui()
        self._setup_shortcuts()
        self._wire_signals()
        self._apply_theme()

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 0, 10, 8)
        main_layout.setSpacing(6)

        # ----------------------------------------------------
        # 1. TOP HEADER (Super compact 34px bar - no cluttered F5/navigation buttons)
        # ----------------------------------------------------
        toolbar = QWidget()
        toolbar.setFixedHeight(34)
        toolbar.setObjectName("editorToolbar")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(6, 2, 6, 2)
        toolbar_layout.setSpacing(8)

        # Brand Icon (2D vector icon)
        brand_icon = QLabel()
        brand_icon.setPixmap(create_vector_icon("code", "#00FFAA", 15).pixmap(15, 15))

        brand_lbl = QLabel("POP Code Studio")
        brand_lbl.setStyleSheet("font-size: 12px; font-weight: 700; color: #00FFAA; letter-spacing: 0.5px;")

        self.workspace_lbl = QLabel(f"•  {os.path.basename(self.workspace_dir)}")
        self.workspace_lbl.setStyleSheet("color: #64748B; font-size: 11px;")

        toolbar_layout.addWidget(brand_icon)
        toolbar_layout.addWidget(brand_lbl)
        toolbar_layout.addWidget(self.workspace_lbl)
        toolbar_layout.addWidget(self._create_divider())

        # Main Quick Action Buttons
        self.open_folder_btn = self._create_tool_button(
            "Mở Thư Mục", self._on_open_folder_clicked, icon_name="folder", tooltip="Mở Thư Mục Dự Án (Ctrl+O)"
        )
        self.save_btn = self._create_tool_button(
            "Lưu", self._on_save_clicked, icon_name="disk", tooltip="Lưu File Hiện Tại (Ctrl+S)"
        )
        self.run_btn = self._create_tool_button(
            "Chạy File (F5)", self._on_run_clicked, highlight=True, icon_name="play", tooltip="Chạy File Hiện Tại (F5)"
        )

        toolbar_layout.addWidget(self.open_folder_btn)
        toolbar_layout.addWidget(self.save_btn)
        toolbar_layout.addWidget(self.run_btn)

        toolbar_layout.addStretch()

        # Workspace Tool Toggles
        self.terminal_toggle_btn = self._create_tool_button(
            "Terminal", self._toggle_terminal, icon_name="command", tooltip="Bật / Tắt Terminal tích hợp"
        )
        self.ai_toggle_btn = self._create_tool_button(
            "AI Assistant", self._toggle_ai_panel, icon_name="bot", tooltip="Bật / Tắt POP AI Coding Assistant"
        )

        toolbar_layout.addWidget(self.terminal_toggle_btn)
        toolbar_layout.addWidget(self.ai_toggle_btn)
        toolbar_layout.addWidget(self._create_divider())

        # Window Controls (matching PopView top-right controls)
        win_controls = QHBoxLayout()
        win_controls.setSpacing(4)
        btn_style = (
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            "QPushButton:hover { background: rgba(255, 255, 255, 0.08); }"
        )

        self.mascot_btn = QPushButton()
        self.mascot_btn.setIcon(create_vector_icon("mini_mascot", DesignTokens.CYAN_ACCENT, 14))
        self.mascot_btn.setFixedSize(28, 28)
        self.mascot_btn.setToolTip("Ẩn xuống Mini Mascot")
        self.mascot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mascot_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            f"QPushButton:hover {{ background: rgba(0, 255, 170, 0.15); }}"
        )
        self.mascot_btn.clicked.connect(self.windowHideToMascot.emit)

        self.min_btn = QPushButton()
        self.min_btn.setIcon(create_vector_icon("minimize", DesignTokens.TEXT_SECONDARY, 12))
        self.min_btn.setFixedSize(28, 28)
        self.min_btn.setToolTip("Thu nhỏ cửa sổ")
        self.min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.min_btn.setStyleSheet(btn_style)
        self.min_btn.clicked.connect(self.windowMinimize.emit)

        self.max_btn = QPushButton()
        self.max_btn.setIcon(create_vector_icon("maximize", DesignTokens.TEXT_SECONDARY, 12))
        self.max_btn.setFixedSize(28, 28)
        self.max_btn.setToolTip("Phóng to / Khôi phục kích thước")
        self.max_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.max_btn.setStyleSheet(btn_style)
        self.max_btn.clicked.connect(self.windowMaximize.emit)

        self.close_btn = QPushButton()
        self.close_btn.setIcon(create_vector_icon("close", DesignTokens.CORAL_ACCENT, 12))
        self.close_btn.setFixedSize(28, 28)
        self.close_btn.setToolTip("Đóng ứng dụng")
        self.close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.close_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; border-radius: 6px; } "
            "QPushButton:hover { background: rgba(244, 63, 94, 0.22); }"
        )
        self.close_btn.clicked.connect(self.windowClose.emit)

        win_controls.addWidget(self.mascot_btn)
        win_controls.addWidget(self.min_btn)
        win_controls.addWidget(self.max_btn)
        win_controls.addWidget(self.close_btn)

        toolbar_layout.addLayout(win_controls)
        main_layout.addWidget(toolbar)

        # ----------------------------------------------------
        # 2. MAIN SPLITTER LAYOUT (Translucent glass panels)
        # ----------------------------------------------------
        self.main_h_splitter = QSplitter(Qt.Orientation.Horizontal)
        self.main_h_splitter.setHandleWidth(4)

        # Left Panel: Project Explorer
        self.explorer_widget = ProjectExplorerWidget(self, root_path=self.workspace_dir)
        self.main_h_splitter.addWidget(self.explorer_widget)

        # Center Vertical Splitter: Editor Tabs + Terminal
        self.center_v_splitter = QSplitter(Qt.Orientation.Vertical)
        self.center_v_splitter.setHandleWidth(4)

        self.tab_widget = EditorTabWidget(self)
        self.center_v_splitter.addWidget(self.tab_widget)

        self.terminal_widget = EmbeddedTerminalWidget(self, working_dir=self.workspace_dir)
        self.center_v_splitter.addWidget(self.terminal_widget)

        # Set center splitter ratios: 70% editor, 30% terminal
        self.center_v_splitter.setSizes([550, 220])
        self.main_h_splitter.addWidget(self.center_v_splitter)

        # Right Panel: AI Coding Assistant
        self.ai_panel = AICodingPanel(self)
        self.main_h_splitter.addWidget(self.ai_panel)

        # Set main splitter initial widths: Left 240px, Center 760px, Right 310px
        self.main_h_splitter.setSizes([240, 760, 310])

        main_layout.addWidget(self.main_h_splitter, stretch=1)

        # ----------------------------------------------------
        # 3. STATUS BAR (Transparent Container Frame)
        # ----------------------------------------------------
        status_bar = QFrame()
        status_bar.setFixedHeight(24)
        status_bar.setObjectName("editorStatusBar")
        sb_layout = QHBoxLayout(status_bar)
        sb_layout.setContentsMargins(8, 0, 8, 0)
        sb_layout.setSpacing(10)

        self.status_msg_lbl = QLabel("Sẵn sàng")
        self.status_msg_lbl.setStyleSheet("color: #94A3B8; font-size: 11px;")

        self.status_path_lbl = QLabel("")
        self.status_path_lbl.setStyleSheet("color: #64748B; font-size: 11px;")

        self.status_pos_lbl = QLabel("Dòng 1, Cột 1")
        self.status_pos_lbl.setStyleSheet("color: #00FFAA; font-size: 11px; font-weight: 600; padding: 0 12px;")

        self.status_info_lbl = QLabel("UTF-8  |  Spaces: 4")
        self.status_info_lbl.setStyleSheet("color: #64748B; font-size: 11px; padding: 0 8px;")

        sb_layout.addWidget(self.status_msg_lbl, stretch=1)
        sb_layout.addWidget(self.status_path_lbl)
        sb_layout.addWidget(self.status_pos_lbl)
        sb_layout.addWidget(self.status_info_lbl)

        main_layout.addWidget(status_bar)

    def _create_divider(self) -> QWidget:
        div = QWidget()
        div.setFixedSize(1, 18)
        div.setStyleSheet("background-color: rgba(255, 255, 255, 0.08);")
        return div

    def _create_tool_button(self, text: str, callback, highlight: bool = False, icon_name: Optional[str] = None, tooltip: str = "") -> QPushButton:
        btn = QPushButton(f" {text}" if icon_name else text)
        btn.setFixedHeight(28)
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        if tooltip:
            btn.setToolTip(tooltip)
        if icon_name:
            color = "#00FFAA" if highlight else DesignTokens.TEXT_SECONDARY
            btn.setIcon(create_vector_icon(icon_name, color, 14))
            btn.setIconSize(QSize(14, 14))
        if highlight:
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(0, 255, 170, 0.12);
                    color: #00FFAA;
                    font-weight: 700;
                    font-size: 11px;
                    border: 1px solid rgba(0, 255, 170, 0.35);
                    border-radius: 6px;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: rgba(0, 255, 170, 0.22);
                    color: #FFFFFF;
                    border-color: #00FFAA;
                }
            """)
        else:
            btn.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.04);
                    color: #CBD5E1;
                    font-size: 11px;
                    font-weight: 500;
                    border: 1px solid rgba(255, 255, 255, 0.07);
                    border-radius: 6px;
                    padding: 0 10px;
                }
                QPushButton:hover {
                    background: rgba(255, 255, 255, 0.09);
                    color: #FFFFFF;
                    border-color: rgba(0, 255, 170, 0.3);
                }
            """)
        btn.clicked.connect(callback)
        return btn

    def _setup_shortcuts(self):
        # F5 -> Run current file
        f5_shortcut = QShortcut(QKeySequence("F5"), self)
        f5_shortcut.activated.connect(self._on_run_clicked)

        # Ctrl+` -> Toggle Terminal
        term_shortcut = QShortcut(QKeySequence("Ctrl+`"), self)
        term_shortcut.activated.connect(self._toggle_terminal)

    def _wire_signals(self):
        # File Explorer -> Tab Widget
        self.explorer_widget.fileSelected.connect(self._open_file_in_editor)
        self.explorer_widget.folderOpened.connect(self._on_workspace_folder_changed)

        # Tab Widget -> Window
        self.tab_widget.activeFileChanged.connect(self._on_active_file_changed)
        self.tab_widget.statusMessage.connect(self._set_status_message)

        # Terminal button in terminal widget
        self.terminal_widget.btn_run.clicked.connect(self._on_run_clicked)
        self.terminal_widget.closeRequested.connect(lambda: self.terminal_widget.setVisible(False))

        # AI Panel -> Editor modification
        self.ai_panel.applyToEditor.connect(self._apply_ai_code)
        self.ai_panel.insertAtCursor.connect(self._insert_ai_code)
        self.ai_panel.statusMessage.connect(self._set_status_message)

    # ----------------------------------------------------
    # Workspace & File Actions
    # ----------------------------------------------------
    def _open_file_in_editor(self, file_path: str):
        editor = self.tab_widget.open_file(file_path)
        if editor:
            try:
                editor.cursorPositionChanged.disconnect(self._update_cursor_pos)
            except Exception:
                pass
            editor.cursorPositionChanged.connect(self._update_cursor_pos)
            self._update_cursor_pos()
            self._update_ai_context()

    def _on_workspace_folder_changed(self, new_dir: str):
        self.workspace_dir = new_dir
        self.workspace_lbl.setText(f"•  {os.path.basename(new_dir)}")
        self.terminal_widget.set_working_dir(new_dir)
        self._set_status_message(f"Đã chuyển thư mục làm việc sang {new_dir}")

    def _on_open_folder_clicked(self):
        folder = QFileDialog.getExistingDirectory(self, "Chọn thư mục dự án", self.workspace_dir)
        if folder:
            self.explorer_widget.set_workspace(folder)

    def _on_save_clicked(self):
        self.tab_widget.save_current_file()

    def _on_run_clicked(self):
        curr_file = self.tab_widget.get_current_file_path()
        if not curr_file:
            QMessageBox.information(self, "Chưa chọn file", "Vui lòng mở file code bạn muốn chạy.")
            return

        # Auto-save before running
        editor = self.tab_widget.get_current_editor()
        if editor and editor.is_dirty():
            self.tab_widget.save_current_file()

        # Ensure terminal is visible
        if not self.terminal_widget.isVisible():
            self.terminal_widget.setVisible(True)

        self.terminal_widget.run_file(curr_file)
        self._set_status_message(f"Đang chạy {os.path.basename(curr_file)}...")

    def _toggle_terminal(self):
        is_vis = self.terminal_widget.isVisible()
        self.terminal_widget.setVisible(not is_vis)

    def _toggle_ai_panel(self):
        is_vis = self.ai_panel.isVisible()
        self.ai_panel.setVisible(not is_vis)

    # ----------------------------------------------------
    # Active Editor & AI Synchronization
    # ----------------------------------------------------
    def _on_active_file_changed(self, file_path: str):
        if file_path:
            self.status_path_lbl.setText(file_path)
            self._update_cursor_pos()
            self._update_ai_context()
        else:
            self.status_path_lbl.setText("")
            self.status_pos_lbl.setText("Dòng 1, Cột 1")
            self.ai_panel.set_context("", "")

    def _update_cursor_pos(self):
        editor = self.tab_widget.get_current_editor()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.status_pos_lbl.setText(f"Dòng {line}, Cột {col}")
            self._update_ai_context()

    def _update_ai_context(self):
        editor = self.tab_widget.get_current_editor()
        if editor:
            code = editor.toPlainText()
            selection = editor.get_selected_text()
            self.ai_panel.set_context(editor.file_path, code, selection)

    def _apply_ai_code(self, code: str):
        editor = self.tab_widget.get_current_editor()
        if editor:
            if editor.textCursor().hasSelection():
                editor.replace_selection(code)
            else:
                editor.setPlainText(code)

    def _insert_ai_code(self, code: str):
        editor = self.tab_widget.get_current_editor()
        if editor:
            editor.insert_code_at_cursor(code)

    def _set_status_message(self, msg: str):
        self.status_msg_lbl.setText(msg)

    # ----------------------------------------------------
    # PopView Transparent Glass Theme
    # ----------------------------------------------------
    def _apply_theme(self):
        self.setStyleSheet("""
            QWidget {
                background-color: transparent;
            }
            #editorToolbar {
                background-color: transparent;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
            #editorStatusBar {
                background-color: transparent;
                border-top: 1px solid rgba(255, 255, 255, 0.06);
            }
            QSplitter::handle {
                background-color: rgba(255, 255, 255, 0.04);
            }
            QSplitter::handle:hover {
                background-color: rgba(0, 255, 170, 0.6);
            }
            QScrollBar:vertical {
                background: transparent;
                width: 8px;
                border: none;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 0.12);
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: rgba(0, 255, 170, 0.4);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background: transparent;
                height: 8px;
                border: none;
            }
            QScrollBar::handle:horizontal {
                background: rgba(255, 255, 255, 0.12);
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: rgba(0, 255, 170, 0.4);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
            }
        """)


class CodeEditorWindow(QMainWindow):
    """POP Assistant Native Code Studio (Standalone Window mode)."""

    def __init__(self, parent=None, initial_dir: str = ""):
        super().__init__(parent)
        self.setWindowTitle("POP Code Studio — Trợ Lý Lập Trình AI")
        self.setWindowIcon(get_pop_logo_icon(32))
        self.resize(1320, 840)
        self.setMinimumSize(800, 600)

        self.studio = CodeEditorStudioWidget(self, initial_dir=initial_dir)
        self.setCentralWidget(self.studio)

        # Delegate child attributes for backwards compatibility
        self.tab_widget = self.studio.tab_widget
        self.explorer_widget = self.studio.explorer_widget
        self.terminal_widget = self.studio.terminal_widget
        self.ai_panel = self.studio.ai_panel

    def _apply_ai_code(self, code: str):
        self.studio._apply_ai_code(code)

    def _update_ai_context(self):
        self.studio._update_ai_context()
