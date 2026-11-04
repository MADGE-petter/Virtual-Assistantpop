"""
Mascot IPC Bridge - Hybrid Architecture Layer (Python <-> C++ Native Core).
Manages independent C++ Native Mascot process or seamlessly falls back to Python MiniMascotWidget.
IPC Channel: QLocalServer / QLocalSocket (Local Named Pipe '\\\\.\\pipe\\pop_mascot_ipc').
"""

import json
import os
import subprocess
import sys
from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal, QPoint, QRect, QTimer
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

from model.voice_state_model import VoiceState
from utils.paths import resource_path


class MascotIpcBridge(QObject):
    """
    Unified Mascot Interface for PopView.
    - If native/bin/PopMascotNative.exe exists, spawns it as an independent 60 FPS C++ process.
    - If not, falls back seamlessly to Python MiniMascotWidget (zero disruption).
    """

    toggleMainWindowRequested = pyqtSignal()
    toggleVoiceRequested = pyqtSignal()
    openCollectionRequested = pyqtSignal()

    PIPE_NAME = "pop_mascot_ipc"

    def __init__(self, parent=None):
        super().__init__(parent)
        self._native_process: Optional[subprocess.Popen] = None
        self._server: Optional[QLocalServer] = None
        self._socket: Optional[QLocalSocket] = None
        self._fallback_widget = None
        self._is_native = False

        self._current_char = None
        self._current_state = VoiceState.READY
        self._is_visible = False
        self._pos = QPoint(100, 100)
        self._coll_svc = None

        # Check for compiled native binary
        native_exe = self._get_native_exe_path()
        if native_exe and os.path.isfile(native_exe):
            self._init_native_ipc(native_exe)
        else:
            self._init_fallback_widget(parent)

    # ============================================================
    # NATIVE C++ IPC INITIALIZATION
    # ============================================================

    @staticmethod
    def _get_native_exe_path() -> Optional[str]:
        candidates = [
            resource_path(os.path.join("native", "bin", "PopMascotNative.exe")),
            os.path.abspath(os.path.join("native", "bin", "PopMascotNative.exe")),
            os.path.abspath(os.path.join("native", "build", "Release", "PopMascotNative.exe")),
            os.path.abspath(os.path.join("native", "build", "PopMascotNative.exe")),
        ]
        for p in candidates:
            if os.path.isfile(p):
                return p
        return None

    def _init_native_ipc(self, exe_path: str):
        """Start local IPC server and launch native C++ mascot process."""
        print(f"[MascotIPC] Found native C++ mascot: {exe_path}")
        self._server = QLocalServer(self)
        QLocalServer.removeServer(self.PIPE_NAME)

        if not self._server.listen(self.PIPE_NAME):
            print(f"[MascotIPC] Failed to start IPC server: {self._server.errorString()}, falling back.")
            self._init_fallback_widget()
            return

        self._server.newConnection.connect(self._on_client_connected)

        try:
            # Spawn independent high-performance native process
            self._native_process = subprocess.Popen(
                [exe_path, f"--pipe={self.PIPE_NAME}"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._is_native = True
            print(f"[MascotIPC] Spawned native process PID {self._native_process.pid}")
        except Exception as e:
            print(f"[MascotIPC] Error launching native mascot: {e}, falling back to Python widget.")
            self._init_fallback_widget()

    def _on_client_connected(self):
        """Handle connection from native C++ mascot."""
        if not self._server:
            return
        self._socket = self._server.nextPendingConnection()
        if not self._socket:
            return
        print("[MascotIPC] Native C++ Mascot connected to IPC bus!")
        self._socket.readyRead.connect(self._on_data_received)
        self._socket.disconnected.connect(self._on_client_disconnected)

        # Sync initial state to native mascot
        if self._current_char:
            self.set_character(self._current_char)
        self.set_voice_state(self._current_state)
        self.setVisible(self._is_visible)

    def _on_client_disconnected(self):
        print("[MascotIPC] Native mascot disconnected.")
        self._socket = None

    def _on_data_received(self):
        """Parse incoming JSON events from C++ native mascot."""
        if not self._socket:
            return
        raw = self._socket.readAll().data().decode("utf-8", errors="ignore")
        for line in raw.split("\n"):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                ev = data.get("event")
                if ev == "toggle_main_window":
                    self.toggleMainWindowRequested.emit()
                elif ev == "toggle_mic":
                    self.toggleVoiceRequested.emit()
                elif ev == "open_collection":
                    self.openCollectionRequested.emit()
                elif ev == "position_changed":
                    x = data.get("x", self._pos.x())
                    y = data.get("y", self._pos.y())
                    self._pos = QPoint(int(x), int(y))
            except Exception as e:
                print(f"[MascotIPC] Packet parse error: {e}")

    def _send_cmd(self, cmd_dict: dict):
        """Send JSON command to C++ native mascot over IPC."""
        if self._socket and self._socket.isOpen():
            try:
                payload = json.dumps(cmd_dict, ensure_ascii=False) + "\n"
                self._socket.write(payload.encode("utf-8"))
                self._socket.flush()
            except Exception as e:
                print(f"[MascotIPC] Send command error: {e}")

    # ============================================================
    # FALLBACK PYTHON WIDGET
    # ============================================================

    def _init_fallback_widget(self, parent=None):
        """Initialize in-process MiniMascotWidget when native C++ binary is not present."""
        from view.ui.mascot.mascot_widget import MiniMascotWidget
        self._is_native = False
        self._fallback_widget = MiniMascotWidget(parent=parent)
        self._fallback_widget.toggleMainWindowRequested.connect(self.toggleMainWindowRequested.emit)
        self._fallback_widget.toggleVoiceRequested.connect(self.toggleVoiceRequested.emit)
        self._fallback_widget.openCollectionRequested.connect(self.openCollectionRequested.emit)
        print("[MascotIPC] Running in Python in-process mode (MiniMascotWidget).")

    # ============================================================
    # UNIFIED PUBLIC API (Matches MiniMascotWidget)
    # ============================================================

    @property
    def is_native(self) -> bool:
        return self._is_native

    @property
    def voice_state(self) -> VoiceState:
        return self._current_state

    @voice_state.setter
    def voice_state(self, state: VoiceState):
        self.set_voice_state(state)

    @property
    def _settings(self):
        if self._fallback_widget:
            return self._fallback_widget._settings
        from PyQt6.QtCore import QSettings
        return QSettings("PopAI", "MiniMascot")

    @property
    def _collection_service(self):
        if self._fallback_widget and hasattr(self._fallback_widget, "_collection_service"):
            return self._fallback_widget._collection_service
        return self._coll_svc

    @_collection_service.setter
    def _collection_service(self, svc):
        self._coll_svc = svc
        if self._fallback_widget:
            self._fallback_widget._collection_service = svc
            if hasattr(self._fallback_widget, "painter") and hasattr(svc, "equipped"):
                try:
                    self._fallback_widget.painter.set_character(svc.equipped())
                except Exception:
                    pass
            if hasattr(svc, "on_equip_changed"):
                try:
                    svc.on_equip_changed(self.set_character)
                except Exception:
                    pass

    def set_collection_service(self, svc):
        """Set collection service and synchronize equipped skin."""
        self._collection_service = svc

    @property
    def model(self):
        if self._fallback_widget:
            return self._fallback_widget.model
        # Mock minimal model for compatibility
        class _ModelMock:
            def __init__(self, settings):
                self.settings = settings
                self.is_sleeping = False
                self.voice_state = VoiceState.READY
                self.cling_edge = None
            def load_saved_position(self):
                pos = self.settings.value("position", None)
                return pos if isinstance(pos, QPoint) else None
        return _ModelMock(self._settings)

    def set_voice_state(self, state: VoiceState):
        self._current_state = state
        if self._fallback_widget:
            self._fallback_widget.set_voice_state(state)
        elif self._is_native:
            self._send_cmd({"cmd": "set_voice_state", "state": state.value})

    def wake_up(self):
        if self._fallback_widget:
            self._fallback_widget.wake_up()
        elif self._is_native:
            self._send_cmd({"cmd": "wake_up"})

    def set_character(self, char_def):
        self._current_char = char_def
        if self._fallback_widget:
            self._fallback_widget.set_character(char_def)
        elif self._is_native and char_def:
            self._send_cmd({
                "cmd": "set_character",
                "id": char_def.id,
                "name": char_def.name,
                "kind": char_def.kind,
                "skin_dir": char_def.skin_dir or "",
                "rarity": char_def.rarity,
            })

    def set_music_mode(self, enabled: bool = True):
        if self._fallback_widget:
            self._fallback_widget.set_music_mode(enabled)
        elif self._is_native:
            self._send_cmd({"cmd": "set_music", "playing": enabled})

    def show(self):
        self._is_visible = True
        if self._fallback_widget:
            self._fallback_widget.show()
        elif self._is_native:
            self._send_cmd({"cmd": "set_visible", "visible": True})

    def hide(self):
        self._is_visible = False
        if self._fallback_widget:
            self._fallback_widget.hide()
        elif self._is_native:
            self._send_cmd({"cmd": "set_visible", "visible": False})

    def setVisible(self, visible: bool):
        if visible:
            self.show()
        else:
            self.hide()

    def set_visible(self, visible: bool):
        self.setVisible(visible)

    def close(self):
        self._is_visible = False
        if self._fallback_widget:
            self._fallback_widget.close()
        elif self._is_native:
            self._send_cmd({"cmd": "quit"})
            if self._native_process:
                try:
                    self._native_process.terminate()
                except Exception:
                    pass

    def raise_(self):
        if self._fallback_widget:
            self._fallback_widget.raise_()
        elif self._is_native:
            self._send_cmd({"cmd": "raise"})

    def move(self, *args):
        if len(args) == 1 and isinstance(args[0], QPoint):
            self._pos = args[0]
        elif len(args) == 2:
            self._pos = QPoint(int(args[0]), int(args[1]))
        if self._fallback_widget:
            self._fallback_widget.move(*args)
        elif self._is_native:
            self._send_cmd({"cmd": "move", "x": self._pos.x(), "y": self._pos.y()})

    def isVisible(self) -> bool:
        if self._fallback_widget:
            return self._fallback_widget.isVisible()
        return self._is_visible

    def reload_settings(self):
        if self._fallback_widget:
            self._fallback_widget.reload_settings()
        elif self._is_native:
            self._send_cmd({"cmd": "reload_settings"})

    def play_character_sfx(self, char_id=None, action="talk"):
        if self._fallback_widget:
            self._fallback_widget.play_character_sfx(char_id, action)

    def open_collection_dialog(self):
        if self._fallback_widget:
            self._fallback_widget.open_collection_dialog()
        else:
            user_key = getattr(self._coll_svc, 'user_key', None) if self._coll_svc else None
            try:
                from view.ui.collection.collection_dialog import CollectionDialog
                dlg = CollectionDialog(user_key=user_key, parent=self.parent())
                dlg.exec()
            except Exception as e:
                print(f"[MascotIPC] Open collection dialog error: {e}")

