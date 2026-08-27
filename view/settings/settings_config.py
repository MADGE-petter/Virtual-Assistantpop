import os
import json
import urllib.request
import urllib.parse
from PyQt6.QtCore import pyqtSignal, QThread

SETTINGS_FILE = os.path.join(os.getcwd(), "database", "user_settings.json")


def load_user_settings() -> dict:
    default_settings = {
        "model_dir": os.path.join(os.getcwd(), "LLM-agents"),
        "system_rule": "Bạn là POP AI - Trợ lý thông minh. Hãy trả lời ngắn gọn, chính xác và lịch sự bằng tiếng Việt.",
        "autostart": False,
        "mascot_top": True,
        "tts_enabled": True
    }
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                default_settings.update(data)
        except Exception:
            pass
    return default_settings


def save_user_settings(settings: dict):
    os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving user settings: {e}")


class HFSearchThread(QThread):
    """Thread tìm kiếm model GGUF trên Hugging Face API."""
    resultsFound = pyqtSignal(list)
    suggestionsFound = pyqtSignal(list)
    searchError = pyqtSignal(str)

    def __init__(self, query: str, is_suggest: bool = False, parent=None):
        super().__init__(parent)
        self.query = query
        self.is_suggest = is_suggest

    def run(self):
        try:
            url = f"https://huggingface.co/api/models?search={urllib.parse.quote(self.query)}&filter=gguf&limit=20"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [
                    {
                        "id": item.get('id', ''),
                        "author": item.get('author', item.get('id', '').split('/')[0] if '/' in item.get('id', '') else 'Community'),
                        "name": item.get('id', '').split('/')[-1] if '/' in item.get('id', '') else item.get('id', ''),
                    }
                    for item in data if item.get('id')
                ]
                if self.is_suggest:
                    suggestions = [m["id"] for m in models]
                    self.suggestionsFound.emit(suggestions)
                else:
                    self.resultsFound.emit(models)
        except Exception as e:
            if not self.is_suggest:
                self.searchError.emit(str(e))
