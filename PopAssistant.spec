# -*- mode: python ; coding: utf-8 -*-
import os
from PyInstaller.utils.hooks import collect_all

datas = [
    ('assets', 'assets'),
    ('tools', 'tools'),
]

if os.path.exists('voice-models'):
    datas.append(('voice-models', 'voice-models'))

db_path = os.path.join('database', 'conversations.db')
if os.path.exists(db_path):
    datas.append((db_path, 'database'))

# Collect dynamic data, binaries, and hidden imports for AI/Audio packages
sherpa_datas, sherpa_binaries, sherpa_hidden = collect_all('sherpa_onnx')
oww_datas, oww_binaries, oww_hidden = collect_all('openwakeword')

datas += sherpa_datas + oww_datas
binaries = sherpa_binaries + oww_binaries

hiddenimports = [
    'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.sip',
    'comtypes', 'pycaw', 'wmi', 'psutil', 'speech_recognition',
    'gtts', 'playsound', 'pynvml', 'nvidia_ml_py', 'screen_brightness_control',
    'sqlite3', 'sounddevice', 'soundfile', 'librosa', 'pyaudio', 'requests',
    'numpy', 'huggingface_hub', 'encodings'
] + sherpa_hidden + oww_hidden

a = Analysis(
    ['login.py'],
    pathex=['.'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc', 'pdb', 'difflib'],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

icon_file = 'assets/icon.ico' if os.path.exists('assets/icon.ico') else None

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='PopAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='PopAssistant',
)
