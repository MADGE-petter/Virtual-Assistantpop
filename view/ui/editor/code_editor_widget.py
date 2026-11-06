"""Code Editor Widget with synchronized Line Number Gutter,
smart auto-indentation, current line highlight, and syntax highlighting.
"""
from typing import Optional
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt6.QtGui import (
    QColor, QPainter, QTextFormat, QTextCursor, QFont, QFontMetrics,
    QKeyEvent, QResizeEvent, QPaintEvent, QTextCharFormat
)
from PyQt6.QtWidgets import (
    QWidget, QPlainTextEdit, QTextEdit
)

from view.ui.editor.code_highlighter import CodeHighlighter


class LineNumberArea(QWidget):
    """Gutter widget displaying line numbers synchronized with the editor."""

    def __init__(self, editor: 'CodeEditorWidget'):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, a0: Optional[QPaintEvent]):
        if a0 is not None:
            self.code_editor.line_number_area_paint_event(a0)


class CodeEditorWidget(QPlainTextEdit):
    """High-performance native code editor for POP Assistant."""

    modificationChanged = pyqtSignal(bool)

    def __init__(self, parent=None, file_path: str = ""):
        super().__init__(parent)
        self.file_path = file_path
        self._is_modified = False

        # Font setup (Monospace)
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        # Tab stop = 4 spaces
        metrics = QFontMetrics(font)
        self.setTabStopDistance(4 * metrics.horizontalAdvance(' '))

        # Gutter line numbers
        self.line_number_area = LineNumberArea(self)

        # Connect internal signals
        self.blockCountChanged.connect(self._update_line_number_area_width)
        self.updateRequest.connect(self._update_line_number_area)
        self.cursorPositionChanged.connect(self._highlight_current_line)
        self.textChanged.connect(self._on_text_changed)

        self._update_line_number_area_width(0)
        self._highlight_current_line()

        # Syntax highlighter
        ext = file_path.split('.')[-1] if '.' in file_path else "python"
        self.highlighter = CodeHighlighter(self.document(), language=ext)

        # Dark translucent glass styling matching PopView
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: rgba(6, 10, 18, 0.60);
                color: #E2E8F0;
                border: 1px solid rgba(255, 255, 255, 0.05);
                border-radius: 8px;
                selection-background-color: rgba(0, 204, 255, 0.25);
                selection-color: #FFFFFF;
            }
        """)

    def set_file_path(self, path: str):
        self.file_path = path
        ext = path.split('.')[-1] if '.' in path else "python"
        self.highlighter.set_language(ext)

    def line_number_area_width(self) -> int:
        digits = 1
        m = max(1, self.blockCount())
        while m >= 10:
            m //= 10
            digits += 1
        space = 14 + self.fontMetrics().horizontalAdvance('9') * max(3, digits)
        return space

    def _update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def _update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        vp = self.viewport()
        if vp is not None and rect.contains(vp.rect()):
            self._update_line_number_area_width(0)

    def resizeEvent(self, e: Optional[QResizeEvent]):
        super().resizeEvent(e)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def _highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor(16, 24, 38, 140)  # Subtle dark cyber highlight
            fmt = QTextCharFormat()
            fmt.setBackground(line_color)
            fmt.setProperty(QTextFormat.Property.FullWidthSelection, True)

            cur = self.textCursor()
            cur.clearSelection()

            setattr(selection, "format", fmt)
            setattr(selection, "cursor", cur)
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor(6, 10, 18, 160))

        # Right border line for gutter
        painter.setPen(QColor(255, 255, 255, 15))
        w = self.line_number_area.width()
        painter.drawLine(w - 1, event.rect().top(), w - 1, event.rect().bottom())

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = round(self.blockBoundingGeometry(block).translated(self.contentOffset()).top())
        bottom = top + round(self.blockBoundingRect(block).height())

        current_block_num = self.textCursor().blockNumber()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                if block_number == current_block_num:
                    painter.setPen(QColor("#00FFAA"))  # Active line highlighted in emerald
                    font = painter.font()
                    font.setBold(True)
                    painter.setFont(font)
                else:
                    painter.setPen(QColor("#475569"))  # Inactive lines in slate grey
                    font = painter.font()
                    font.setBold(False)
                    painter.setFont(font)

                painter.drawText(
                    0, top, self.line_number_area.width() - 8, self.fontMetrics().height(),
                    Qt.AlignmentFlag.AlignRight, number
                )

            block = block.next()
            top = bottom
            bottom = top + round(self.blockBoundingRect(block).height())
            block_number += 1

    def keyPressEvent(self, e: Optional[QKeyEvent]):
        if e is None:
            return

        # 1. Tab key -> 4 spaces
        if e.key() == Qt.Key.Key_Tab and not e.modifiers():
            self.insertPlainText("    ")
            return

        # 2. Enter key -> Smart Auto-Indent
        if e.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            cursor = self.textCursor()
            line_text = cursor.block().text()
            # Calculate leading whitespace
            indent = ""
            for ch in line_text:
                if ch in (" ", "\t"):
                    indent += ch
                else:
                    break

            # If line ends with ':' or '{', increase indent
            stripped = line_text.rstrip()
            if stripped.endswith(":") or stripped.endswith("{"):
                indent += "    "

            super().keyPressEvent(e)
            self.insertPlainText(indent)
            return

        super().keyPressEvent(e)

    def _on_text_changed(self):
        if not self._is_modified:
            self._is_modified = True
            self.modificationChanged.emit(True)

    def mark_saved(self):
        self._is_modified = False
        self.modificationChanged.emit(False)

    def is_dirty(self) -> bool:
        return self._is_modified

    # ============ HELPER CODING METHODS FOR AI ============

    def get_selected_text(self) -> str:
        cursor = self.textCursor()
        return cursor.selectedText().replace('\u2029', '\n')

    def replace_selection(self, new_text: str):
        cursor = self.textCursor()
        if cursor.hasSelection():
            cursor.insertText(new_text)
        else:
            # If no selection, replace whole file or insert at cursor
            cursor.insertText(new_text)

    def insert_code_at_cursor(self, code: str):
        cursor = self.textCursor()
        cursor.insertText(code)

