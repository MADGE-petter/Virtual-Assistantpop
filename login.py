#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pop Assistant - Login Launcher
Chạy giao diện đăng nhập
"""

import os
import sys
import traceback


def show_fatal_error(error_msg: str):
    """Hiển thị chi tiết lỗi ra màn hình console, ghi file log và hiện popup Windows."""
    border = "=" * 65
    print(f"\n{border}\n  [POP ASSISTANT - ERROR REPORT]\n{border}\n")
    print(error_msg)
    print(f"\n{border}")
    
    # Ghi file crash.log
    try:
        from utils.paths import get_writeable_path
        log_path = get_writeable_path("crash.log")
    except Exception:
        log_path = os.path.join(os.path.expanduser("~"), "PopAssistant_crash.log")
    
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(error_msg)
        print(f"[Log] Đã lưu thông tin lỗi tại: {log_path}")
    except Exception:
        pass

    # Hiện dialog thông báo Windows native (không phụ thuộc vào PyQt6)
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, error_msg[:1000], "Pop Assistant - Lỗi khởi động", 0x10)
    except Exception:
        pass

    # Giữ cửa sổ console mở để người dùng xem lỗi
    print("\nNhấn Enter để đóng cửa sổ...")
    try:
        input()
    except Exception:
        pass


def main():
    """Main function to run login application"""
    print("=" * 65)
    print("  POP ASSISTANT - CONSOLE LOG MONITOR")
    print("=" * 65)
    print("[PopAssistant] Đang khởi động hệ thống...")

    try:
        from PyQt6.QtCore import QTimer
        from PyQt6.QtWidgets import QApplication

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

        # Apply global typography (Arial)
        from view.ui.styles import init_fonts
        init_fonts()

        from controller.login_controller import LoginController

        print("[Login] Initializing LoginController (MVC)...")
        login_controller = LoginController()
        main_window = None  # Khai báo để nonlocal hoạt động
        
        def on_logout():
            nonlocal main_window, login_controller
            print("[Login] Đăng xuất thành công - Đang mở lại cửa sổ đăng nhập...")
            if main_window:
                if hasattr(main_window, 'mini_mascot') and main_window.mini_mascot:
                    main_window.mini_mascot.hide()
                    main_window.mini_mascot.close()
                main_window.hide()
                main_window.close()
                main_window = None

            login_controller = LoginController()
            login_controller.login_success.connect(on_login_success)
            login_controller.exit_requested.connect(app.quit)
            login_controller.show()

        def on_login_success(username):
            nonlocal main_window, login_controller
            print(f"[Login] Đăng nhập thành công: {username}")

            # Đóng login window NGAY LẬP TỨC
            if login_controller:
                login_controller.hide()
                login_controller.close()
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
                    traceback.print_exc()

            QTimer.singleShot(0, _init_main_window)

        login_controller.login_success.connect(on_login_success)
        login_controller.exit_requested.connect(app.quit)
        
        login_controller.show()
        print("[Login] Giao diện đăng nhập đã sẵn sàng. Đang chạy vòng lặp sự kiện...")
        
        # Run the application
        sys.exit(app.exec())
            
    except Exception as e:
        err_detail = f"Lỗi không thể khởi động ứng dụng:\n{e}\n\nTraceback:\n{traceback.format_exc()}"
        show_fatal_error(err_detail)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        err_detail = f"Lỗi nghiêm trọng cấp hệ thống:\n{e}\n\nTraceback:\n{traceback.format_exc()}"
        show_fatal_error(err_detail)
