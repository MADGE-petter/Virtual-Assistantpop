import os
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame, QMessageBox, QFileDialog,
    QStackedWidget, QComboBox, QCheckBox
)
from PyQt6.QtGui import QDesktopServices
from PyQt6.QtCore import QUrl

from view.ui.styles import DesignTokens
from view.ui.icons import get_brand_logo_pixmap
from view.ui.settings.settings_config import save_user_settings
from service.cloud_llm_service import CLOUD_PROVIDERS, CloudLLMService


class CloudTestThread(QThread):
    """Background thread to test Cloud API credentials without blocking UI."""
    testFinished = pyqtSignal(bool, str)

    def __init__(self, provider: str, base_url: str, api_key: str, model: str):
        super().__init__()
        self.provider = provider
        self.base_url = base_url
        self.api_key = api_key
        self.model = model

    def run(self):
        try:
            svc = CloudLLMService(
                api_key=self.api_key,
                base_url=self.base_url,
                model=self.model,
                provider=self.provider,
                timeout=12
            )
            success, message = svc.test_connection()
            self.testFinished.emit(success, message)
        except Exception as e:
            self.testFinished.emit(False, str(e))


class ModelsTabWidget(QWidget):
    """Tab Quản lý Models: Hỗ trợ cả Models Cục Bộ (GGUF Offline) và Cloud Model API (Online)."""

    modelDownloaded = pyqtSignal()
    requestOpenDownloadTab = pyqtSignal()

    def __init__(self, user_settings: dict, parent=None):
        super().__init__(parent)
        self.user_settings = user_settings
        self._test_thread = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 24, 28, 24)
        layout.setSpacing(16)

        # ----------------------------------------------------
        # 1. TOP SEGMENTED SWITCHER (Local vs Cloud)
        # ----------------------------------------------------
        segmented_container = QWidget()
        segmented_layout = QHBoxLayout(segmented_container)
        segmented_layout.setContentsMargins(0, 0, 0, 0)
        segmented_layout.setSpacing(10)

        self.btn_tab_local = QPushButton("🖥️  Model Cục Bộ (GGUF Offline)")
        self.btn_tab_local.setFixedHeight(38)
        self.btn_tab_local.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_tab_cloud = QPushButton("☁️  Model Cloud (API Online)")
        self.btn_tab_cloud.setFixedHeight(38)
        self.btn_tab_cloud.setCursor(Qt.CursorShape.PointingHandCursor)

        self.btn_tab_local.clicked.connect(lambda: self._switch_subtab(0))
        self.btn_tab_cloud.clicked.connect(lambda: self._switch_subtab(1))

        segmented_layout.addWidget(self.btn_tab_local)
        segmented_layout.addWidget(self.btn_tab_cloud)
        segmented_layout.addStretch()

        layout.addWidget(segmented_container)

        # ----------------------------------------------------
        # 2. MAIN STACKED WIDGET
        # ----------------------------------------------------
        self.stack = QStackedWidget()
        self.stack.setStyleSheet("QStackedWidget { background: transparent; }")

        # Page 0: Local Models
        self.local_page = self._create_local_models_page()
        self.stack.addWidget(self.local_page)

        # Page 1: Cloud Models
        self.cloud_page = self._create_cloud_models_page()
        self.stack.addWidget(self.cloud_page)

        layout.addWidget(self.stack, stretch=1)

        # Initialize subtab style
        is_cloud_active = self.user_settings.get("use_cloud_api", False)
        self._switch_subtab(1 if is_cloud_active else 0)

    def _switch_subtab(self, index: int):
        self.stack.setCurrentIndex(index)
        active_style = (
            f"QPushButton {{ background: {DesignTokens.GRADIENT_BLUE_GREEN}; "
            f"color: #03050B; font-weight: 700; font-size: 13px; border: none; border-radius: 8px; padding: 0 20px; }}"
        )
        inactive_style = (
            f"QPushButton {{ background: rgba(255, 255, 255, 0.04); color: {DesignTokens.TEXT_MUTED}; "
            f"font-weight: 600; font-size: 13px; border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 8px; padding: 0 20px; }}"
            f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.08); color: {DesignTokens.TEXT_MAIN}; }}"
        )
        if index == 0:
            self.btn_tab_local.setStyleSheet(active_style)
            self.btn_tab_cloud.setStyleSheet(inactive_style)
            self.reload_local_models()
        else:
            self.btn_tab_local.setStyleSheet(inactive_style)
            self.btn_tab_cloud.setStyleSheet(active_style)

    # ============================================================
    # PAGE 0: LOCAL MODELS (GGUF OFFLINE)
    # ============================================================
    def _create_local_models_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(16)

        # Header Title Bar
        header_layout = QHBoxLayout()
        title_box = QVBoxLayout()
        title_box.setSpacing(4)

        title_row = QHBoxLayout()
        title = QLabel("Quản Lý Models Cục Bộ")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("GGUF ENGINE")
        badge.setStyleSheet(
            f"background: transparent; color: {DesignTokens.CYAN}; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT};"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel("Các mô hình AI định dạng GGUF chạy offline 100% trên phần cứng máy tính (GPU/RAM)")
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px;")
        desc.setWordWrap(True)

        title_box.addLayout(title_row)
        title_box.addWidget(desc)
        header_layout.addLayout(title_box, stretch=1)

        open_hub_btn = QPushButton("+  Tải Model Mới")
        open_hub_btn.setFixedHeight(34)
        open_hub_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        open_hub_btn.setStyleSheet(
            f"QPushButton {{ background: {DesignTokens.GRADIENT_BLUE_GREEN}; "
            f"color: #03050B; font-weight: 700; font-size: 12px; border: none; border-radius: 8px; padding: 0 16px; }}"
            f"QPushButton:hover {{ background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699); }}"
        )
        open_hub_btn.clicked.connect(lambda: self.requestOpenDownloadTab.emit())
        header_layout.addWidget(open_hub_btn)

        layout.addLayout(header_layout)

        # Storage Directory Glass Card
        dir_card = QFrame()
        dir_card.setObjectName("dirCard")
        dir_card.setStyleSheet(
            f"#dirCard {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 12px; }}"
            f"#dirCard:hover {{ background: rgba(255, 255, 255, 0.03); border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; }}"
            f"#dirCard QLabel {{ border: none; background: transparent; }}"
        )
        df_layout = QHBoxLayout(dir_card)
        df_layout.setContentsMargins(14, 10, 14, 10)
        df_layout.setSpacing(12)

        dir_title = QLabel("Thư mục lưu trữ:")
        dir_title.setStyleSheet(f"font-size: 12px; font-weight: 600; color: {DesignTokens.TEXT_SECONDARY};")

        self.txt_model_dir = QLineEdit(self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents")))
        self.txt_model_dir.setReadOnly(True)
        self.txt_model_dir.setStyleSheet(
            f"QLineEdit {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 6px; padding: 6px 12px; font-size: 12px; color: {DesignTokens.TEXT_MAIN}; }}"
        )

        change_dir_btn = QPushButton("Đổi thư mục...")
        change_dir_btn.setFixedHeight(30)
        change_dir_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        change_dir_btn.setStyleSheet(
            f"QPushButton {{ background: transparent; color: {DesignTokens.TEXT_MAIN}; "
            f"border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 6px; padding: 0 14px; font-size: 12px; font-weight: 500; }}"
            f"QPushButton:hover {{ background: rgba(255, 255, 255, 0.04); border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; color: {DesignTokens.CYAN_ACCENT}; }}"
        )
        change_dir_btn.clicked.connect(self._change_model_directory)

        df_layout.addWidget(dir_title)
        df_layout.addWidget(self.txt_model_dir, stretch=1)
        df_layout.addWidget(change_dir_btn)
        layout.addWidget(dir_card)

        # Section Label
        self.models_list_lbl = QLabel("Danh sách mô hình đã cài đặt:")
        self.models_list_lbl.setStyleSheet(f"font-size: 13px; font-weight: 600; color: {DesignTokens.TEXT_MUTED}; margin-top: 4px;")
        layout.addWidget(self.models_list_lbl)

        # Scroll Area for Model Cards
        self.scroll_models = QScrollArea()
        self.scroll_models.setWidgetResizable(True)
        self.scroll_models.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_models.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_models.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.cards_container = QWidget()
        self.cards_container.setStyleSheet("background: transparent;")
        self.cards_layout = QVBoxLayout(self.cards_container)
        self.cards_layout.setContentsMargins(2, 4, 14, 12)
        self.cards_layout.setSpacing(10)

        self.scroll_models.setWidget(self.cards_container)
        layout.addWidget(self.scroll_models, stretch=1)

        return page

    # ============================================================
    # PAGE 1: CLOUD MODEL API (ONLINE)
    # ============================================================
    def _create_cloud_models_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(16)

        # Header Title Bar
        header_box = QVBoxLayout()
        header_box.setSpacing(4)

        title_row = QHBoxLayout()
        title = QLabel("Cấu Hình Cloud Model API")
        title.setStyleSheet(f"font-size: 18px; font-weight: 700; color: {DesignTokens.TEXT_MAIN}; letter-spacing: 0.5px;")

        badge = QLabel("OPENAI COMPATIBLE")
        badge.setStyleSheet(
            f"background: transparent; color: #00FFAA; font-size: 11px; "
            f"font-weight: 700; border-radius: 4px; padding: 2px 8px; border: 1px solid rgba(0, 255, 170, 0.4);"
        )
        title_row.addWidget(title)
        title_row.addWidget(badge)
        title_row.addStretch()

        desc = QLabel(
            "Kết nối trực tiếp tới các mô hình AI đám mây mạnh mẽ nhất thế giới (DeepSeek, OpenAI GPT-4o, Groq, Google Gemini, OpenRouter) "
            "để trò chuyện và lập trình với tốc độ cao mà không tốn tài nguyên máy tính."
        )
        desc.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 12px; line-height: 1.5;")
        desc.setWordWrap(True)

        header_box.addLayout(title_row)
        header_box.addWidget(desc)
        layout.addLayout(header_box)

        # Master Toggle Card
        toggle_card = QFrame()
        toggle_card.setStyleSheet(
            f"QFrame {{ background: rgba(0, 255, 170, 0.04); border: 1px solid rgba(0, 255, 170, 0.2); border-radius: 12px; padding: 12px 16px; }}"
        )
        tc_layout = QHBoxLayout(toggle_card)
        tc_layout.setContentsMargins(12, 10, 12, 10)

        self.chk_use_cloud = QCheckBox("Ưu tiên sử dụng Cloud Model API cho Trợ Lý & Code Studio")
        self.chk_use_cloud.setChecked(self.user_settings.get("use_cloud_api", False))
        self.chk_use_cloud.setCursor(Qt.CursorShape.PointingHandCursor)
        self.chk_use_cloud.setStyleSheet(
            f"QCheckBox {{ color: #00FFAA; font-size: 13px; font-weight: 700; spacing: 10px; }}"
            f"QCheckBox::indicator {{ width: 18px; height: 18px; border-radius: 4px; border: 1px solid #00FFAA; background: transparent; }}"
            f"QCheckBox::indicator:checked {{ background: #00FFAA; image: none; }}"
        )

        tc_layout.addWidget(self.chk_use_cloud, stretch=1)
        layout.addWidget(toggle_card)

        # Credentials Form Card
        form_card = QFrame()
        form_card.setStyleSheet(
            f"QFrame {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; border-radius: 12px; }}"
        )
        form_layout = QVBoxLayout(form_card)
        form_layout.setContentsMargins(20, 18, 20, 18)
        form_layout.setSpacing(14)

        # 1. Provider Selector
        prov_row = QHBoxLayout()
        prov_lbl = QLabel("Nhà cung cấp (Provider):")
        prov_lbl.setFixedWidth(160)
        prov_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 600;")

        self.cb_provider = QComboBox()
        self.cb_provider.setStyleSheet(
            f"QComboBox {{ background: #0D111A; color: {DesignTokens.TEXT_MAIN}; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 6px; padding: 6px 12px; font-size: 13px; min-height: 28px; }}"
            f"QComboBox::drop-down {{ border: none; }}"
            f"QComboBox QAbstractItemView {{ background: #0D111A; color: #FFFFFF; selection-background-color: #141C2A; }}"
        )
        for key, info in CLOUD_PROVIDERS.items():
            self.cb_provider.addItem(f"  {info['name']}", key)

        # Select saved provider
        saved_provider = self.user_settings.get("cloud_provider", "deepseek")
        idx = self.cb_provider.findData(saved_provider)
        if idx >= 0:
            self.cb_provider.setCurrentIndex(idx)

        self.cb_provider.currentIndexChanged.connect(self._on_provider_changed)

        prov_row.addWidget(prov_lbl)
        prov_row.addWidget(self.cb_provider, stretch=1)
        form_layout.addLayout(prov_row)

        # Provider Description & Link
        self.lbl_provider_desc = QLabel("")
        self.lbl_provider_desc.setStyleSheet("color: #94A3B8; font-size: 11px; margin-left: 160px;")
        self.lbl_provider_desc.setOpenExternalLinks(True)
        form_layout.addWidget(self.lbl_provider_desc)

        # 2. Base URL
        url_row = QHBoxLayout()
        url_lbl = QLabel("Base URL Endpoint:")
        url_lbl.setFixedWidth(160)
        url_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 600;")

        self.txt_base_url = QLineEdit(self.user_settings.get("cloud_base_url", "https://api.deepseek.com/v1"))
        self.txt_base_url.setStyleSheet(
            f"QLineEdit {{ background: #0D111A; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 6px; padding: 6px 12px; font-size: 12px; color: {DesignTokens.TEXT_MAIN}; }}"
        )
        url_row.addWidget(url_lbl)
        url_row.addWidget(self.txt_base_url, stretch=1)
        form_layout.addLayout(url_row)

        # 3. API Key
        key_row = QHBoxLayout()
        key_lbl = QLabel("API Key:")
        key_lbl.setFixedWidth(160)
        key_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 600;")

        self.txt_api_key = QLineEdit(self.user_settings.get("cloud_api_key", ""))
        self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        self.txt_api_key.setPlaceholderText("sk-...")
        self.txt_api_key.setStyleSheet(
            f"QLineEdit {{ background: #0D111A; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 6px; padding: 6px 12px; font-size: 12px; color: {DesignTokens.TEXT_MAIN}; }}"
        )

        self.btn_toggle_key = QPushButton("👁️")
        self.btn_toggle_key.setFixedSize(34, 34)
        self.btn_toggle_key.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_key.setToolTip("Hiện/Ẩn API Key")
        self.btn_toggle_key.setStyleSheet(
            "QPushButton { background: rgba(255, 255, 255, 0.05); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 6px; }"
        )
        self.btn_toggle_key.clicked.connect(self._toggle_api_key_visibility)

        key_row.addWidget(key_lbl)
        key_row.addWidget(self.txt_api_key, stretch=1)
        key_row.addWidget(self.btn_toggle_key)
        form_layout.addLayout(key_row)

        # 4. Model Selection (Editable ComboBox)
        model_row = QHBoxLayout()
        model_lbl = QLabel("Tên Model:")
        model_lbl.setFixedWidth(160)
        model_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MAIN}; font-size: 13px; font-weight: 600;")

        self.cb_model = QComboBox()
        self.cb_model.setEditable(True)
        self.cb_model.setStyleSheet(
            f"QComboBox {{ background: #0D111A; color: {DesignTokens.TEXT_MAIN}; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
            f"border-radius: 6px; padding: 6px 12px; font-size: 12px; min-height: 28px; }}"
            f"QComboBox QAbstractItemView {{ background: #0D111A; color: #FFFFFF; selection-background-color: #141C2A; }}"
        )
        model_row.addWidget(model_lbl)
        model_row.addWidget(self.cb_model, stretch=1)
        form_layout.addLayout(model_row)

        layout.addWidget(form_card)

        # ----------------------------------------------------
        # Action Bar: Test Connection & Save
        # ----------------------------------------------------
        action_layout = QHBoxLayout()
        action_layout.setSpacing(12)

        self.btn_test_conn = QPushButton("⚡  Kiểm Tra Kết Nối")
        self.btn_test_conn.setFixedHeight(36)
        self.btn_test_conn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_test_conn.setStyleSheet("""
            QPushButton {
                background: rgba(0, 204, 255, 0.1);
                color: #00CCFF;
                font-weight: 700;
                font-size: 12px;
                border: 1px solid rgba(0, 204, 255, 0.35);
                border-radius: 8px;
                padding: 0 18px;
            }
            QPushButton:hover {
                background: rgba(0, 204, 255, 0.2);
                color: #FFFFFF;
                border-color: #00CCFF;
            }
        """)
        self.btn_test_conn.clicked.connect(self._test_cloud_connection)

        self.btn_save_cloud = QPushButton("💾  Lưu Cấu Hình")
        self.btn_save_cloud.setFixedHeight(36)
        self.btn_save_cloud.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_save_cloud.setStyleSheet(f"""
            QPushButton {{
                background: {DesignTokens.GRADIENT_BLUE_GREEN};
                color: #03050B;
                font-weight: 700;
                font-size: 12px;
                border: none;
                border-radius: 8px;
                padding: 0 24px;
            }}
            QPushButton:hover {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0077D6, stop:1 #00E699);
            }}
        """)
        self.btn_save_cloud.clicked.connect(self._save_cloud_settings)

        action_layout.addWidget(self.btn_test_conn)
        action_layout.addWidget(self.btn_save_cloud)
        action_layout.addStretch()

        layout.addLayout(action_layout)

        # Status / Result Label
        self.lbl_test_result = QLabel("")
        self.lbl_test_result.setWordWrap(True)
        self.lbl_test_result.setStyleSheet("font-size: 12px; padding: 6px 12px; border-radius: 6px;")
        self.lbl_test_result.setVisible(False)
        layout.addWidget(self.lbl_test_result)

        layout.addStretch()

        # Update initial provider information
        self._on_provider_changed(self.cb_provider.currentIndex())

        return page

    # ============================================================
    # PROVIDER LOGIC & ACTIONS
    # ============================================================
    def _on_provider_changed(self, index: int):
        prov_key = self.cb_provider.itemData(index)
        info = CLOUD_PROVIDERS.get(prov_key, {})
        if not info:
            return

        # Update description
        url_link = info.get("api_key_url", "")
        desc_text = info.get("description", "")
        if url_link:
            desc_text += f" &nbsp;•&nbsp; <a style='color: #00FFAA; text-decoration: underline;' href='{url_link}'>Lấy API Key tại đây ↗</a>"
        self.lbl_provider_desc.setText(desc_text)

        # Update base url if empty or previous was a default
        self.txt_base_url.setText(info.get("base_url", ""))

        # Populate model dropdown
        saved_model = self.user_settings.get("cloud_model", "")
        self.cb_model.clear()
        for m in info.get("models", []):
            self.cb_model.addItem(m)

        if saved_model:
            self.cb_model.setEditText(saved_model)
        else:
            self.cb_model.setEditText(info.get("default_model", ""))

    def _toggle_api_key_visibility(self):
        if self.txt_api_key.echoMode() == QLineEdit.EchoMode.Password:
            self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Normal)
            self.btn_toggle_key.setText("🙈")
        else:
            self.txt_api_key.setEchoMode(QLineEdit.EchoMode.Password)
            self.btn_toggle_key.setText("👁️")

    def _test_cloud_connection(self):
        prov_key = self.cb_provider.currentData()
        base_url = self.txt_base_url.text().strip()
        api_key = self.txt_api_key.text().strip()
        model = self.cb_model.currentText().strip()

        self.btn_test_conn.setEnabled(False)
        self.lbl_test_result.setVisible(True)
        self.lbl_test_result.setStyleSheet("color: #00CCFF; background: rgba(0, 204, 255, 0.08);")
        self.lbl_test_result.setText("⏳ Đang gửi yêu cầu kiểm tra kết nối đến API...")

        self._test_thread = CloudTestThread(prov_key, base_url, api_key, model)
        self._test_thread.testFinished.connect(self._on_test_finished)
        self._test_thread.start()

    def _on_test_finished(self, success: bool, message: str):
        self.btn_test_conn.setEnabled(True)
        if success:
            self.lbl_test_result.setStyleSheet(
                "color: #00FFAA; background: rgba(0, 255, 170, 0.1); border: 1px solid rgba(0, 255, 170, 0.3);"
            )
            self.lbl_test_result.setText(f"✓ {message}")
        else:
            self.lbl_test_result.setStyleSheet(
                "color: #FF5555; background: rgba(255, 85, 85, 0.1); border: 1px solid rgba(255, 85, 85, 0.3);"
            )
            self.lbl_test_result.setText(f"✕ {message}")

    def _save_cloud_settings(self):
        prov_key = self.cb_provider.currentData()
        self.user_settings["use_cloud_api"] = self.chk_use_cloud.isChecked()
        self.user_settings["cloud_provider"] = prov_key
        self.user_settings["cloud_base_url"] = self.txt_base_url.text().strip()
        self.user_settings["cloud_api_key"] = self.txt_api_key.text().strip()
        self.user_settings["cloud_model"] = self.cb_model.currentText().strip()

        save_user_settings(self.user_settings)

        # Notify LLMService to reload
        try:
            from service.llm_service import LLMService
            LLMService().reload_config()
        except Exception:
            pass

        QMessageBox.information(
            self,
            "Đã Lưu Cấu Hình",
            f"Đã lưu thành công cấu hình Cloud Model API ({self.cb_provider.currentText().strip()})!\n"
            f"Trạng thái: {'Đang BẬT' if self.chk_use_cloud.isChecked() else 'Đang TẮT (Dùng Local Model)'}."
        )

    # ============================================================
    # LOCAL MODEL DISK MANAGEMENT
    # ============================================================
    def _change_model_directory(self):
        new_dir = QFileDialog.getExistingDirectory(self, "Chọn thư mục lưu trữ Models", self.txt_model_dir.text())
        if new_dir:
            self.txt_model_dir.setText(new_dir)
            self.user_settings["model_dir"] = new_dir
            save_user_settings(self.user_settings)
            self.reload_local_models()

    def reload_local_models(self):
        while self.cards_layout.count():
            item = self.cards_layout.takeAt(0)
            if item is not None:
                w = item.widget()
                if w is not None:
                    w.deleteLater()

        target_dir = self.user_settings.get("model_dir", os.path.join(os.getcwd(), "LLM-agents"))
        if not os.path.exists(target_dir) or not os.listdir(target_dir):
            empty_card = QFrame()
            empty_card.setStyleSheet(
                "QFrame { background: transparent; border: 1px dashed rgba(255, 255, 255, 0.15); "
                "border-radius: 12px; padding: 36px; }"
            )
            ec_layout = QVBoxLayout(empty_card)
            ec_layout.setSpacing(10)
            
            from view.ui.icons import create_vector_icon
            ec_icon = QLabel()
            ec_icon.setPixmap(create_vector_icon("box", "#557088", 36).pixmap(36, 36))
            ec_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)

            ec_lbl = QLabel("Chưa có mô hình AI nào trong thư mục máy tính.\nNhấp vào nút '+ Tải Model Mới' ở trên để khám phá & tải mô hình về.")
            ec_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            ec_lbl.setStyleSheet(f"color: {DesignTokens.TEXT_MUTED}; font-size: 13px; line-height: 1.6;")
            
            ec_layout.addWidget(ec_icon)
            ec_layout.addWidget(ec_lbl)
            self.cards_layout.addWidget(empty_card)
            self.models_list_lbl.setText("Danh sách mô hình đã cài đặt (0):")
            self.cards_layout.addStretch()
            return

        count = 0
        total_size_mb = 0.0
        for item in sorted(os.listdir(target_dir)):
            if item.startswith('.'): continue
            full_p = os.path.join(target_dir, item)
            size_mb = (os.path.getsize(full_p) / (1024 * 1024)) if os.path.isfile(full_p) else 0.0
            total_size_mb += size_mb

            card = QFrame()
            card.setObjectName(f"modelCard_{count}")
            card.setStyleSheet(
                f"#modelCard_{count} {{ background: transparent; border: 1px solid; border-color: {DesignTokens.BORDER_GRADIENT}; "
                f"border-radius: 12px; padding: 12px 16px; }}"
                f"#modelCard_{count}:hover {{ border-color: {DesignTokens.BORDER_GRADIENT_HOVER}; background: rgba(255, 255, 255, 0.03); }}"
                f"#modelCard_{count} QLabel {{ border: none; background: transparent; }}"
            )
            cl = QHBoxLayout(card)
            cl.setContentsMargins(8, 4, 8, 4)
            cl.setSpacing(16)

            icon_lbl = QLabel()
            icon_lbl.setPixmap(get_brand_logo_pixmap(item, 38))
            cl.addWidget(icon_lbl)

            info_box = QVBoxLayout()
            info_box.setSpacing(4)
            
            name_lbl = QLabel(item)
            name_lbl.setStyleSheet(f"font-size: 14px; font-weight: 600; color: {DesignTokens.TEXT_MAIN};")

            size_str = f"{size_mb / 1024:.2f} GB" if size_mb >= 1024 else f"{size_mb:.1f} MB"
            sub_lbl = QLabel(
                f"<span style='color: #00FFAA; font-weight: 600;'>● Sẵn sàng</span> &nbsp;•&nbsp; "
                f"<span style='color: #96D7E9;'>Dung lượng: {size_str}</span> &nbsp;•&nbsp; "
                f"<span style='color: #557088;'>Định dạng GGUF</span>"
            )
            sub_lbl.setStyleSheet("font-size: 12px;")

            info_box.addWidget(name_lbl)
            info_box.addWidget(sub_lbl)
            cl.addLayout(info_box, stretch=1)

            del_btn = QPushButton("Xóa")
            del_btn.setFixedHeight(30)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(
                f"QPushButton {{ background: rgba(255, 75, 110, 0.12); color: {DesignTokens.CORAL_ACCENT}; "
                f"border: 1px solid rgba(255, 75, 110, 0.3); border-radius: 6px; padding: 0 16px; font-size: 12px; font-weight: 600; }}"
                f"QPushButton:hover {{ background: rgba(255, 75, 110, 0.25); color: #FFFFFF; border-color: {DesignTokens.CORAL_ACCENT}; }}"
            )
            del_btn.clicked.connect(lambda _, path=full_p: self._delete_local_model(path))
            cl.addWidget(del_btn)

            self.cards_layout.addWidget(card)
            count += 1

        total_str = f"{total_size_mb / 1024:.2f} GB" if total_size_mb >= 1024 else f"{total_size_mb:.1f} MB"
        self.models_list_lbl.setText(f"Danh sách mô hình đã cài đặt ({count} models • Tổng dung lượng: {total_str}):")
        self.cards_layout.addStretch()

    def _delete_local_model(self, path: str):
        confirm = QMessageBox(self)
        confirm.setWindowTitle("Xác nhận xóa")
        confirm.setText(f"Bạn có chắc muốn xóa mô hình này khỏi đĩa cứng?\n\n{os.path.basename(path)}")
        confirm.setIcon(QMessageBox.Icon.Question)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)
        if confirm.exec() == QMessageBox.StandardButton.Yes:
            try:
                if os.path.isfile(path): os.remove(path)
                elif os.path.isdir(path): import shutil; shutil.rmtree(path)
                self.reload_local_models()
                self.modelDownloaded.emit()
            except Exception as e:
                QMessageBox.critical(self, "Lỗi", f"Không thể xóa model: {e}")
