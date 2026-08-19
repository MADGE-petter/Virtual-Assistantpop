#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Login View - Pop Assistant
Giao diện đăng nhập/đăng ký thống nhất
Deep dark theme with animated starfield background
"""

import os
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QMessageBox,
    QWidget
)

from view.login.login_styles import MAIN_WINDOW_STYLE, TITLE_STYLE, REGISTER_LABEL_STYLE
from view.login.login_widgets import show_toast
from view.login.starfield_widget import StarfieldWidget


class LoginView(QDialog):
    login_success = pyqtSignal(str)
    
    def __init__(self, login_service):
        super().__init__()
        # Service injection - View nhận Service từ Controller, không tự tạo
        if login_service is None:
            raise ValueError("login_service is required - View must receive Service from Controller")
        self.login_service = login_service

        self.settings = self.login_service.load_settings()
        self._footer_label = None
        self._starfield = None
        self._is_register_mode = False
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện đăng nhập với starfield background"""
        self.setWindowTitle("Pop Assistant")
        self.setFixedSize(380, 480)
        
        # Set style từ file login_styles
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Create starfield background (as child widget, behind everything)
        self._starfield = StarfieldWidget(self, star_count=150)
        self._starfield.setGeometry(0, 0, self.width(), self.height())
        self._starfield.lower()  # Send to back
        
        # Main layout - center everything vertically and horizontally
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)
        
        # Center container
        center_widget = QWidget()
        center_layout = QVBoxLayout(center_widget)
        center_layout.setSpacing(16)
        center_layout.setContentsMargins(40, 40, 40, 40)
        
        # Title with gradient text
        self.title = QLabel("POP ASSISTANT")
        self.title.setStyleSheet(TITLE_STYLE)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        center_layout.addWidget(self.title)
        
        # Form container - fixed width for consistent sizing
        form_container = QWidget()
        form_container.setFixedWidth(280)
        form_layout = QVBoxLayout(form_container)
        form_layout.setSpacing(12)
        form_layout.setContentsMargins(0, 0, 0, 0)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        self.username_input.setFixedHeight(44)
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setFixedHeight(44)
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.password_input)
        
        # Confirm Password (hidden by default, shown in register mode)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Xác nhận mật khẩu")
        self.confirm_password_input.setFixedHeight(44)
        self.confirm_password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirm_password_input.hide()
        form_layout.addWidget(self.confirm_password_input)
        
        # Action button
        self.action_btn = QPushButton("Đăng nhập")
        self.action_btn.setFixedHeight(44)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self.handle_action)
        form_layout.addWidget(self.action_btn)
        
        center_layout.addWidget(form_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Switch mode text
        self.switch_layout = QHBoxLayout()
        self.switch_layout.addStretch()
        
        self.switch_label = QLabel("Chưa có tài khoản? Đăng ký")
        self.switch_label.setStyleSheet(REGISTER_LABEL_STYLE)
        self.switch_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch_label.mousePressEvent = self.toggle_mode
        self.switch_layout.addWidget(self.switch_label)
        self.switch_layout.addStretch()
        
        center_layout.addLayout(self.switch_layout)
        center_layout.addStretch()
        
        # Add center widget to main layout with stretches for vertical centering
        layout.addStretch()
        layout.addWidget(center_widget, alignment=Qt.AlignmentFlag.AlignCenter)
        layout.addStretch()
        self._create_footer()

    def _create_footer(self):
        """Tạo footer version info đơn giản"""
        from PyQt6.QtWidgets import QLabel
        from PyQt6.QtCore import Qt
        self._footer_label = QLabel("Pop Assistant v1.0", self)
        self._footer_label.setStyleSheet("color: rgba(255,255,255,100); font-size: 10px;")
        self._footer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._footer_label.adjustSize()
        self._position_footer()

    def _position_footer(self):
        """Cập nhật vị trí footer"""
        if self._footer_label:
            self._footer_label.move(
                (self.width() - self._footer_label.width()) // 2,
                self.height() - self._footer_label.height() - 10
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_footer()

    def save_settings(self):
        """Lưu cài đặt người dùng qua Service"""
        self.login_service.save_settings(self.settings)

    def toggle_mode(self, event):
        """Chuyển đổi giữa đăng nhập và đăng ký"""
        self._is_register_mode = not self._is_register_mode
        
        if self._is_register_mode:
            # Chuyển sang đăng ký - đổi title thành TẠO TÀI KHOẢN với gradient
            self.title.setText("TẠO TÀI KHOẢN")
            self.title.setStyleSheet("""
                QLabel {
                    color: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                   stop:0 #00ffaa, stop:1 #00ccff);
                    font-size: 32px;
                    font-weight: 300;
                    font-family: 'Segoe UI', 'Microsoft YaHei', sans-serif;
                    text-align: center;
                    padding: 20px;
                }
            """)
            self.action_btn.setText("Đăng ký")
            self.switch_label.setText("Đã có tài khoản? Đăng nhập")
            self.confirm_password_input.show()
            self.confirm_password_input.clear()
        else:
            # Chuyển về đăng nhập - title về POP ASSISTANT
            self.title.setText("POP ASSISTANT")
            self.title.setStyleSheet(TITLE_STYLE)
            self.action_btn.setText("Đăng nhập")
            self.switch_label.setText("Chưa có tài khoản? Đăng ký")
            self.confirm_password_input.hide()
            self.confirm_password_input.clear()
        
        # Clear inputs when switching
        self.username_input.clear()
        self.password_input.clear()

    def handle_action(self):
        """Xử lý đăng nhập hoặc đăng ký tùy theo mode"""
        if self._is_register_mode:
            self.handle_register()
        else:
            self.handle_login()

    def handle_login(self):
        """Xử lý đăng nhập"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        print(f"[LoginView] Login attempt: username='{username}'")
        
        if not username or not password:
            print("[LoginView] Empty username or password")
            show_toast(self, "Vui lòng điền đầy đủ thông tin!", "error")
            return
            
        if self.login_service.authenticate_user(username, password):
            print(f"[LoginView] Login successful for: {username}")
            self.login_success.emit(username)
            self.accept()
        else:
            print("[LoginView] Login failed")
            show_toast(self, "Tên đăng nhập hoặc mật khẩu không chính xác!", "error")

    def handle_register(self):
        """Xử lý đăng ký"""
        username = self.username_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        
        print(f"[LoginView] Register attempt: username='{username}'")
        
        if not username or not password:
            show_toast(self, "Vui lòng điền đầy đủ thông tin!", "error")
            return
            
        if password != confirm_password:
            show_toast(self, "Mật khẩu xác nhận không khớp!", "error")
            return
            
        if len(password) < 6:
            show_toast(self, "Mật khẩu phải có ít nhất 6 ký tự!", "warning")
            return
            
        if self.login_service.save_new_user(username, password):
            show_toast(self, "Đăng ký tài khoản thành công!", "success")
            # Tự động chuyển về đăng nhập
            self.toggle_mode(None)
        else:
            QMessageBox.warning(self, "Lỗi", "Tên đăng nhập đã tồn tại!")
