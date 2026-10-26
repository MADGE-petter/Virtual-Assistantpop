"""
POP Sidebar Widget - Backward Compatibility Shim.
Tất cả các thành phần thanh bên trái đã được module hóa vào thư mục package:
    `view.ui.widgets.sidebar`
File này giữ vai trò chuyển tiếp (proxy) để đảm bảo không làm gãy các import cũ.
"""

from view.ui.widgets.sidebar import (
    ConversationItemWidget,
    AvatarPopupMenu,
    SidebarWidget,
)

__all__ = [
    "ConversationItemWidget",
    "AvatarPopupMenu",
    "SidebarWidget",
]
