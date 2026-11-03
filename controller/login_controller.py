# -*- coding: utf-8 -*-
"""
Login Controller - Điều phối xác thực và giao diện đăng nhập (Controller Layer).
Tuân thủ nghiêm ngặt mô hình MVC: Làm cầu nối giữa LoginView và LoginService.
"""

from PyQt6.QtCore import QObject, pyqtSignal
from service.login_service import LoginService
from view.login.login_view import LoginView


class LoginController(QObject):
    """Controller điều phối xác thực người dùng và quản lý vòng đời LoginView."""

    login_success = pyqtSignal(str)
    exit_requested = pyqtSignal()

    def __init__(self, view=None, service=None):
        super().__init__()
        self.service = service if service is not None else LoginService()
        self.view = view if view is not None else LoginView(controller=self)

        # Đảm bảo view trỏ về controller
        if hasattr(self.view, 'set_controller'):
            self.view.set_controller(self)

        self._connect_signals()
        self._init_data()

    def _connect_signals(self):
        """Kết nối các signals từ View tới Controller slots."""
        if hasattr(self.view, 'login_requested'):
            self.view.login_requested.connect(self.handle_login)
        if hasattr(self.view, 'register_requested'):
            self.view.register_requested.connect(self.handle_register)
        if hasattr(self.view, 'exit_requested'):
            self.view.exit_requested.connect(self.exit_requested.emit)

    def _init_data(self):
        """Khởi tạo dữ liệu tự động đăng nhập (nếu có) từ Service và đưa lên View."""
        try:
            auto_data = self.service.get_auto_login()
            if isinstance(auto_data, dict):
                username = auto_data.get("username", "")
                password = auto_data.get("password", "")
                if hasattr(self.view, 'set_credentials'):
                    self.view.set_credentials(username, password)
        except Exception as e:
            print(f"[LoginController] Lỗi nạp auto-login: {e}")

    def handle_login(self, username: str, password: str):
        """Xử lý yêu cầu đăng nhập từ View."""
        print(f"[LoginController] Xử lý đăng nhập: '{username}'")

        if not username or not password:
            self.view.show_toast("Vui lòng điền đầy đủ thông tin!", "error")
            return

        if self.service.authenticate_user(username, password):
            print(f"[LoginController] Đăng nhập thành công: {username}")
            try:
                self.service.save_auto_login(username, password)
            except Exception as e:
                print(f"[LoginController] Không thể lưu auto login: {e}")

            self.view.hide()
            self.view.accept()
            self.login_success.emit(username)
        else:
            print(f"[LoginController] Đăng nhập thất bại cho '{username}'")
            self.view.show_toast("Tên đăng nhập hoặc mật khẩu không chính xác!", "error")

    def handle_register(self, username: str, password: str, confirm_password: str):
        """Xử lý yêu cầu đăng ký từ View."""
        print(f"[LoginController] Xử lý đăng ký: '{username}'")

        if not username or not password:
            self.view.show_toast("Vui lòng điền đầy đủ thông tin!", "error")
            return

        if password != confirm_password:
            self.view.show_toast("Mật khẩu xác nhận không khớp!", "error")
            return

        if len(password) < 6:
            self.view.show_toast("Mật khẩu phải có ít nhất 6 ký tự!", "warning")
            return

        if self.service.save_new_user(username, password):
            print(f"[LoginController] Đăng ký thành công cho '{username}'")
            self.view.show_toast("Đăng ký thành công!", "success")
            try:
                self.service.save_auto_login(username, password)
            except Exception as e:
                print(f"[LoginController] Không thể lưu auto login: {e}")

            self.view.hide()
            self.view.accept()
            self.login_success.emit(username)
        else:
            self.view.show_error_dialog("Lỗi", "Tên đăng nhập đã tồn tại!")

    def show(self):
        """Hiển thị cửa sổ đăng nhập."""
        if self.view:
            self.view.show()
            self.view.raise_()
            self.view.activateWindow()

    def hide(self):
        """Ẩn cửa sổ đăng nhập."""
        if self.view:
            self.view.hide()

    def close(self):
        """Đóng cửa sổ đăng nhập."""
        if self.view:
            self.view.close()
