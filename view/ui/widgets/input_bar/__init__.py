"""
Gói thành phần Input Bar (Thanh nhập liệu trò chuyện) cho POP Assistant.
Mô hình MVC - View Layer.

Các thành phần bao gồm:
1. InputBarWidget: Khung thanh nhập liệu chính với viền phát sáng, chứa ô nhập văn bản,
   các nút chức năng (đính kèm, mic, gửi tin), dropdown chọn model và dải xem trước tệp.
2. MessageTextEdit: Ô nhập văn bản hỗ trợ phím tắt Enter (gửi) và Shift+Enter (xuống dòng).
3. ModelComboBox: Dropdown danh sách mô hình AI với style bán trong suốt và căn lề phải.
4. ModelItemDelegate: Bộ tùy biến render item dropdown với icon, hover và đường kẻ phân cách.
5. AttachedFileSquare: Thẻ vuông preview tệp đính kèm (hình ảnh, tài liệu Office, PDF, code) kèm nút gỡ.
"""

from view.ui.widgets.input_bar.input_bar_widget import InputBarWidget
from view.ui.widgets.input_bar.message_text_edit import MessageTextEdit
from view.ui.widgets.input_bar.model_combo_box import ModelComboBox, ModelItemDelegate
from view.ui.widgets.input_bar.attached_file_square import AttachedFileSquare

__all__ = [
    "InputBarWidget",
    "MessageTextEdit",
    "ModelComboBox",
    "ModelItemDelegate",
    "AttachedFileSquare",
]
