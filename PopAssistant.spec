# -*- mode: python ; coding: utf-8 -*-
import os
import sys
from PyInstaller.utils.hooks import collect_all, copy_metadata

# 1. Base datas
datas = [
    ('assets', 'assets'),
    ('tools', 'tools'),
]

# Database template
db_path = os.path.join('database', 'conversations.db')
if os.path.exists(db_path):
    datas.append((db_path, 'database'))

# Filtered collection for voice-models (exclude .git, __pycache__, .ipynb to keep size clean)
if os.path.exists('voice-models'):
    for root, dirs, files in os.walk('voice-models'):
        dirs[:] = [d for d in dirs if d not in ('.git', '.github', '__pycache__')]
        for f in files:
            if f.endswith(('.ipynb', '.gitignore', '.gitattributes', '.DS_Store', '.pyc')):
                continue
            src = os.path.join(root, f)
            rel = os.path.relpath(root, '.')
            datas.append((src, rel))

# 2. Collect dynamic packages: sherpa_onnx, openwakeword, underthesea, llama_cpp
binaries = []
hiddenimports = [
    'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.sip',
    'comtypes', 'pycaw', 'wmi', 'psutil', 'speech_recognition',
    'gtts', 'playsound', 'pynvml', 'nvidia_ml_py', 'screen_brightness_control',
    'sqlite3', 'sounddevice', 'soundfile', 'librosa', 'pyaudio', 'requests',
    'numpy', 'huggingface_hub', 'encodings',
    'torch', 'torchaudio', 'transformers', 'numba', 'scipy',
    'pyautogui', 'pytweening', 'mouseinfo', 'pygetwindow', 'pyscreeze',
    'tools', 'tools.file_search_tool', 'tools.web_tool', 'tools.zalo_tool', 'tools.facebook_tool',
    'controller', 'controller.login_controller', 'controller.pop_controller', 'controller.voice_mode_coordinator',
    'view', 'view.ui', 'view.ui.styles', 'view.ui.pop_view', 'view.ui.login_view',
    'service', 'service.login_service', 'service.conversation_service', 'service.AudioService', 'service.voice_service', 'service.llm_service',
    'database', 'database.conversation_db',
    'melo', 'melo.api', 'melo.utils', 'melo.commons', 'melo.models', 'melo.modules',
    'melo.mel_processing', 'melo.split_utils', 'melo.download_utils', 'melo.text',
    'melo.text.vietnamese', 'melo.text.vietnamese_bert', 'melo.text.cleaner',
    'melo.text.symbols', 'melo.text.tone_sandhi',
]

for pkg in ['sherpa_onnx', 'openwakeword', 'underthesea', 'llama_cpp']:
    try:
        pkg_datas, pkg_binaries, pkg_hidden = collect_all(pkg)
        datas += pkg_datas
        binaries += pkg_binaries
        hiddenimports += pkg_hidden
    except Exception as e:
        print(f"[Spec] Note: collect_all for {pkg} returned: {e}")

# Copy metadata needed for HuggingFace / Transformers / Torch
for meta_pkg in ['transformers', 'huggingface_hub', 'tokenizers', 'safetensors', 'tqdm', 'regex', 'requests', 'torch']:
    try:
        datas += copy_metadata(meta_pkg)
    except Exception:
        pass

a = Analysis(
    ['login.py'],
    pathex=['.', 'voice-models/melotts'],
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
    a.binaries,
    a.datas,
    [],
    name='PopAssistant',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)
