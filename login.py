#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pop Assistant - Login Launcher
Chạy giao diện đăng nhập
"""

import os
import sys
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import QApplication

def main():
    """Main function to run login application"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Pop Assistant Login")
        app.setOrganizationName("Pop AI")
        app.setQuitOnLastWindowClosed(True)
        
        # Set application icon
        try:
            from PyQt6.QtGui import QIcon
            from utils.paths import resource_path
            icon_path = resource_path('assets', 'icon.png')
            if os.path.exists(icon_path):
                app.setWindowIcon(QIcon(icon_path))
            else:
                print(f"[Login] Icon not found: {icon_path}")
        except Exception as e:
            print(f"[Login] Could not set icon: {e}")

        # Import temperature_monitor để quản lý OHM lifecycle
        _monitor_ref = None
        try:
            from model.temperature_monitor import _monitor
            _monitor_ref = _monitor
        except Exception as e:
            print(f"[Login] Không import được temperature_monitor: {e}")
        
        def on_app_exit():
            try:
                if _monitor_ref:
                    _monitor_ref.stop_ohm()
            except Exception as e:
                print(f"[Login] Lỗi dừng OHM: {e}")
        
        app.aboutToQuit.connect(on_app_exit)

        from service.login_service import LoginService
        from view.login.login_view import LoginView

        # Tạo Service ở Controller level
        print("[Login] Creating LoginService...")
        login_service = LoginService()
        print(f"[Login] LoginService created, db_path: {login_service.db_path}")
        print(f"[Login] Auth test: {login_service.authenticate_user('tuấn', '123123')}")
        
        # Khởi tạo LoginView trực tiếp
        login_window = LoginView(login_service)
        main_window = None  # Khai báo để nonlocal hoạt động
        
        def on_login_success(username):
            nonlocal main_window
            print(f"Login successful: {username}")

            # Đóng login window NGAY LẬP TỨC
            login_window.hide()
            login_window.close()
            app.processEvents()

            # Gọi Pop View (Main Window) khi đăng nhập thành công
            def _init_main_window():
                nonlocal main_window
                try:
                    import main
                    main_window = main.create_main_window(username)

                    if main_window is None:
                        return

                    main_window.show()
                    main_window.raise_()
                    main_window.activateWindow()
                    main_window.setFocus()
                    app.processEvents()
                except Exception as e:
                    print(f"Lỗi khởi tạo giao diện chính: {e}")
                    import traceback
                    traceback.print_exc()

            QTimer.singleShot(0, _init_main_window)

        login_window.login_success.connect(on_login_success)
        login_window.show()
        print("[Login] Login window shown, starting event loop...")
        
        # Run the application
        result = app.exec()
        print(f"[Login] App exec returned: {result}")
        # Check final state
        widgets = QApplication.topLevelWidgets()
        visible_count = 0
        for widget in widgets:
            if widget.isVisible():
                visible_count += 1
                title = widget.windowTitle() if hasattr(widget, 'windowTitle') else 'No Title'
                print(f"  Visible: {title}")
        
        print(f"Total visible: {visible_count}")
            
    except ImportError as e:
        print(f"Chi tiết lỗi: {e}")
        input("Nhấn Enter để thoát...")
    except Exception as e:
        print(f"Lỗi khởi động ứng dụng: {e}")
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()
