import os
import shutil
import subprocess
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


def build():
    print("=" * 60)
    print("  Pop Assistant - PyInstaller Build Script")
    print("=" * 60)

    # 1. Ensure icon.ico exists
    icon_path = os.path.join("assets", "icon.ico")
    if not os.path.exists(icon_path):
        png_path = os.path.join("assets", "POP.png")
        if os.path.exists(png_path):
            try:
                from PIL import Image
                img = Image.open(png_path)
                img.save(icon_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
                print(f"[Build] Generated icon.ico from {png_path}")
            except Exception as e:
                print(f"[Build] Warning: Could not generate icon.ico: {e}")

    # 2. Command to build using PopAssistant.spec
    spec_file = "PopAssistant.spec"
    if not os.path.exists(spec_file):
        print(f"Error: {spec_file} not found!")
        sys.exit(1)

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        spec_file,
        "--noconfirm",
    ]

    print(f"[Build] Running command: {' '.join(cmd)}")
    print("[Build] Packaging standalone application...\n")

    try:
        subprocess.check_call(cmd)
        dist_dir = os.path.abspath(os.path.join("dist", "PopAssistant"))
        exe_path = os.path.join(dist_dir, "PopAssistant.exe")

        # Sync voice-models directly next to PopAssistant.exe
        if os.path.exists("voice-models"):
            dest_models = os.path.join(dist_dir, "voice-models")
            shutil.copytree("voice-models", dest_models, dirs_exist_ok=True)
            print(f"[Build] Synced voice-models into {dest_models}")

        print("\n" + "=" * 60)
        print("  BUILD HOAN TAT!")
        print("=" * 60)
        print(f"Thu muc ung dung: {dist_dir}")
        print(f"File chay:        {exe_path}")
        print("\nBan chi can nen thu muc 'PopAssistant' trong 'dist' thanh file .zip de mang sang may khac su dung ngay!")
    except subprocess.CalledProcessError as e:
        print(f"\n[Build Error] PyInstaller exited with code {e.returncode}")
        sys.exit(e.returncode)


if __name__ == "__main__":
    build()
