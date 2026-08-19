"""
Login Widgets - Pop Assistant
Dialog phụ trợ cho màn hình đăng nhập (Settings, Toast/Message)
"""

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QCheckBox, QSpinBox, QSlider, QWidget
)



class ToastWidget(QWidget):
    """Custom toast notification matching dark theme"""
    def __init__(self, parent, message, type="error", duration=3000):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.ToolTip)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        
        # Colors by type
        colors = {
            "error": ("#FF4444", "#FF6666"),
            "success": ("#00FFAA", "#33FFBB"),
            "warning": ("#FFAA00", "#FFCC33"),
            "info": ("#00CCFF", "#33DDFF")
        }
        border_color, text_color = colors.get(type, colors["error"])
        
        # Style directly on self (ToastWidget) - single frame only
        self.setStyleSheet(f"""
            QWidget {{
                background: rgba(8, 12, 20, 240);
                border: 2px solid {border_color};
                border-radius: 20px;
            }}
        """)
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(28, 18, 28, 18)
        
        # Message only - single frame
        msg_label = QLabel(message)
        msg_label.setStyleSheet(f"color: {text_color}; font-size: 14px; font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;")
        msg_label.setWordWrap(False)
        layout.addWidget(msg_label, 1)
        
        self.adjustSize()
        
        # Position at top-center of parent
        self._position_at_top_center()
        
        # Animation: slide down + fade in
        self._animate_in()
        
        # Auto close timer
        QTimer.singleShot(duration, self._animate_out)
    
    def _position_at_top_center(self):
        if self.parent():
            parent_rect = self.parent().geometry()
            x = parent_rect.x() + (parent_rect.width() - self.width()) // 2
            y = parent_rect.y() + 20
            self.move(x, y)
    
    def _animate_in(self):
        # Start slightly above and transparent
        start_pos = self.pos()
        start_pos.setY(start_pos.y() - 20)
        self.move(start_pos)
        self.setWindowOpacity(0.0)
        self.show()
        
        self._anim = QPropertyAnimation(self, b"pos")
        self._anim.setDuration(300)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.setStartValue(start_pos)
        self._anim.setEndValue(self.pos())
        self._anim.start()
        
        self._opacity_anim = QPropertyAnimation(self, b"windowOpacity")
        self._opacity_anim.setDuration(300)
        self._opacity_anim.setStartValue(0.0)
        self._opacity_anim.setEndValue(1.0)
        self._opacity_anim.start()
    
    def _animate_out(self):
        self._fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self._fade_anim.setDuration(200)
        self._fade_anim.setStartValue(1.0)
        self._fade_anim.setEndValue(0.0)
        self._fade_anim.finished.connect(self.close)
        self._fade_anim.start()


def show_toast(parent, message, type="error", duration=3000):
    """Convenience function to show toast notification"""
    toast = ToastWidget(parent, message, type, duration)
    return toast
