#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Pop Assistant - PyQt6 Interface
Trợ lý giọng nói thông minh với giao diện hiện đại
"""

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


def create_main_window(username):
    """Create main window with proper MVC structure."""
    try:
        print(f"Creating main window for user: {username}")

        from controller.pop_controller import PopController
        from view.ui.pop_view import PopView
        view = PopView(username)
        controller = PopController(view, login_username=username)
        controller.start()
        return view
    except Exception as e:
        print(f"Error creating main window: {e}")
        import traceback
        traceback.print_exc()
        return None
