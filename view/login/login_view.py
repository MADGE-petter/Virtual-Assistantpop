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
from view.ui.widgets.starfield_widget import StarfieldWidget


class LoginView(QDialog):
    login_success = pyqtSignal(str)
    
    def __init__(self, login_service):
        super().__init__()
        if login_service is None:
            raise ValueError("login_service is required - View must receive Service from Controller")
        self.login_service = login_service

        self.settings = self.login_service.load_settings()
        self._footer_label = None
        self._starfield = None
        self._is_register_mode = False
        self._drag_pos = None
        self.init_ui()
    
    def init_ui(self):
        """Khởi tạo giao diện đăng nhập tối giản: Chữ + 2 ô input + Button"""
        self.setWindowTitle("Pop Assistant")
        self.setFixedSize(320, 390)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        
        # Set style từ file login_styles
        self.setStyleSheet(MAIN_WINDOW_STYLE)
        
        # Create starfield background
        self._starfield = StarfieldWidget(self, star_count=16)
        self._starfield.setGeometry(0, 0, self.width(), self.height())
        self._starfield.lower()  # Send to back
        
        # Main layout
        layout = QVBoxLayout()
        layout.setSpacing(0)
        layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(layout)

        # Custom Frameless Window Control Bar (Top Right)
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(12, 10, 14, 0)
        top_bar.addStretch()

        btn_style = """
            QPushButton {
                background: transparent;
                color: rgba(200, 220, 240, 0.7);
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(0, 255, 170, 0.15);
                color: #00FFAA;
            }
        """
        close_btn_style = """
            QPushButton {
                background: transparent;
                color: rgba(200, 220, 240, 0.7);
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 6px;
            }
            QPushButton:hover {
                background: rgba(255, 75, 110, 0.25);
                color: #FF4B6E;
            }
        """

        min_btn = QPushButton("─")
        min_btn.setFixedSize(28, 24)
        min_btn.setStyleSheet(btn_style)
        min_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        min_btn.clicked.connect(self.showMinimized)

        close_btn = QPushButton("✕")
        close_btn.setFixedSize(28, 24)
        close_btn.setStyleSheet(close_btn_style)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.reject)

        top_bar.addWidget(min_btn)
        top_bar.addWidget(close_btn)
        layout.addLayout(top_bar)
        
        # Content Container (trực tiếp không cần khung bọc)
        content_box = QVBoxLayout()
        content_box.setContentsMargins(30, 8, 30, 16)
        content_box.setSpacing(12)

        # Title (Chữ)
        self.title = QLabel("POP ASSISTANT")
        self.title.setStyleSheet(TITLE_STYLE)
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        content_box.addWidget(self.title)
        
        # Form inputs
        form_layout = QVBoxLayout()
        form_layout.setSpacing(10)
        form_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Tên đăng nhập")
        self.username_input.setFixedSize(220, 36)
        self.username_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setPlaceholderText("Mật khẩu")
        self.password_input.setFixedSize(220, 36)
        self.password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        form_layout.addWidget(self.password_input)
        
        # Confirm Password (ẩn, dùng cho đăng ký)
        self.confirm_password_input = QLineEdit()
        self.confirm_password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.confirm_password_input.setPlaceholderText("Xác nhận mật khẩu")
        self.confirm_password_input.setFixedSize(220, 36)
        self.confirm_password_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.confirm_password_input.hide()
        form_layout.addWidget(self.confirm_password_input)
        
        # Action button
        self.action_btn = QPushButton("ĐĂNG NHẬP")
        self.action_btn.setObjectName("action_btn")
        self.action_btn.setFixedSize(220, 36)
        self.action_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.action_btn.clicked.connect(self.handle_action)
        form_layout.addWidget(self.action_btn)
        
        content_box.addLayout(form_layout)
        
        # Switch mode text
        self.switch_layout = QHBoxLayout()
        self.switch_layout.addStretch()
        
        self.switch_label = QLabel("Chưa có tài khoản? Đăng ký ngay")
        self.switch_label.setStyleSheet(REGISTER_LABEL_STYLE)
        self.switch_label.setCursor(Qt.CursorShape.PointingHandCursor)
        self.switch_label.mousePressEvent = self.toggle_mode
        self.switch_layout.addWidget(self.switch_label)
        self.switch_layout.addStretch()
        
        content_box.addLayout(self.switch_layout)
        
        layout.addStretch()
        layout.addLayout(content_box)
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

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton and self._drag_pos is not None:
            self.move(event.globalPosition().toPoint() - self._drag_pos)
            event.accept()

    def save_settings(self):
        """Lưu cài đặt người dùng qua Service"""
        self.login_service.save_settings(self.settings)

    def toggle_mode(self, event):
        """Chuyển đổi giữa đăng nhập và đăng ký"""
        self._is_register_mode = not self._is_register_mode
        
        if self._is_register_mode:
            self.title.setText("TẠO TÀI KHOẢN")
            self.action_btn.setText("ĐĂNG KÝ")
            self.switch_label.setText("Đã có tài khoản? Đăng nhập ngay")
            self.confirm_password_input.show()
            self.confirm_password_input.clear()
        else:
            self.title.setText("POP ASSISTANT")
            self.action_btn.setText("ĐĂNG NHẬP")
            self.switch_label.setText("Chưa có tài khoản? Đăng ký ngay")
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
