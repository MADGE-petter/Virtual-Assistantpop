import os
import subprocess
import sys


def build():
    print("Starting PyInstaller build process...")
    
    # Define entry point and output name
    entry_point = "login.py"
    app_name = "PopAssistant"
    
    # Base command options
    cmd = [
        "pyinstaller",
        "--onedir",
        "--paths=.",
        "--windowed",
        f"--name={app_name}",
        "--clean",
        "--noconfirm",
    ]
    
    # Add hidden imports
    hidden_imports = [
        "PyQt6.QtCore", "PyQt6.QtWidgets", "PyQt6.QtGui", "PyQt6.sip",
        "comtypes", "pycaw", "wmi", "psutil", "speech_recognition",
        "gtts", "playsound", "pynvml", "nvidia_ml_py", "screen_brightness_control"
    ]
    for h in hidden_imports:
        cmd.append(f"--hidden-import={h}")

    # Add collect all for complex native packages
    collect_all = ["vosk", "ctranslate2"]
    for c in collect_all:
        cmd.append(f"--collect-all={c}")
    
    # Add icon if available
    icon_path = os.path.join("assets", "icon.ico")
    if os.path.exists(icon_path):
        cmd.append(f"--icon={icon_path}")
        print(f"Using application icon: {icon_path}")
    else:
        print("Warning: icon.ico not found in assets/")

    # Add data files (format: src;dest)
    datas = [
        ("assets", "assets"),
        ("tools", "tools"),
        (os.path.join("database", "conversations.db"), "database"),
    ]
    
    for src, dest in datas:
        if os.path.exists(src):
            cmd.append(f"--add-data={src};{dest}")
            print(f"Bundling data: {src} -> {dest}")
        else:
            print(f"Warning: Data source path not found: {src}")
            
    # Add entry point
    cmd.append(entry_point)
    
    # Run PyInstaller
    print(f"Running command: {' '.join(cmd)}")
    try:
        subprocess.check_call(cmd)
        print("\nBuild completed successfully!")
        print(f"Application is located at: {os.path.abspath(os.path.join('dist', app_name))}")
    except subprocess.CalledProcessError as e:
        print(f"\nError: PyInstaller exited with code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
