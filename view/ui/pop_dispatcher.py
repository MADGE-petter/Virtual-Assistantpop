"""
POP UI Dispatcher - Thread-safe cross-thread signal routing for PopView.
Handles thread synchronization between background threads and the main Qt UI thread.
"""

from PyQt6.QtCore import QObject, pyqtSignal


class PopDispatcher(QObject):
    """Encapsulates cross-thread Qt signals for thread-safe UI updates."""

    botTextSignal = pyqtSignal(str)
    userTextSignal = pyqtSignal(str)
    voiceStateSignal = pyqtSignal(object)
    toastSignal = pyqtSignal(str, str)
    alertSignal = pyqtSignal(dict)
    showWindowSignal = pyqtSignal()
    hideWindowSignal = pyqtSignal()
    confirmationCardSignal = pyqtSignal(str, str, str, dict)
    filePreviewSignal = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
