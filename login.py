#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pop Assistant - Login Launcher
Chạy giao diện đăng nhập
"""

import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QApplication

def main():
    """Main function to run login application"""
    try:
        app = QApplication(sys.argv)
        app.setApplicationName("Pop Assistant Login")
        app.setOrganizationName("Pop AI")
        app.setQuitOnLastWindowClosed(False)
        
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

        from service.login_service import LoginService
        from view.login.login_view import LoginView

        # Tạo Service ở Controller level
        print("[Login] Creating LoginService...")
        login_service = LoginService()
        
        # Khởi tạo LoginView trực tiếp
        login_window = LoginView(login_service)
        main_window = None  # Khai báo để nonlocal hoạt động
        
        def on_logout():
            nonlocal main_window, login_window
            print("[Login] Đăng xuất thành công - Đang mở lại cửa sổ đăng nhập...")
            if main_window:
                if hasattr(main_window, 'mini_mascot') and main_window.mini_mascot:
                    main_window.mini_mascot.hide()
                    main_window.mini_mascot.close()
                main_window.hide()
                main_window.close()
                main_window = None

            login_window = LoginView(login_service)
            login_window.login_success.connect(on_login_success)
            login_window.show()
            login_window.raise_()
            login_window.activateWindow()

        def on_login_success(username):
            nonlocal main_window, login_window
            print(f"Login successful: {username}")

            # Đóng login window NGAY LẬP TỨC
            if login_window:
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

                    main_window.logoutRequested.connect(on_logout)

                    # Không hiển thị cửa sổ chat chính ngay, chỉ mở giao diện Mini Mascot lơ lửng.
                    # Muốn chat thì đúp chuột vào Mini Mascot để bật cửa sổ chat.
                    main_window.hide()
                    if hasattr(main_window, 'mini_mascot') and main_window.mini_mascot:
                        main_window.mini_mascot.show()
                        main_window.mini_mascot.raise_()
                    app.processEvents()
                    print(f"[Login] Đã khởi tạo Mini Mascot cho '{username}'. Đúp chuột vào Mini Mascot để mở cửa sổ chat.")
                except Exception as e:
                    print(f"Lỗi khởi tạo giao diện chính: {e}")
                    import traceback
                    traceback.print_exc()

            QTimer.singleShot(0, _init_main_window)

        login_window.login_success.connect(on_login_success)
        login_window.show()
        print("[Login] Login window shown, starting event loop...")
        
        # Run the application
        app.exec()
            
    except ImportError as e:
        print(f"Chi tiết lỗi: {e}")
        input("Nhấn Enter để thoát...")
    except Exception as e:
        print(f"Lỗi khởi động ứng dụng: {e}")
        input("Nhấn Enter để thoát...")

if __name__ == "__main__":
    main()
