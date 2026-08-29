import os
import json
import time
import urllib.request
import urllib.parse
from PyQt6.QtCore import QThread, pyqtSignal

CONFIG_PATH = os.path.join(os.getcwd(), "user_settings.json")

DEFAULT_SETTINGS = {
    "language": "vi",
    "theme": "dark",
    "auto_launch": False,
    "model_dir": os.path.join(os.getcwd(), "LLM-agents"),
    "max_tokens": 2048,
    "temperature": 0.7,
    "context_rules": "Bạn là POP AI Assistant, trợ lý thông minh thân thiện bằng tiếng Việt."
}


def load_user_settings() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except Exception:
            pass
    return DEFAULT_SETTINGS.copy()


def save_user_settings(settings: dict):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"[Settings] Error saving settings: {e}")


class HFSearchThread(QThread):
    """Luồng tìm kiếm và gợi ý model từ Hugging Face Hub API."""
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
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                models = [
                    {
                        "id": item.get('id', ''),
                        "author": item.get('author', item.get('id', '').split('/')[0] if '/' in item.get('id', '') else 'Community'),
                        "name": item.get('id', '').split('/')[-1] if '/' in item.get('id', '') else item.get('id', ''),
                        "downloads": item.get('downloads', 0),
                        "tags": item.get('pipeline_tag', 'Language Model')
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


class HFModelDownloadThread(QThread):
    """Luồng tải file GGUF thực tế từ Hugging Face qua luồng stream HTTP kèm tiến độ chính xác."""
    progressChanged = pyqtSignal(int, float, float, float)  # percent, downloaded_mb, total_mb, speed_mb_s
    statusUpdated = pyqtSignal(str)
    downloadFinished = pyqtSignal(str)
    downloadError = pyqtSignal(str)

    def __init__(self, repo_id: str, target_dir: str, preferred_file: str = None, parent=None):
        super().__init__(parent)
        self.repo_id = repo_id
        self.target_dir = target_dir
        self.preferred_file = preferred_file
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            self.statusUpdated.emit("Đang phân tích danh sách file GGUF trong repository...")
            os.makedirs(self.target_dir, exist_ok=True)

            # 1. Tìm các file .gguf trong repo Hugging Face
            api_url = f"https://huggingface.co/api/models/{self.repo_id}/tree/main"
            req = urllib.request.Request(api_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                tree_data = json.loads(resp.read().decode('utf-8'))

            gguf_files = [f['path'] for f in tree_data if isinstance(f, dict) and f.get('path', '').endswith('.gguf')]
            
            if not gguf_files:
                raise Exception(f"Không tìm thấy file .gguf nào trong repository '{self.repo_id}'.")

            # Chọn file GGUF tốt nhất (Ưu tiên Q4_K_M hoặc file được chọn)
            chosen_file = None
            if self.preferred_file and self.preferred_file in gguf_files:
                chosen_file = self.preferred_file
            else:
                for f in gguf_files:
                    if "q4_k_m" in f.lower() or "q4_0" in f.lower():
                        chosen_file = f
                        break
                if not chosen_file:
                    chosen_file = gguf_files[0]

            self.statusUpdated.emit(f"Bắt đầu tải file: {chosen_file}...")

            # 2. Tạo đường dẫn tải thực tế từ Hugging Face Resolve
            download_url = f"https://huggingface.co/{self.repo_id}/resolve/main/{chosen_file}"
            target_path = os.path.join(self.target_dir, os.path.basename(chosen_file))
            temp_path = target_path + ".downloading"

            # 3. Stream download với chunk 1MB và tính toán tốc độ
            req = urllib.request.Request(download_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=30) as resp:
                total_size = int(resp.headers.get('content-length', 0))
                total_mb = total_size / (1024 * 1024) if total_size > 0 else 0.0
                downloaded = 0
                start_time = time.time()
                last_update_time = start_time
                last_downloaded = 0

                with open(temp_path, "wb") as f_out:
                    while True:
                        if self._is_cancelled:
                            f_out.close()
                            if os.path.exists(temp_path):
                                os.remove(temp_path)
                            self.downloadError.emit("Đã hủy quá trình tải model.")
                            return

                        chunk = resp.read(1024 * 1024)  # 1MB per chunk
                        if not chunk:
                            break

                        f_out.write(chunk)
                        downloaded += len(chunk)

                        now = time.time()
                        if now - last_update_time >= 0.5:
                            duration = now - last_update_time
                            speed_mb_s = ((downloaded - last_downloaded) / (1024 * 1024)) / duration if duration > 0 else 0.0
                            percent = int((downloaded / total_size) * 100) if total_size > 0 else 0
                            downloaded_mb = downloaded / (1024 * 1024)
                            self.progressChanged.emit(percent, downloaded_mb, total_mb, speed_mb_s)
                            last_update_time = now
                            last_downloaded = downloaded

            # Hoàn tất: đổi tên file tạm sang file chính thức
            if os.path.exists(target_path):
                os.remove(target_path)
            os.rename(temp_path, target_path)

            self.downloadFinished.emit(target_path)

        except Exception as e:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception:
                    pass
            self.downloadError.emit(f"Lỗi tải model: {str(e)}")
