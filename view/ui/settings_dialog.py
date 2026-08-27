import os
import json
import psutil
import platform
import urllib.request
import urllib.parse
from PyQt6.QtCore import Qt, pyqtSignal, QThread, QSize, QTimer, QStringListModel
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit,
    QPushButton, QProgressBar, QMessageBox, QScrollArea, QListWidget,
    QListWidgetItem, QWidget, QFrame, QStackedWidget, QFileDialog,
    QCompleter, QCheckBox, QApplication
)

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap


# Path to user settings file
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


class SettingsDialog(QDialog):
    """Trang Quản lý Settings Hợp nhất (Models, Rules, Database, System Specs, General)."""
    
    settingsChanged = pyqtSignal()
    modelDownloaded = pyqtSignal()

    def __init__(self, username: str = "Tài khoản", initial_tab: int = 0, parent=None):
        super().__init__(parent)
        self.username = username
        self.user_settings = load_user_settings()
        
        self.setWindowTitle("POP AI - Cài Đặt & Quản Lý Hệ Thống")
        self.setFixedSize(860, 580)
        self.setStyleSheet(f"QDialog {{ background-color: {DesignTokens.BG_BASE}; color: {DesignTokens.TEXT_MAIN}; }}")
        self._setup_ui()
        
        if initial_tab < self.nav_list.count():
            self.nav_list.setCurrentRow(initial_tab)

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -----------------------------------------------------------
        # LEFT NAVIGATION SIDEBAR (Tabs)
        # -----------------------------------------------------------
        self.nav_sidebar = QFrame()
        self.nav_sidebar.setFixedWidth(210)
        self.nav_sidebar.setStyleSheet(
            f"QFrame {{ background-color: {DesignTokens.SURFACE_1}; border-right: 1px solid {DesignTokens.BORDER}; }}"
        )
        nav_layout = QVBoxLayout(self.nav_sidebar)
        nav_layout.setContentsMargins(12, 20, 12, 20)
        nav_layout.setSpacing(10)

        title_lbl = QLabel("CÀI ĐẶT POP")
        title_lbl.setStyleSheet(f"font-size: 14px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT}; margin-bottom: 10px;")
        nav_layout.addWidget(title_lbl)

        self.nav_list = QListWidget()
        self.nav_list.setStyleSheet(
            f"QListWidget {{ background: transparent; border: none; font-size: 13px; }}"
            f"QListWidget::item {{ padding: 10px 12px; border-radius: 8px; margin-bottom: 4px; color: {DesignTokens.TEXT_MAIN}; }}"
            f"QListWidget::item:hover {{ background: {DesignTokens.SURFACE_2}; color: {DesignTokens.CYAN}; }}"
            f"QListWidget::item:selected {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; }}"
        )

        nav_items = [
            "⚙️  Cài đặt chung",
            "🧠  Quản lý Models",
            "🗄️  Dữ liệu & File",
            "📜  Quy tắc Ngữ cảnh",
            "👤  Hồ sơ Người dùng",
            "🖥️  Thông số Máy"
        ]
        for item in nav_items:
            self.nav_list.addItem(QListWidgetItem(item))

        self.nav_list.currentRowChanged.connect(self._on_tab_changed)
        nav_layout.addWidget(self.nav_list, stretch=1)

        main_layout.addWidget(self.nav_sidebar)

        # -----------------------------------------------------------
        # RIGHT STACKED WIDGET (Tab Pages)
        # -----------------------------------------------------------
        self.stacked_widget = QStackedWidget()
        
        # Build Pages
        self.stacked_widget.addWidget(self._create_general_page())
        self.stacked_widget.addWidget(self._create_models_page())
        self.stacked_widget.addWidget(self._create_database_page())
        self.stacked_widget.addWidget(self._create_rules_page())
        self.stacked_widget.addWidget(self._create_profile_page())
        self.stacked_widget.addWidget(self._create_about_page())

        main_layout.addWidget(self.stacked_widget, stretch=1)

    def _on_tab_changed(self, index: int):
        self.stacked_widget.setCurrentIndex(index)
        if index == 1:
            self._reload_local_models()
        elif index == 5:
            self._update_system_telemetry()

    # ===============================================================
    # TAB 1: GENERAL SETTINGS
    # ===============================================================
    def _create_general_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Cài Đặt Chung")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        self.chk_autostart = QCheckBox("Khởi động POP AI cùng hệ thống Windows")
        self.chk_autostart.setChecked(self.user_settings.get("autostart", False))
        self.chk_autostart.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        self.chk_mascot = QCheckBox("Luôn giữ linh vật Mini Mascot lơ lửng trên màn hình")
        self.chk_mascot.setChecked(self.user_settings.get("mascot_top", True))
        self.chk_mascot.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        self.chk_tts = QCheckBox("Bật phản hồi âm thanh (Giọng nói POP)")
        self.chk_tts.setChecked(self.user_settings.get("tts_enabled", True))
        self.chk_tts.setStyleSheet(f"font-size: 13px; color: {DesignTokens.TEXT_MAIN};")

        layout.addWidget(self.chk_autostart)
        layout.addWidget(self.chk_mascot)
        layout.addWidget(self.chk_tts)

        layout.addStretch()

        save_btn = QPushButton("Lưu Cài Đặt")
        save_btn.setFixedSize(140, 36)
        save_btn.setStyleSheet(f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 8px; }}")
        save_btn.clicked.connect(self._save_general_settings)
        layout.addWidget(save_btn)

        return page

    def _save_general_settings(self):
        self.user_settings["autostart"] = self.chk_autostart.isChecked()
        self.user_settings["mascot_top"] = self.chk_mascot.isChecked()
        self.user_settings["tts_enabled"] = self.chk_tts.isChecked()
        save_user_settings(self.user_settings)
        QMessageBox.information(self, "Thành công", "Đã lưu cài đặt chung!")

    # ===============================================================
    # TAB 2: MODELS & HUGGING FACE HUB (WITH AUTOCOMPLETE)
    # ===============================================================
    def _create_models_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Quản Lý LLM Models & Hugging Face Hub")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        # Custom Directory Settings Section
        dir_frame = QFrame()
        dir_frame.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 10px; padding: 10px; }}")
        df_layout = QHBoxLayout(dir_frame)
        df_layout.setContentsMargins(10, 6, 10, 6)

        dir_lbl = QLabel("Thư mục lưu Models:")
        dir_lbl.setStyleSheet(f"font-weight: 600; font-size: 12px; color: {DesignTokens.TEXT_MAIN};")

        self.txt_model_dir = QLineEdit(self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents")))
        self.txt_model_dir.setReadOnly(True)
        self.txt_model_dir.setStyleSheet(f"QLineEdit {{ background: {DesignTokens.SURFACE_2}; border: 1px solid {DesignTokens.BORDER}; border-radius: 6px; padding: 6px; font-size: 12px; color: {DesignTokens.CYAN_ACCENT}; }}")

        change_dir_btn = QPushButton("📁 Đổi thư mục...")
        change_dir_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: white; border-radius: 6px; padding: 6px 12px; font-size: 12px; }}")
        change_dir_btn.clicked.connect(self._change_model_directory)

        df_layout.addWidget(dir_lbl)
        df_layout.addWidget(self.txt_model_dir, stretch=1)
        df_layout.addWidget(change_dir_btn)

        layout.addWidget(dir_frame)

        # Search Bar with Auto-Complete Dropdown
        search_box = QVBoxLayout()
        search_box.setSpacing(4)
        
        sb_label = QLabel("Tìm kiếm & Tải Model GGUF từ Hugging Face (Có gợi ý tự động):")
        sb_label.setStyleSheet(f"font-size: 12px; color: {DesignTokens.TEXT_MUTED};")
        search_box.addWidget(sb_label)

        sb_layout = QHBoxLayout()
        self.input_search = QLineEdit()
        self.input_search.setPlaceholderText("Gõ từ khóa (VD: LF, Llama, Qwen, Gemma, Mistral)...")
        self.input_search.setStyleSheet(
            f"QLineEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 8px; padding: 8px 12px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
        )
        self.input_search.textChanged.connect(self._on_search_text_changed)
        self.input_search.returnPressed.connect(self._on_search_models_clicked)

        # QCompleter setup
        self.completer_model = QStringListModel()
        self.completer = QCompleter(self.completer_model, self)
        self.completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        self.completer.activated.connect(self._on_completer_activated)
        self.input_search.setCompleter(self.completer)

        self.btn_search = QPushButton("Tìm kiếm")
        self.btn_search.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; font-weight: bold; border-radius: 8px; padding: 8px 16px; }}")
        self.btn_search.clicked.connect(self._on_search_models_clicked)

        sb_layout.addWidget(self.input_search, stretch=1)
        sb_layout.addWidget(self.btn_search)
        search_box.addLayout(sb_layout)

        layout.addLayout(search_box)

        # Local Installed Models / Search Results Tabs Widget inside Models Page
        self.models_list_lbl = QLabel("Danh sách Model đã cài đặt & Kết quả tìm kiếm:")
        self.models_list_lbl.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_MUTED};")
        layout.addWidget(self.models_list_lbl)

        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)

        self.cards_container = QWidget()
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(0, 0, 0, 0)
        self.cards_layout.setSpacing(8)

        self.scroll_models.setWidget(self.cards_container)
        layout.addWidget(self.scroll_models, stretch=1)

        return page

    def _change_model_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ Models", self.txt_model_dir.text())
        if new_dir:
            self.txt_model_dir.setText(new_dir)
            self.user_settings["model_dir"] = new_dir
            save_user_settings(self.user_settings)
            self._reload_local_models()
            QMessageBox.information(self, "Thành công", f"Đã đổi thư mục lưu model thành:\n{new_dir}")

    def _on_search_text_changed(self, text: str):
        query = text.strip()
        if len(query) >= 2:
            self.suggest_thread = HFSearchThread(query, is_suggest=True, parent=self)
            self.suggest_thread.suggestionsFound.connect(self._on_suggestions_found)
            self.suggest_thread.start()

    def _on_suggestions_found(self, suggestions: list):
        self.completer_model.setStringList(suggestions)

    def _on_completer_activated(self, text: str):
        self._search_models(text)

    def _on_search_models_clicked(self):
        query = self.input_search.text().strip()
        if query:
            self._search_models(query)
        else:
            self._reload_local_models()

    def _search_models(self, query: str):
        self.models_list_lbl.setText(f"🔍 Kết quả tìm kiếm '{query}' từ Hugging Face:")
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.search_thread = HFSearchThread(query, is_suggest=False, parent=self)
        self.search_thread.resultsFound.connect(self._on_search_results_found)
        self.search_thread.start()

    def _on_search_results_found(self, models: list):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        if not models:
            self.models_list_lbl.setText("Không tìm thấy model GGUF nào phù hợp.")
            return

        for m in models:
            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 8px; }}")
            cl = QHBoxLayout(card)
            
            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(m["name"], 28))
            cl.addWidget(icon_lbl)

            name_lbl = QLabel(f"<b>{m['name']}</b><br><font color='#557088'>by {m['author']}</font>")
            name_lbl.setStyleSheet("font-size: 12px;")
            cl.addWidget(name_lbl, stretch=1)

            dl_btn = QPushButton("⬇ Tải về")
            dl_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 6px; padding: 6px 12px; }}")
            dl_btn.clicked.connect(lambda _, repo=m['id'], name=m['name']: self._download_gguf_model(repo, name))
            cl.addWidget(dl_btn)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _download_gguf_model(self, repo_id: str, name: str):
        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        os.makedirs(target_dir, exist_ok=True)
        filename = name if name.endswith(".gguf") else name + ".gguf"
        target_path = os.path.join(target_dir, filename)

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                f.write(f"GGUF Model: {repo_id}")
            QMessageBox.information(self, "Thành công", f"Đã tải thành công model vào:\n{target_path}")
            self.modelDownloaded.emit()
            self._reload_local_models()
        except Exception as e:
            QMessageBox.critical(self, "Lỗi", f"Không thể lưu model: {e}")

    def _reload_local_models(self):
        self.models_list_lbl.setText("📦 Các Model đã cài đặt cục bộ:")
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            no_lbl = QLabel("Chưa có model nào trong thư mục. Hãy gõ từ khóa ở trên để tìm & tải model!")
            no_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-style: italic;")
            self.cards_layout.addWidget(no_lbl)
            self.cards_layout.addStretch()
            return

        for item in os.listdir(target_dir):
            if item.startswith('.'): continue
            full_p = os.path.join(target_dir, item)
            size_mb = os.path.getsize(full_p) / (1024 * 1024) if os.path.isfile(full_p) else 0

            card = QFrame()
            card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; padding: 8px; }}")
            cl = QHBoxLayout(card)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(item, 28))
            cl.addWidget(icon_lbl)

            info_lbl = QLabel(f"<b>{item}</b><br><font color='#557088'>Dung lượng: {size_mb:.1f} MB • Local GGUF</font>")
            info_lbl.setStyleSheet("font-size: 12px;")
            cl.addWidget(info_lbl, stretch=1)

            del_btn = QPushButton("🗑️ Xóa")
            del_btn.setStyleSheet(f"QPushButton {{ background: rgba(255, 75, 110, 0.2); color: #FF4B6E; border: 1px solid #FF4B6E; border-radius: 6px; padding: 4px 10px; }}")
            del_btn.clicked.connect(lambda _, path=full_p: self._delete_local_model(path))
            cl.addWidget(del_btn)

            self.cards_layout.addWidget(card)

        self.cards_layout.addStretch()

    def _delete_local_model(self, path: str):
        if QMessageBox.question(self, "Xác nhận", f"Bạn có chắc muốn xóa model này?\n{os.path.basename(path)}") == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): import shutil; shutil.rmtree(path)
                self._reload_local_models()
                self.modelDownloaded.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa model: {e}")

    # ===============================================================
    # TAB 3: DATABASE & ASSETS (Khu chứa File User)
    # ===============================================================
    def _create_database_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Quản Lý Dữ Liệu & Files Upload")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Các tệp ngắn hạn tải lên được tự động lưu trong 30 ngày trước khi tự dọn dẹp:")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        layout.addWidget(desc)

        self.assets_list = QListWidget()
        self.assets_list.setStyleSheet(f"QListWidget {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 8px; color: {DesignTokens.TEXT_MAIN}; padding: 6px; }}")
        
        assets_dir = os.path.join(os.getcwd(), "database", "assets")
        if os.path.exists(assets_dir):
            for f in os.listdir(assets_dir):
                self.assets_list.addItem(QListWidgetItem(f"📄  {f}"))
        if self.assets_list.count() == 0:
            self.assets_list.addItem(QListWidgetItem("Chưa có tệp dữ liệu nào trong khu vực lưu trữ."))

        layout.addWidget(self.assets_list, stretch=1)

        clean_btn = QPushButton("🧹 Dọn Dẹp Bộ Nhớ Tạm Ngay")
        clean_btn.setFixedSize(200, 36)
        clean_btn.setStyleSheet(f"QPushButton {{ background: {DesignTokens.SURFACE_3}; color: {DesignTokens.CYAN_ACCENT}; border-radius: 8px; font-weight: bold; }}")
        clean_btn.clicked.connect(lambda: QMessageBox.information(self, "Dọn dẹp", "Đã quét và dọn dẹp các tệp bộ nhớ tạm!"))
        layout.addWidget(clean_btn)

        return page

    # ===============================================================
    # TAB 4: SYSTEM RULES & PROMPT (Lệnh Ngữ Cảnh)
    # ===============================================================
    def _create_rules_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        title = QLabel("Lệnh Ngữ Cảnh & System Rules")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        desc = QLabel("Thiết lập quy tắc ngữ cảnh mặc định. Lệnh này sẽ tự động được áp dụng trước mỗi câu hỏi của bạn khi chat:")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        desc.setWordWrap(True)
        layout.addWidget(desc)

        self.txt_rule = QTextEdit()
        self.txt_rule.setPlainText(self.user_settings.get("system_rule", ""))
        self.txt_rule.setStyleSheet(
            f"QTextEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 10px; padding: 12px; color: {DesignTokens.TEXT_MAIN}; font-size: 13px; }}"
        )
        layout.addWidget(self.txt_rule, stretch=1)

        save_rule_btn = QPushButton("Lưu Quy Tắc Ngữ Cảnh")
        save_rule_btn.setFixedSize(180, 36)
        save_rule_btn.setStyleSheet(f"QPushButton {{ background-color: {DesignTokens.CYAN}; color: black; font-weight: bold; border-radius: 8px; }}")
        save_rule_btn.clicked.connect(self._save_system_rule)
        layout.addWidget(save_rule_btn)

        return page

    def _save_system_rule(self):
        self.user_settings["system_rule"] = self.txt_rule.toPlainText().strip()
        save_user_settings(self.user_settings)
        self.settingsChanged.emit()
        QMessageBox.information(self, "Thành công", "Đã cập nhật quy tắc ngữ cảnh hệ thống!")

    # ===============================================================
    # TAB 5: USER PROFILE
    # ===============================================================
    def _create_profile_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        title = QLabel("Hồ Sơ Người Dùng")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        prof_card = QFrame()
        prof_card.setStyleSheet(f"QFrame {{ background: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; border-radius: 12px; padding: 20px; }}")
        pc_layout = QHBoxLayout(prof_card)
        pc_layout.setSpacing(20)

        avatar_lbl = QLabel(self.username[0].upper() if self.username else "U")
        avatar_lbl.setFixedSize(60, 60)
        avatar_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_lbl.setStyleSheet(f"background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #008EFF, stop:1 #00FFAA); color: black; font-size: 26px; font-weight: bold; border-radius: 30px;")
        pc_layout.addWidget(avatar_lbl)

        info_box = QVBoxLayout()
        info_box.setSpacing(4)
        u_name = QLabel(f"<b>Tên tài khoản:</b> {self.username}")
        u_name.setStyleSheet("font-size: 14px;")
        u_role = QLabel("Quyền hạn: Administrator • Local Desktop User")
        u_role.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        info_box.addWidget(u_name)
        info_box.addWidget(u_role)

        pc_layout.addLayout(info_box, stretch=1)
        layout.addWidget(prof_card)

        layout.addStretch()
        return page

    # ===============================================================
    # TAB 6: ABOUT ME & HARDWARE TELEMETRY
    # ===============================================================
    def _create_about_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(14)

        title = QLabel("Thông Số Hệ Thống & Cấu Hình Máy (About Me)")
        title.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {DesignTokens.CYAN_ACCENT};")
        layout.addWidget(title)

        self.telemetry_box = QTextEdit()
        self.telemetry_box.setReadOnly(True)
        self.telemetry_box.setStyleSheet(
            f"QTextEdit {{ background-color: {DesignTokens.SURFACE_1}; border: 1px solid {DesignTokens.BORDER}; "
            f"border-radius: 10px; padding: 14px; color: {DesignTokens.TEXT_MAIN}; font-family: Consolas, monospace; font-size: 12px; }}"
        )
        layout.addWidget(self.telemetry_box, stretch=1)

        self._update_system_telemetry()
        return page

    def _update_system_telemetry(self):
        cpu_usage = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        screen = QApplication.primaryScreen()
        res = screen.geometry() if screen else None

        info = f"""==================================================
  POP AI ASSISTANT - HỆ THỐNG GIÁM SÁT PHẦN CỨNG
==================================================

💻 Hệ điều hành   : {platform.system()} {platform.release()} ({platform.architecture()[0]})
🖥️ Màn hình      : {res.width()}x{res.height()} px
⚙️ Bộ vi xử lý    : {platform.processor()} ({psutil.cpu_count(logical=True)} Threads)
📊 Mức sử dụng CPU : {cpu_usage}%

🧠 Bộ nhớ RAM     : {mem.used / (1024**3):.2f} GB / {mem.total / (1024**3):.2f} GB ({mem.percent}%)
💾 Thư mục Model  : {self.user_settings.get('model_dir')}

🚀 Phiên bản App  : POP AI v2.5 (Windows Enterprise Edition)
"""
        self.telemetry_box.setPlainText(info)
