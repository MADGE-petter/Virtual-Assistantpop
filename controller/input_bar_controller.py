"""
POP Input Bar Controller - Điều phối giữa InputBarWidget (View) và InputBarModel (Model).
Tuân thủ nghiêm ngặt mô hình MVC:
- Tiếp nhận các sự kiện người dùng từ View (gửi tin, đính kèm tệp, đổi mô hình, mở hub).
- Thao tác với Model để xử lý nghiệp vụ (quét mô hình, đọc tài liệu, chuẩn bị prompt).
- Cập nhật lại trạng thái hiển thị của View.
"""

from typing import Optional, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QWidget
from model.input_bar_model import InputBarModel


class InputBarController(QObject):
    """Controller điều phối Input Bar theo chuẩn MVC."""

    # Tín hiệu phát ra ngoài cho ChatAreaWidget / PopView
    sendMessage = pyqtSignal(str)
    voiceToggle = pyqtSignal()
    switchModel = pyqtSignal(str)
    attachmentClicked = pyqtSignal()

    def __init__(self, view=None, model: Optional[InputBarModel] = None):
        super().__init__()
        self.model: InputBarModel = model if model is not None else InputBarModel()
        self.view = None
        if view is not None:
            self.set_view(view)

    def set_view(self, view):
        """Thiết lập View và kết nối các signal từ View tới Controller."""
        self.view = view
        self._connect_signals()

    def _connect_signals(self):
        if not self.view:
            return

        # Kết nối các tín hiệu yêu cầu hành động từ View
        if hasattr(self.view, "sendActionRequested"):
            self.view.sendActionRequested.connect(self.handle_send)
        if hasattr(self.view, "attachFileRequested"):
            self.view.attachFileRequested.connect(self.handle_attach_click)
        if hasattr(self.view, "removeFileRequested"):
            self.view.removeFileRequested.connect(self.handle_remove_file)
        if hasattr(self.view, "modelChangeRequested"):
            self.view.modelChangeRequested.connect(self.handle_model_changed)
        if hasattr(self.view, "openModelHubRequested"):
            self.view.openModelHubRequested.connect(self.handle_open_model_hub)
        if hasattr(self.view, "voiceToggleRequested"):
            self.view.voiceToggleRequested.connect(lambda: self.voiceToggle.emit())

    def load_local_models(self):
        """Quét các model local từ Model và cập nhật lên View."""
        models = self.model.scan_local_models()
        if self.view and hasattr(self.view, "set_models"):
            self.view.set_models(models)

    def handle_attach_click(self):
        """Mở hộp thoại chọn tệp tin và cập nhật danh sách đính kèm."""
        self.attachmentClicked.emit()
        if not self.view:
            return

        file_paths, _ = QFileDialog.getOpenFileNames(
            self.view,
            "Chọn các tệp để đính kèm (Hình ảnh, Word, Excel, PPT, PDF, Code, Văn bản...)",
            "",
            "Tất cả tệp hỗ trợ (*.png *.jpg *.jpeg *.webp *.bmp *.docx *.doc *.xlsx *.xls *.pptx *.ppt *.pdf *.txt *.md *.py *.json *.csv *.xml *.html *.js *.ts *.cpp *.c *.java *.rs *.sql);;"
            "Hình ảnh (*.png *.jpg *.jpeg *.webp *.bmp *.gif);;"
            "Microsoft Office & PDF (*.docx *.xlsx *.pptx *.pdf *.xls *.ppt);;"
            "Mã nguồn & Văn bản (*.txt *.md *.py *.json *.csv *.sql *.xml *.html);;"
            "Tất cả tệp (*.*)"
        )
        if file_paths:
            self.add_attached_files(file_paths)

    def add_attached_files(self, file_paths: List[str]):
        """Thêm các tệp đính kèm vào Model và cập nhật View."""
        changed = self.model.add_attached_files(file_paths)
        if changed and self.view and hasattr(self.view, "render_attached_files"):
            self.view.render_attached_files(self.model.get_attached_files())

    def handle_remove_file(self, file_path: str):
        """Gỡ bỏ một tệp khỏi Model và cập nhật View."""
        if self.model.remove_attached_file(file_path):
            if self.view and hasattr(self.view, "render_attached_files"):
                self.view.render_attached_files(self.model.get_attached_files())

    def clear_attached_files(self):
        """Xóa toàn bộ tệp đính kèm khỏi Model và View."""
        self.model.clear_attached_files()
        if self.view and hasattr(self.view, "render_attached_files"):
            self.view.render_attached_files([])

    def handle_model_changed(self, model_name: str):
        """Xử lý sự kiện người dùng chọn mô hình khác trên dropdown."""
        self.model.selected_model = model_name
        active_model = "" if model_name == "Auto" else model_name
        self.switchModel.emit(active_model)

    def handle_open_model_hub(self):
        """Mở kho mô hình (tab Model Download trong Settings)."""
        if not self.view:
            return

        win = self.view.window()
        if win and hasattr(win, "_open_settings_page"):
            getattr(win, "_open_settings_page")(2)
            return

        from view.ui.settings import SettingsDialog
        dialog = SettingsDialog(username="Tài khoản", initial_tab=2, parent=self.view)
        dialog.modelDownloaded.connect(self.load_local_models)
        dialog.exec()

    def handle_send(self, user_text: Optional[str] = None):
        """
        Xử lý khi người dùng nhấn Gửi hoặc Enter.
        Nếu user_text không được truyền vào, sẽ lấy trực tiếp từ View.
        """
        if user_text is None and self.view and hasattr(self.view, "get_text"):
            user_text = self.view.get_text()
        user_text = (user_text or "").strip()

        attached_files = self.model.get_attached_files()
        if not user_text and not attached_files:
            return

        final_message = self.model.build_message_payload(user_text)

        # Xóa đính kèm sau khi gửi
        self.clear_attached_files()

        # Xóa ô nhập liệu
        if self.view and hasattr(self.view, "clear_input"):
            self.view.clear_input()

        if final_message:
            self.sendMessage.emit(final_message)
