"""Background Music Detector for Desktop Mascot.

Accurately detects when real music / YouTube audio is playing on Windows:
- Filters specifically for Media & Browser applications (Chrome, Edge, Firefox, Spotify, VLC, etc.).
- Strictly blacklists Communication apps (Teams, Discord, Zalo, Telegram, Zoom, Skype) and System sounds.
- Strictly blacklists Python (preventing the assistant's own TTS voice from triggering music mode).
- Sustained audio buffer requirement (>= 1.5s of continuous audio) so short pings, clicks, or ad snippets
  never cause false triggers.
- Automatic silence timeout (~1.8s of silence) to return mascot to idle when music is paused.
"""

import sys
import threading
import time
import warnings
from typing import Optional, Set


class MusicDetector:
    """Thread-safe background detector for active music/YouTube media streams."""

    _instance: Optional["MusicDetector"] = None

    BLACKLIST_APPS: Set[str] = {
        "ms-teams.exe", "teams.exe", "discord.exe", "zalo.exe", "telegram.exe",
        "zoom.exe", "slack.exe", "skype.exe", "viber.exe", "explorer.exe",
        "system", "audiodg.exe", "python.exe", "pythonw.exe", "virtual-assistantpop.exe"
    }

    KNOWN_MEDIA_APPS: Set[str] = {
        "spotify.exe", "chrome.exe", "msedge.exe", "firefox.exe", "opera.exe",
        "brave.exe", "vivaldi.exe", "vlc.exe", "wmplayer.exe", "foobar2000.exe",
        "musicbee.exe", "aimp.exe", "itunes.exe", "apple-music.exe", "tidal.exe",
        "coccoc.exe", "kmplayer.exe", "potplayer64.exe", "potplayermini64.exe"
    }

    def __init__(self):
        self._is_playing: bool = False
        self._active_source: Optional[str] = None
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()

    @classmethod
    def instance(cls) -> "MusicDetector":
        if cls._instance is None:
            cls._instance = MusicDetector()
        return cls._instance

    @property
    def is_playing(self) -> bool:
        with self._lock:
            return self._is_playing

    @property
    def active_source(self) -> Optional[str]:
        with self._lock:
            return self._active_source

    def start(self):
        """Starts the background media audio polling thread."""
        if self._running or sys.platform != "win32":
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, name="MascotMusicDetector", daemon=True)
        self._thread.start()

    def stop(self):
        """Stops the background detector thread."""
        self._running = False

    def _worker_loop(self):
        try:
            import comtypes
            comtypes.CoInitialize()
        except Exception:
            pass

        try:
            from pycaw.pycaw import AudioUtilities, IAudioMeterInformation
        except Exception:
            return

        consecutive_active = 0
        consecutive_silent = 0

        while self._running:
            time.sleep(0.30)  # Check 3 times per second (virtually 0% CPU)
            try:
                max_peak = 0.0
                detected_proc = None

                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    sessions = AudioUtilities.GetAllSessions()
                    for s in sessions:
                        if not s.Process:
                            continue
                        pname = s.Process.name().lower()
                        if pname in self.BLACKLIST_APPS:
                            continue

                        # Target media apps or processes with 'player'/'music' in name
                        is_target = (
                            pname in self.KNOWN_MEDIA_APPS
                            or "music" in pname
                            or "player" in pname
                            or "audio" in pname
                        )
                        if not is_target:
                            continue

                        try:
                            meter = s._ctl.QueryInterface(IAudioMeterInformation)
                            peak = float(meter.GetPeakValue())
                            if peak > max_peak:
                                max_peak = peak
                                detected_proc = pname
                        except Exception:
                            pass

                # Peak threshold: real music produces solid volume (>= 0.025 / 2.5% volume)
                if max_peak >= 0.025:
                    consecutive_active += 1
                    consecutive_silent = 0
                    # Sustained energy for >= 1.5 seconds (5 ticks * 0.3s) confirms real music, not a ping!
                    if consecutive_active >= 5:
                        with self._lock:
                            self._is_playing = True
                            self._active_source = detected_proc
                else:
                    consecutive_silent += 1
                    consecutive_active = max(0, consecutive_active - 1)
                    # When music is paused or ends (silence for >= 1.8 seconds), turn off music mode
                    if consecutive_silent >= 6:
                        with self._lock:
                            self._is_playing = False
                            self._active_source = None

            except Exception:
                pass

        try:
            import comtypes
            comtypes.CoUninitialize()
        except Exception:
            pass

