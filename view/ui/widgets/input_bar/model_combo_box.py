"""
ModelComboBox & ModelItemDelegate - Dropdown chọn mô hình AI (LLM Models).
- Hỗ trợ hiển thị danh sách bán trong suốt (glassmorphism).
- Vẽ đường phân cách giữa các mô hình.
- Đổi màu sáng khi di chuột qua từng dòng (hover highlight).
- Tự động căn chỉnh popup về mép phải của Input Bar.
"""

from typing import cast
from PyQt6.QtCore import Qt, QSize, QRect, QRectF
from PyQt6.QtGui import QColor, QPainter, QPen, QBrush, QIcon
from PyQt6.QtWidgets import (
    QComboBox, QStyledItemDelegate, QStyleOptionViewItem, QStyle, QWidget
)


class ModelItemDelegate(QStyledItemDelegate):
    """Custom item delegate to render semi-transparent dropdown items,
    horizontal dividing lines between all rows, and distinct hover brightening."""

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.TextAntialiasing)

        rect = cast(QRect, option.rect)
        is_hovered = bool(cast(QStyle.StateFlag, option.state) & (QStyle.StateFlag.State_MouseOver | QStyle.StateFlag.State_Selected))

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
        divider_pen = QPen(QColor(255, 255, 255, 30), 1)
        painter.setPen(divider_pen)
        painter.drawLine(rect.left() + 8, rect.bottom(), rect.right() - 8, rect.bottom())

        painter.restore()

    def sizeHint(self, option: QStyleOptionViewItem, index):
        return QSize(cast(QRect, option.rect).width(), 36)


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
            viewport = view.viewport()
            if viewport is not None:
                viewport.setMouseTracking(True)
                viewport.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.setItemDelegate(ModelItemDelegate(self))

    def showPopup(self):
        fm = self.fontMetrics()
        optimal_width = 240
        for i in range(self.count()):
            text = self.itemText(i)
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
