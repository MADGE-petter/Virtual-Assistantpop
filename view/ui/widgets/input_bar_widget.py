"""
POP Input Bar Widget - Backward Compatibility Shim.
Tất cả các thành phần thanh nhập liệu đã được gom vào thư mục package:
    `view.ui.widgets.input_bar`
File này giữ vai trò chuyển tiếp (proxy) để đảm bảo không làm gãy các import cũ.
"""

from view.ui.widgets.input_bar import (
    InputBarWidget,
    MessageTextEdit,
    ModelComboBox,
    ModelItemDelegate,
    AttachedFileSquare,
)

__all__ = [
    "InputBarWidget",
    "MessageTextEdit",
    "ModelComboBox",
    "ModelItemDelegate",
    "AttachedFileSquare",
]
