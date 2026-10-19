"""
POP Navigation Manager - Coordinates UI routing between Central Stack (Chat Area vs Settings Tabs)
and smoothly animates side panel transitions.
"""

from PyQt6.QtCore import QObject, QVariantAnimation, QEasingCurve


class PopNavigation(QObject):
    """Manages view transitions and animated drawer/panel sliding."""

    def __init__(self, sidebar, center_stack, settings_page, right_panel, right_panel_line, parent=None):
        super().__init__(parent)
        self.sidebar = sidebar
        self.center_stack = center_stack
        self.settings_page = settings_page
        self.right_panel = right_panel
        self.right_panel_line = right_panel_line
        self._rp_anim = None

    def show_chat_view(self):
        """Switch to Chat Area in central stack and mode 0 in sidebar."""
        self.sidebar.set_mode(0)
        self.center_stack.setCurrentIndex(0)

    def open_settings_page(self, tab_index: int = 0):
        """Switch to Settings page with specific tab in central stack and mode 1 in sidebar."""
        self.sidebar.set_mode(1, tab_index)
        self.settings_page.open_tab(tab_index)
        self.center_stack.setCurrentIndex(1)

    def toggle_right_panel(self):
        """Smoothly slide open or closed the right telemetry panel with OutCubic curve."""
        is_open = self.right_panel.width() > 10 and self.right_panel.isVisible()
        start_w = self.right_panel.width() if is_open else 0
        target_w = 0 if is_open else 260

        if self._rp_anim and self._rp_anim.state() == QVariantAnimation.State.Running:
            self._rp_anim.stop()

        if not is_open:
            self.right_panel.show()
            if self.right_panel_line:
                self.right_panel_line.show()

        self._rp_anim = QVariantAnimation(self)
        self._rp_anim.setDuration(220)
        self._rp_anim.setStartValue(start_w)
        self._rp_anim.setEndValue(target_w)
        self._rp_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        def _on_step(val):
            w = int(val)
            self.right_panel.setFixedWidth(w)

        def _on_finish():
            if target_w == 0:
                self.right_panel.hide()
                if self.right_panel_line:
                    self.right_panel_line.hide()
            else:
                self.right_panel.setFixedWidth(260)

        self._rp_anim.valueChanged.connect(_on_step)
        self._rp_anim.finished.connect(_on_finish)
        self._rp_anim.start()
