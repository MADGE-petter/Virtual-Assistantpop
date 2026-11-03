"""
POP Window Manager - Manages frameless window dragging, resizing, starfield lifecycle,
and Desktop Mini Mascot floating assistant coordination.
"""

from PyQt6.QtCore import Qt, QPoint


class PopWindowManager:
    """Handles window movements, sizing, and coordination with Mini Mascot."""

    def __init__(self, main_window, mini_mascot, starfield):
        self.window = main_window
        self.mascot = mini_mascot
        self.starfield = starfield
        self._drag_pos = QPoint()

        # Connect mascot toggle request
        if self.mascot:
            self.mascot.toggleMainWindowRequested.connect(self.toggle_visibility_from_mascot)

    def handle_mouse_press(self, event):
        if event and event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.window.frameGeometry().topLeft()
            event.accept()

    def handle_mouse_move(self, event):
        if event and event.buttons() == Qt.MouseButton.LeftButton and not self.window.isMaximized():
            self.window.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def switch_to_mini_mascot(self):
        """Hide main window and reveal Mini Mascot."""
        self.window.hide()
        if self.mascot:
            self.mascot.show()
            self.mascot.raise_()

    def toggle_visibility_from_mascot(self):
        """Toggle main window visibility when double-clicking Mini Mascot."""
        if self.window.isVisible():
            self.switch_to_mini_mascot()
        else:
            if self.mascot:
                self.mascot.hide()
            self.window.show()
            self.window.raise_()
            self.window.activateWindow()
            self.window.setFocus()

    def toggle_maximize(self):
        if self.window.isMaximized():
            self.window.showNormal()
        else:
            self.window.showMaximized()

    def handle_resize(self, width: int, height: int):
        if self.starfield:
            self.starfield.setGeometry(0, 0, width, height)

    def handle_show(self):
        if self.starfield and hasattr(self.starfield, 'timer'):
            if not self.starfield.timer.isActive():
                self.starfield.timer.start(55)

    def handle_hide(self):
        if self.starfield and hasattr(self.starfield, 'timer'):
            if self.starfield.timer.isActive():
                self.starfield.timer.stop()
