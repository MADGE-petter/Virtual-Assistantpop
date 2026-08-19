import os
import sys


def resource_path(*parts: str) -> str:
    """Return an absolute path to a resource bundled with the app.

    Uses PyInstaller's _MEIPASS when available; otherwise resolves
    relative to the repository root.
    """
    # If running from a PyInstaller bundle
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        # repo root is parent of this utils package
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    return os.path.join(base, *parts)


def get_writeable_path(*parts: str) -> str:
    """Return an absolute path to a writeable, persistent file or directory.

    When running from a PyInstaller bundle, uses the user's Local AppData folder.
    Otherwise, resolves relative to the repository root.
    """
    if getattr(sys, 'frozen', False):
        appdata = os.environ.get('LOCALAPPDATA') or os.environ.get('APPDATA') or os.path.expanduser('~')
        base = os.path.join(appdata, 'PopAssistant')
    else:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    path = os.path.join(base, *parts)
    # Ensure directory containing the target file exists
    os.makedirs(os.path.dirname(path), exist_ok=True)
    return path


def get_database_path(filename: str = "conversations.db") -> str:
    """Return the path to the application's database file.

    Saves to persistent AppData when compiled, repository database directory during dev.
    If running compiled and the file doesn't exist in AppData, copies it from the bundle.
    """
    write_path = get_writeable_path("database", filename)
    
    if getattr(sys, 'frozen', False):
        if not os.path.exists(write_path):
            import shutil
            bundle_path = resource_path("database", filename)
            if os.path.exists(bundle_path):
                try:
                    os.makedirs(os.path.dirname(write_path), exist_ok=True)
                    shutil.copy2(bundle_path, write_path)
                    print(f"[Paths] Copied default database template to {write_path}")
                except Exception as e:
                    print(f"[Paths] Error copying database template: {e}")
                    
    return write_path

