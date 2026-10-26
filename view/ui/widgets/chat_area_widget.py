"""
POP Chat Area Widget - Backward Compatibility Shim.
Tất cả các thành phần khu vực chat đã được module hóa vào thư mục package:
    `view.ui.widgets.chat_area`
File này giữ vai trò chuyển tiếp (proxy) để đảm bảo không làm gãy các import cũ.
"""

from view.ui.widgets.chat_area import (
    ActionConfirmationCardWidget,
    FilePreviewCardWidget,
    ThinkingIndicatorWidget,
    MessageBubbleWidget,
    ChatHeaderBarWidget,
    ChatAreaWidget,
)

__all__ = [
    "ActionConfirmationCardWidget",
    "FilePreviewCardWidget",
    "ThinkingIndicatorWidget",
    "MessageBubbleWidget",
    "ChatHeaderBarWidget",
    "ChatAreaWidget",
]
