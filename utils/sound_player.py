"""Safe audio player utility for UI sounds and voice previews.
Prevents PortAudio / sounddevice crashes when PyAudio is concurrently running on Windows.
"""

import os
import sys
import threading


def play_wav_safely(wav_path: str):
    """Plays a WAV file asynchronously and safely without crashing the application."""
    if not wav_path or not os.path.isfile(wav_path):
        return

    abs_path = os.path.abspath(wav_path)

    # 1. On Windows, winsound is native, crash-proof, and non-blocking
    if sys.platform == "win32":
        try:
            import winsound
            winsound.PlaySound(abs_path, winsound.SND_FILENAME | winsound.SND_ASYNC)
            return
        except Exception:
            pass

    # 2. Asynchronous fallback using playsound / soundfile
    def _worker():
        try:
            import soundfile as sf
            import sounddevice as sd
            data, sr = sf.read(abs_path)
            sd.play(data, sr)
            sd.wait()
        except Exception:
            try:
                import playsound
                playsound.playsound(abs_path, block=True)
            except Exception:
                pass

    threading.Thread(target=_worker, daemon=True).start()

