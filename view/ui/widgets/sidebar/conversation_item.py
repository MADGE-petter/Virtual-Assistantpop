"""
POP Sidebar - Conversation Item Component.
"""

from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from PyQt6.QtWidgets import (
    QHBoxLayout, QLabel, QPushButton, QFrame,
    QSizePolicy, QMenu
)

from view.ui.styles import DesignTokens
from view.ui.icons import create_vector_icon
from model.pop_chat_model import ConversationSession


class ConversationItemWidget(QFrame):
    """Single Conversation Item Widget in Left Sidebar - Clean, modern, borderless design."""

    clicked = pyqtSignal(str)
    deleteRequested = pyqtSignal(str)

    def __init__(self, session: ConversationSession, is_active: bool = False, is_collapsed: bool = False, parent=None):
        super().__init__(parent)
        self.session = session
        self.is_active = is_active
        self.is_collapsed = is_collapsed
        self.setObjectName("convItem")
        self.setFixedHeight(38)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._setup_ui()

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 4, 8, 4)
        layout.setSpacing(10)

        self.icon_lbl = QLabel()
        self.icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.icon_lbl.setFixedSize(16, 16)
        self.icon_lbl.setStyleSheet("border: none; background: transparent; padding: 0px;")

        self.title_lbl = QLabel()
        self.title_lbl.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        self.title_lbl.setStyleSheet("border: none; background: transparent; padding: 0px;")
        fm = self.title_lbl.fontMetrics()
        elided = fm.elidedText(self.session.title, Qt.TextElideMode.ElideRight, 130)
        self.title_lbl.setText(elided)
        self.title_lbl.setToolTip(self.session.title)

        self.time_lbl = QLabel(self.session.timestamp)
        self.time_lbl.setStyleSheet("border: none; background: transparent; padding: 0px;")

        self.dots_btn = QPushButton()
        self.dots_btn.setIcon(create_vector_icon("dots", "#64748B", 12))
        self.dots_btn.setFixedSize(22, 22)
        self.dots_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.dots_btn.setStyleSheet(
            "QPushButton { border: none; background: transparent; padding: 0px; } "
            "QPushButton:hover { background-color: rgba(255, 255, 255, 0.08); border-radius: 4px; }"
        )
        self.dots_btn.clicked.connect(self._show_options_menu)

        layout.addWidget(self.icon_lbl)
        layout.addWidget(self.title_lbl)
        layout.addWidget(self.time_lbl)
        layout.addWidget(self.dots_btn)

        self._update_collapsed_state(self.is_collapsed)
        self._update_style()

    def _show_options_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background-color: {DesignTokens.SURFACE_2}; border: 1px solid rgba(255,255,255,0.08); "
            f"border-radius: 8px; padding: 4px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QMenu::item {{ padding: 6px 14px; border-radius: 4px; font-size: 12px; }}"
            f"QMenu::item:selected {{ background-color: rgba(244, 63, 94, 0.16); color: #F43F5E; }}"
        )
        del_act = menu.addAction("Xóa cuộc trò chuyện")
        if del_act:
            del_act.triggered.connect(lambda: self.deleteRequested.emit(self.session.id))
        menu.exec(self.dots_btn.mapToGlobal(QPoint(0, self.dots_btn.height() + 2)))

    def _update_collapsed_state(self, collapsed: bool):
        self.is_collapsed = collapsed
        if collapsed:
            self.title_lbl.hide()
            self.time_lbl.hide()
            self.dots_btn.hide()
            self.setToolTip(self.session.title)
        else:
            self.title_lbl.show()
            self.time_lbl.show()
            self.dots_btn.show()
            self.setToolTip("")

    def _update_style(self):
        icon_color = "gradient" if self.is_active else "#64748B"
        self.icon_lbl.setPixmap(create_vector_icon("message", icon_color, 15).pixmap(15, 15))

        if self.is_active:
            self.title_lbl.setStyleSheet("color: #FFFFFF; font-size: 13px; font-weight: 500; border: none; background: transparent;")
            self.time_lbl.setStyleSheet("color: #64748B; font-size: 11px; font-weight: 400; border: none; background: transparent;")
            self.setStyleSheet(
                f"#convItem {{"
                f"  background-color: transparent;"
                f"  border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
                f"  border-left: 3px solid #00FFAA;"
                f"  border-radius: 8px;"
                f"}}"
                f"#convItem QLabel {{"
                f"  border: none;"
                f"  background: transparent;"
                f"}}"
            )
        else:
            self.title_lbl.setStyleSheet("color: #94A3B8; font-size: 13px; font-weight: 400; border: none; background: transparent;")
            self.time_lbl.setStyleSheet("color: #475569; font-size: 11px; font-weight: 400; border: none; background: transparent;")
            self.setStyleSheet(
                f"#convItem {{"
                f"  background-color: transparent;"
                f"  border: 1px solid transparent;"
                f"  border-radius: 8px;"
                f"}}"
                f"#convItem:hover {{"
                f"  background-color: rgba(255, 255, 255, 0.03);"
                f"  border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
                f"}}"
                f"#convItem QLabel {{"
                f"  border: none;"
                f"  background: transparent;"
                f"}}"
            )

    def mousePressEvent(self, a0):
        if a0 and a0.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.session.id)
        super().mousePressEvent(a0)
